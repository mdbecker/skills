#!/usr/bin/env python3
"""Install verified skill folders from an explicitly selected release archive."""

import argparse
import hashlib
import io
import json
import math
import os
from pathlib import Path, PurePosixPath
import posixpath
import re
import shutil
import stat
import sys
import tempfile
import unicodedata
from html import unescape
from urllib.parse import unquote, urlsplit
import zipfile


HOST_DIRS = {"codex": ".agents/skills", "claude": ".claude/skills"}
PACKAGE = "mdbecker-skills"
MAX_FILES = 2000
MAX_BYTES = 32 * 1024 * 1024
RECEIPT = ".mdbecker-skills.json"
METADATA_TYPED_SCALARS = (
    r"(?:yes|Yes|YES|no|No|NO|true|True|TRUE|false|False|FALSE|on|On|ON|off|Off|OFF)",
    r"(?:~|null|Null|NULL)",
    r"[-+]?(?:0b[0-1_]+|0[0-7_]+|0|[1-9][0-9_]*|0x[0-9a-fA-F_]+|[1-9][0-9_]*(?::[0-5]?[0-9])+)",
    r"(?:[-+]?[0-9][0-9_]*\.[0-9_]*(?:[eE][-+][0-9]+)?|\.[0-9][0-9_]*(?:[eE][-+][0-9]+)?|[-+]?[0-9][0-9_]*(?::[0-5]?[0-9])+\.[0-9_]*|[-+]?\.(?:inf|Inf|INF)|\.(?:nan|NaN|NAN))",
    r"(?:[0-9]{4}-[0-9]{2}-[0-9]{2}|[0-9]{4}-[0-9]{1,2}-[0-9]{1,2}(?:[Tt]|[ \t]+)[0-9]{1,2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]*)?(?:[ \t]*(?:Z|[-+][0-9]{1,2}(?::[0-9]{2})?))?)",
)


def digest(content):
    return hashlib.sha256(content).hexdigest()


def safe_relative(value):
    if not isinstance(value, str) or not value or "\\" in value or ":" in value or any(ord(character) < 32 or ord(character) == 127 for character in value):
        raise ValueError(f"Invalid relative path: {value!r}")
    relative = PurePosixPath(value)
    if relative.is_absolute() or any(part in {".", "..", ""} for part in value.split("/")):
        raise ValueError(f"Unsafe archive path: {value!r}")
    return relative


def parse_json(content):
    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"Duplicate JSON key: {key}")
            result[key] = value
        return result
    def invalid_constant(value):
        raise ValueError("Non-JSON numeric constant")

    def finite_float(value):
        number = float(value)
        if not math.isfinite(number):
            raise ValueError("Nonfinite JSON number")
        return number

    return json.loads(content, object_pairs_hook=unique_object,
                      parse_constant=invalid_constant, parse_float=finite_float)


def _metadata_scalar(value):
    value = value.strip()
    if value.startswith("'"):
        match = re.fullmatch(r"'((?:[^']|'')*)'(?:\s+#.*)?\s*", value)
        if not match:
            raise ValueError("Unsupported single-quoted metadata")
        return match.group(1).replace("''", "'")
    if value.startswith('"'):
        try:
            parsed, end = json.JSONDecoder().raw_decode(value)
        except ValueError as error:
            raise ValueError("Unsupported double-quoted metadata") from error
        tail = value[end:]
        if not isinstance(parsed, str) or tail and not re.fullmatch(r"\s+(?:#.*)?", tail):
            raise ValueError("Unsupported quoted metadata suffix")
        return parsed
    value = re.split(r"\s+#", value, maxsplit=1)[0].rstrip()
    if (not value or value.startswith(tuple("[{*&!|>@`#")) or value.startswith(("- ", "? ", ": "))
            or re.search(r":(?:\s|$)", value)):
        raise ValueError("Metadata needs a supported string scalar")
    if any(re.fullmatch(pattern, value) for pattern in METADATA_TYPED_SCALARS):
        raise ValueError("Metadata values must be strings, not typed scalars")
    return value


def _metadata_block(lines, index, indicator):
    content = []
    indentation = None
    while index < len(lines):
        line = lines[index]
        if line.strip() and not line.startswith((' ', '\t')):
            break
        if '\t' in line[:len(line) - len(line.lstrip())]:
            raise ValueError("Metadata blocks require space indentation")
        if line.strip():
            width = len(line) - len(line.lstrip(' '))
            if indentation is None:
                indentation = width
            if width != indentation:
                raise ValueError("Metadata block indentation must be uniform")
            content.append(line[width:])
        else:
            content.append('')
        index += 1
    if indicator.startswith('|'):
        result = '\n'.join(content)
    else:
        pieces = []
        position = 0
        while position < len(content):
            if not content[position]:
                pieces.append('\n')
                position += 1
            else:
                paragraph = []
                while position < len(content) and content[position]:
                    paragraph.append(content[position])
                    position += 1
                pieces.append(' '.join(paragraph))
        result = ''.join(pieces)
    result = result.rstrip('\n')
    if result and not indicator.endswith('-'):
        result += '\n'
    return result, index


def valid_skill_name(name):
    return (isinstance(name, str) and re.fullmatch(r'[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?', name) is not None
            and '--' not in name)


def parse_skill_metadata(document, expected_name):
    try:
        text = document.decode('utf-8') if isinstance(document, bytes) else document
        if not isinstance(text, str):
            raise ValueError("Expected UTF-8 skill document")
        text = text.replace('\r\n', '\n')
        if '\r' in text:
            raise ValueError("Unsupported line endings")
        match = re.match(r"\A---\n(.*?)\n---(?:\n|$)", text, re.S)
        if not match:
            raise ValueError("Missing YAML frontmatter")
        lines = match.group(1).split('\n')
        values = {}
        index = 0
        while index < len(lines):
            line = lines[index]
            index += 1
            field = re.fullmatch(r"(name|description):(?:[ \t]+(.*))?", line)
            if not field:
                continue
            key, scalar = field.groups()
            if key in values:
                raise ValueError("Duplicate required metadata field")
            scalar = scalar or ''
            block = re.fullmatch(r"([|>]-?)(?:\s+#.*)?\s*", scalar)
            if block:
                values[key], index = _metadata_block(lines, index, block.group(1))
            else:
                values[key] = _metadata_scalar(scalar)
        if (set(values) != {'name', 'description'} or values['name'] != expected_name
                or not valid_skill_name(expected_name) or not values['description'].strip()
                or len(values['description']) > 1024):
            raise ValueError("Required metadata identity or description is invalid")
        return values
    except (ValueError, UnicodeError) as error:
        raise ValueError(f"Invalid skill name/description metadata: {expected_name}: {error}") from error


def resolve_link_target(source, target):
    if re.search(r'%(?![0-9a-fA-F]{2})', target):
        raise ValueError('Malformed URL escape')
    parsed = urlsplit(target)
    if parsed.scheme in {'http', 'https', 'mailto'} or parsed.netloc and not parsed.scheme:
        return None, ''
    if parsed.scheme or parsed.path.startswith(('/', '\\')):
        raise ValueError('Disallowed absolute path or URI scheme')
    path = unquote(parsed.path, errors='strict')
    fragment = unquote(parsed.fragment, errors='strict')
    if '\\' in path or any(ord(character) < 32 or ord(character) == 127 for character in path + fragment):
        raise ValueError('Invalid path characters')
    resolved = posixpath.normpath(posixpath.join(posixpath.dirname(source), path)) if path else source
    if resolved == '..' or resolved.startswith('../') or resolved.startswith('/'):
        raise ValueError('Target escapes its permitted root')
    return resolved, fragment



def inline_destinations(text):
    masked = list(text)

    def hide(start, end):
        for position in range(start, end):
            if masked[position] not in '\r\n':
                masked[position] = ' '

    front = re.match(r'\A---\r?\n.*?\r?\n---(?:\r?\n|$)', text, re.S)
    if front:
        hide(0, front.end())
    for match in re.finditer(r'<!--.*?-->', text, re.S):
        hide(match.start(), match.end())
    fence = None
    position = 0
    for line in text.splitlines(keepends=True):
        match = re.match(r'^ {0,3}(`{3,}|~{3,})', line)
        if match:
            if fence is None:
                fence = (match.group(1)[0], len(match.group(1)))
            elif match.group(1)[0] == fence[0] and len(match.group(1)) >= fence[1]:
                fence = None
            hide(position, position + len(line))
        elif fence or line.startswith(('    ', '\t')):
            hide(position, position + len(line))
        position += len(line)
    clean = ''.join(masked)
    position = 0
    while position < len(clean):
        if clean[position] == '`':
            end = position
            while end < len(clean) and clean[end] == '`':
                end += 1
            close = clean.find(clean[position:end], end)
            if close >= 0:
                hide(position, close + end - position)
                position = close + end - position
                continue
        position += 1
    clean = ''.join(masked)
    position = 0
    while position < len(clean):
        if clean[position] == '\\':
            position += 2
            continue
        if clean[position] != '[':
            position += 1
            continue
        depth = 1
        end = position + 1
        while end < len(clean) and depth:
            if clean[end] == '\\':
                end += 2
                continue
            if clean[end] == '[':
                depth += 1
            elif clean[end] == ']':
                depth -= 1
            end += 1
        if depth or end >= len(clean) or clean[end] != '(':
            position += 1
            continue
        end += 1
        while end < len(clean) and clean[end].isspace():
            end += 1
        start = end
        angle = clean[end:end + 1] == '<'
        if angle:
            start += 1
            end = start
            while end < len(clean) and clean[end] != '>':
                if clean[end] == '\\':
                    end += 1
                end += 1
            if end >= len(clean):
                position += 1
                continue
            destination_end = end
            end += 1
        else:
            depth = 0
            while end < len(clean):
                character = clean[end]
                if character == '\\':
                    end += 2
                    continue
                if character == '(':
                    depth += 1
                elif character == ')':
                    if not depth:
                        break
                    depth -= 1
                elif character.isspace() and not depth:
                    break
                end += 1
            destination_end = end
        separated = end < len(clean) and clean[end].isspace()
        while end < len(clean) and clean[end].isspace():
            end += 1
        if separated and clean[end:end + 1] in {'\"', "'", '('}:
            delimiter = ')' if clean[end] == '(' else clean[end]
            end += 1
            while end < len(clean) and clean[end] != delimiter:
                if clean[end] == '\\':
                    end += 1
                end += 1
            end += 1
            while end < len(clean) and clean[end].isspace():
                end += 1
        if end < len(clean) and clean[end] == ')':
            raw = text[start:destination_end]
            yield unescape(re.sub(r'\\([!"#$%&\x27()*+,\-./:;<=>?@\[\]\\^_`{|}~])', r'\1', raw))
            position = end + 1
        else:
            position += 1


def read_archive(archive, expected_sha256=None):
    with Path(archive).open("rb") as stream:
        archive_content = stream.read(MAX_BYTES * 2 + 1)
    if len(archive_content) > MAX_BYTES * 2:
        raise ValueError("Compressed archive exceeds the size limit")
    if expected_sha256 and digest(archive_content) != expected_sha256.lower():
        raise ValueError("Archive SHA-256 does not match the supplied release checksum")
    with zipfile.ZipFile(io.BytesIO(archive_content)) as bundle:
        entries = bundle.infolist()
        if len(entries) > MAX_FILES or sum(entry.file_size for entry in entries) > MAX_BYTES:
            raise ValueError("Archive exceeds the file-count or uncompressed-size limit")
        paths = set()
        contents = {}
        for entry in entries:
            safe_relative(entry.filename)
            folded = unicodedata.normalize("NFC", entry.filename).casefold()
            if folded in paths:
                raise ValueError(f"Duplicate or case-colliding archive path: {entry.filename}")
            paths.add(folded)
            mode = entry.external_attr >> 16
            if entry.flag_bits & 1 or entry.is_dir() or stat.S_ISLNK(mode) or stat.S_IFMT(mode) not in {0, stat.S_IFREG}:
                raise ValueError(f"Archive must contain regular files only: {entry.filename}")
            contents[entry.filename] = bundle.read(entry)
    for path in contents:
        parts = safe_relative(path).parts
        if any("/".join(parts[:length]) in contents for length in range(1, len(parts))):
            raise ValueError(f"Archive file is also a parent directory: {path}")
    manifest = parse_json(contents.get("manifest.json", b"null"))
    if not isinstance(manifest, dict) or type(manifest.get("schema_version")) is not int or manifest.get("schema_version") != 1 or manifest.get("package") != PACKAGE:
        raise ValueError("Unsupported skill archive manifest")
    if not isinstance(manifest.get("version"), str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}", manifest["version"]):
        raise ValueError("Missing or invalid package version")
    if not isinstance(manifest.get("commit"), str) or not re.fullmatch(r"[0-9a-f]{40}", manifest["commit"]):
        raise ValueError("Missing source commit identity")
    if manifest.get("host_profiles") != HOST_DIRS or not isinstance(manifest.get("qualification"), dict):
        raise ValueError("Missing host mapping or qualification record")
    files = manifest.get("files")
    skills = manifest.get("skills")
    if not isinstance(files, dict) or not isinstance(skills, list) or not skills:
        raise ValueError("Manifest needs complete file hashes and a skill inventory")
    if set(files) != set(contents) - {"manifest.json"}:
        raise ValueError("Archive contents do not match the complete manifest inventory")
    for name, checksum in files.items():
        safe_relative(name)
        if not isinstance(checksum, str) or digest(contents[name]) != checksum:
            raise ValueError(f"File checksum mismatch: {name}")
    names = set()
    for skill in skills:
        name = skill.get("name") if isinstance(skill, dict) else None
        if not valid_skill_name(name):
            raise ValueError("Invalid skill name")
        if name.casefold() in names or skill.get("path") != f"skills/{name}":
            raise ValueError("Duplicate skill name or unexpected skill path")
        names.add(name.casefold())
        if f"skills/{name}/SKILL.md" not in contents:
            raise ValueError(f"Missing skill entrypoint: {name}")
        parse_skill_metadata(contents[f"skills/{name}/SKILL.md"], name)
        required = skill.get("required_files")
        actual = {path[len(f"skills/{name}/"):] for path in contents if path.startswith(f"skills/{name}/")}
        if not isinstance(required, list) or not required or len(set(required)) != len(required) or set(required) != actual:
            raise ValueError(f"Incomplete resource closure: {name}")
        for relative in required:
            safe_relative(relative)
            path = f"skills/{name}/{relative}"
            if PurePosixPath(relative).suffix.lower() in {'.md', '.markdown'}:
                for target in inline_destinations(contents[path].decode('utf-8')):
                    resolved, unused_fragment = resolve_link_target(path, target)
                    if resolved is None:
                        continue
                    if not resolved.startswith(f"skills/{name}/") or resolved not in contents:
                        raise ValueError(f"Missing or escaping bundled reference: {path}: {target}")
    roots = {"README.md", "install.py", "LICENSE", "NOTICE"}
    for name in files:
        parts = safe_relative(name).parts
        if name not in roots and not (len(parts) >= 3 and parts[0] == "skills" and parts[1] in names):
            raise ValueError(f"Undeclared payload path: {name}")
    if not roots.issubset(contents):
        raise ValueError("Missing bootstrap instructions, installer or attribution")
    return manifest, contents


def check_components(project, destination):
    current = project
    for component in destination.relative_to(project).parts:
        current = current / component
        if current.is_symlink() or not current.resolve().is_relative_to(project):
            raise ValueError(f"Installation path must not contain a symlink: {current}")
        if current.exists() and not current.is_dir():
            raise ValueError(f"Installation directory is occupied by a file: {current}")


def tree_hashes(directory):
    if directory.is_symlink():
        raise ValueError(f"Existing skill is a symlink: {directory}")
    if directory.exists() and not directory.is_dir():
        raise ValueError(f"Skill destination is not a directory: {directory}")
    result = {}
    for entry in directory.rglob("*") if directory.exists() else []:
        if entry.is_symlink() or (not entry.is_dir() and not entry.is_file()):
            raise ValueError(f"Existing skill contains a non-regular entry: {entry}")
        if entry.is_file():
            result[entry.relative_to(directory).as_posix()] = digest(entry.read_bytes())
    return result


def _identity(path):
    metadata = path.lstat()
    return (metadata.st_dev, metadata.st_ino, metadata.st_mode, metadata.st_size,
            metadata.st_mtime_ns, metadata.st_ctime_ns)


def _tree_state(path):
    files = tree_hashes(path)
    if not path.exists():
        return None
    metadata = path.stat()
    entries = {}
    for entry in path.rglob('*'):
        if entry.is_symlink():
            raise ValueError('Recovery path contains a symlink')
        identity = _identity(entry)
        entries[entry.relative_to(path).as_posix()] = identity if entry.is_file() else identity[:3]
    if files != tree_hashes(path):
        raise ValueError('Recovery tree changed during inspection')
    return {'identity': (metadata.st_dev, metadata.st_ino, metadata.st_mode),
            'files': files, 'entries': entries}


class _StagingOwnership:
    def __init__(self, root):
        self.root = root
        self.expected = {'': (_identity(root)[:3], None)}

    def parents(self, path):
        relative = path.relative_to(self.root)
        current = self.root
        for part in relative.parts:
            current = current / part
            name = current.relative_to(self.root).as_posix()
            if name not in self.expected:
                current.mkdir()
                self.expected[name] = (_identity(current)[:3], None)
            elif current.is_symlink() or _identity(current)[:3] != self.expected[name][0]:
                raise ValueError('Staging directory ownership changed')

    def write(self, path, content):
        self.parents(path.parent)
        with path.open('xb') as stream:
            stream.write(content)
        path.chmod(0o644)
        self.expected[path.relative_to(self.root).as_posix()] = (_identity(path), digest(content))

    def tree(self, name, state):
        if state is None:
            return
        self.parents((self.root / name).parent)
        self.expected[name] = (state['identity'], None)
        for relative, identity in state['entries'].items():
            self.expected[name + '/' + relative] = (identity, state['files'].get(relative))

    def forget(self, name):
        for path in list(self.expected):
            if path == name or path.startswith(name + '/'):
                del self.expected[path]

    def verify(self):
        actual = {path.relative_to(self.root).as_posix(): path for path in self.root.rglob('*')}
        if set(actual) != set(self.expected) - {''} or self.root.is_symlink() or _identity(self.root)[:3] != self.expected[''][0]:
            raise ValueError('Unknown or replaced staging entries; preserve remnants')
        for name, path in actual.items():
            identity, checksum = self.expected[name]
            if path.is_symlink() or (_identity(path) if checksum is not None else _identity(path)[:3]) != identity:
                raise ValueError('Changed staging entries; preserve remnants')
            if checksum is not None and digest(path.read_bytes()) != checksum:
                raise ValueError('Changed staging content; preserve remnants')


class _InstallJournal:
    def __init__(self, project, destination, expected, staging):
        self.project = project
        self.destination = destination
        self.expected = dict(expected)
        self.moves = []
        self.phase = 'applying'
        self.ownership = _StagingOwnership(staging)

    def verify_selected(self):
        check_components(self.project, self.destination)
        for name, expected in self.expected.items():
            if _tree_state(self.destination / name) != expected:
                raise ValueError(f'Selected destination changed before commit: {name}')


def install(archive, project, host="codex", selected=None, dry_run=False, upgrade=False, expected_sha256=None):
    if host not in HOST_DIRS:
        raise ValueError(f"Unsupported host: {host}")
    supplied_project = Path(project).absolute()
    if supplied_project.is_symlink():
        raise ValueError("Project root must not be a symlink")
    project = supplied_project.resolve(strict=True)
    if not project.is_dir():
        raise ValueError("Project root must be an existing directory")
    manifest, contents = read_archive(archive, expected_sha256)
    available = {skill["name"] for skill in manifest["skills"]}
    selected = list(selected) if selected is not None else [skill["name"] for skill in manifest["skills"]]
    if not selected or len(set(selected)) != len(selected) or not set(selected).issubset(available):
        raise ValueError("Select unique declared skill names")
    destination = project / HOST_DIRS[host]
    check_components(project, destination)
    receipt_path = destination / RECEIPT
    if receipt_path.is_symlink():
        raise ValueError("Installation receipt must not be a symlink")
    receipt_content = receipt_path.read_bytes() if receipt_path.exists() else None
    receipt_identity = _identity(receipt_path) if receipt_path.exists() else None
    receipt = parse_json(receipt_content) if receipt_content is not None else {}
    if not isinstance(receipt, dict) or (receipt_content is not None and (receipt.get("schema_version") != 1 or receipt.get("package") != PACKAGE or not isinstance(receipt.get("skills"), dict))):
        raise ValueError("Invalid existing installation receipt")
    for name, record in receipt.get("skills", {}).items():
        if not valid_skill_name(name) or not isinstance(record, dict) or not isinstance(record.get("files"), dict):
            raise ValueError("Invalid managed-skill receipt")
        for relative, checksum in record["files"].items():
            safe_relative(relative)
            if not isinstance(checksum, str) or not re.fullmatch(r"[0-9a-f]{64}", checksum):
                raise ValueError("Invalid managed-file checksum")
    proposed = {}
    before = {}
    before_states = {}
    changed = []
    for name in selected:
        prefix = f"skills/{name}/"
        proposed[name] = {path[len(prefix):]: content for path, content in contents.items() if path.startswith(prefix)}
        before_states[name] = _tree_state(destination / name)
        before[name] = before_states[name]['files'] if before_states[name] is not None else {}
        checksums = {path: digest(content) for path, content in proposed[name].items()}
        if (destination / name).exists() and before[name] != checksums:
            previous = receipt.get("skills", {}).get(name)
            if not upgrade or not previous or previous.get("files") != before[name]:
                raise ValueError(f"Conflict or local modifications in {name}; refusing to overwrite")
        if not (destination / name).exists() or before[name] != checksums:
            changed.append(name)
    result = {"package": PACKAGE, "version": manifest.get("version"), "host": host,
              "destination": str(destination), "installed": [] if dry_run else changed,
              "planned": changed if dry_run else [], "unchanged": [name for name in selected if name not in changed],
              "dry_run": dry_run, "qualification": manifest.get("qualification", {})}
    if dry_run:
        return result
    check_components(project, destination)
    destination.mkdir(parents=True, exist_ok=True)
    lock = destination / ".mdbecker-skills.lock"
    lock_descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    os.close(lock_descriptor)
    lock_identity = _identity(lock)
    staging = None
    staging_identity = None
    moved = []
    committed = False
    preserve = False
    result['committed'] = False
    prepared_identity = None
    prepared_content = None
    journal = None
    try:
        if (receipt_path.is_symlink() or (receipt_path.read_bytes() if receipt_path.exists() else None) != receipt_content
                or (_identity(receipt_path) if receipt_path.exists() else None) != receipt_identity):
            raise ValueError("Installation receipt changed; rerun preflight")
        staging = Path(tempfile.mkdtemp(prefix='.skills-install-', dir=destination))
        staging_identity = _identity(staging)[:3]
        journal = _InstallJournal(project, destination, before_states, staging)
        moved = journal.moves
        ownership = journal.ownership
        incoming_states = {}
        for name in changed:
            incoming = staging / 'new' / name
            for relative, content in proposed[name].items():
                target = incoming / relative
                ownership.write(target, content)
            incoming_states[name] = _tree_state(incoming)
            journal.expected[name] = incoming_states[name]
        for name in changed:
            check_components(project, destination)
            if _tree_state(destination / name) != before_states[name]:
                raise ValueError(f'Skill changed during installation: {name}')
            backup = staging / 'backup' / name
            ownership.parents(backup.parent)
            record = {'name': name, 'replacement': None, 'backup': before_states[name], 'placed': False}
            moved.append(record)
            if (destination / name).exists():
                ownership.tree('backup/' + name, before_states[name])
                os.replace(destination / name, backup)
            record['replacement'] = incoming_states[name]
            os.replace(staging / 'new' / name, destination / name)
            ownership.forget('new/' + name)
            record['placed'] = True
        updated = dict(receipt.get('skills', {}))
        for name in selected:
            updated[name] = {'version': manifest.get('version'), 'files': {path: digest(content) for path, content in proposed[name].items()}}
        prepared_receipt = staging / 'receipt.json'
        ownership.write(prepared_receipt, (json.dumps({'schema_version': 1, 'package': PACKAGE, 'skills': updated}, indent=2) + '\n').encode())
        prepared_identity = _identity(prepared_receipt)[:4]
        prepared_content = prepared_receipt.read_bytes()
        if (receipt_path.is_symlink() or (receipt_path.read_bytes() if receipt_path.exists() else None) != receipt_content
                or (_identity(receipt_path) if receipt_path.exists() else None) != receipt_identity):
            raise ValueError('Installation receipt changed before commit; preserve competing edits')
        journal.verify_selected()
        os.replace(prepared_receipt, receipt_path)
        ownership.forget('receipt.json')
        committed = True
        journal.phase = 'committed'
        result['committed'] = True
    except BaseException as error:
        if prepared_identity is not None:
            try:
                committed = (not receipt_path.is_symlink() and _identity(receipt_path)[:4] == prepared_identity
                             and receipt_path.read_bytes() == prepared_content)
            except OSError:
                committed = False
        if committed:
            journal.phase = 'committed'
            journal.ownership.forget('receipt.json')
            result['committed'] = True
            result['commit_acknowledgement_error'] = str(error)
            if isinstance(error, OSError):
                return result
            raise
        recovery_errors = []
        if journal is not None:
            journal.phase = 'recovering'
        for record in reversed(moved):
            name = record['name']
            installed = destination / name
            backup = staging / 'backup' / name
            try:
                check_components(project, destination)
                actual = _tree_state(installed)
                if not backup.exists() and actual == record['backup'] and record['replacement'] is None:
                    continue
                if actual is None and record['placed']:
                    raise ValueError('Completed replacement disappeared; preserve original backup')
                if actual is not None:
                    if actual != record['replacement']:
                        raise ValueError('Destination ownership changed; preserve competing edits')
                    retained = staging / 'rollback' / name
                    journal.ownership.parents(retained.parent)
                    os.replace(installed, retained)
                    journal.ownership.forget('new/' + name)
                    journal.ownership.tree('rollback/' + name, record['replacement'])
                if record['backup'] is not None:
                    if _tree_state(backup) != record['backup']:
                        raise ValueError('Original backup changed; preserve recovery material')
                    os.replace(backup, installed)
                    journal.ownership.forget('backup/' + name)
            except (OSError, ValueError) as recovery_error:
                recovery_errors.append(f'{name}: {recovery_error}')
        if recovery_errors:
            preserve = True
            raise OSError(f'{error}; incomplete recovery: {"; ".join(recovery_errors)}; recovery location: {staging}') from error
        raise
    finally:
        active_error = sys.exc_info()[1]
        cleanup_failure = None
        if staging is not None and not preserve:
            try:
                if staging.is_symlink() or _identity(staging)[:3] != staging_identity:
                    raise ValueError('Staging ownership changed')
                journal.ownership.verify()
                shutil.rmtree(staging)
            except (OSError, ValueError) as cleanup_error:
                result['recovery_location'] = str(staging)
                result['cleanup_error'] = str(cleanup_error)
                cleanup_failure = cleanup_error
        try:
            if not lock.is_symlink() and _identity(lock) == lock_identity:
                lock.unlink()
        except OSError:
            result['lock_preserved'] = True
        if cleanup_failure is not None and not committed:
            raise OSError(f'{active_error or "Cleanup failed"}; recovery location: {staging}; {cleanup_failure}') from active_error
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--host", choices=HOST_DIRS, default="codex")
    parser.add_argument("--skills", nargs="+")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--upgrade", action="store_true", help="Replace only previously managed, unchanged skills")
    parser.add_argument("--sha256", help="Expected archive checksum from the trusted release")
    arguments = parser.parse_args()
    if sys.version_info < (3, 11):
        parser.error("Python 3.11+ is required; dependencies are never installed automatically")
    try:
        result = install(arguments.archive, arguments.project, arguments.host, arguments.skills,
                         arguments.dry_run, arguments.upgrade, arguments.sha256)
    except (ValueError, OSError, zipfile.BadZipFile, KeyError, TypeError) as error:
        parser.exit(1, f"error: {error}\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
