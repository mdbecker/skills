#!/usr/bin/env python3
"""Install verified skill folders from an explicitly selected release archive."""

import argparse
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import posixpath
import re
import shutil
import stat
import sys
import tempfile
import unicodedata
import zipfile


HOST_DIRS = {"codex": ".agents/skills", "claude": ".claude/skills"}
PACKAGE = "mdbecker-skills"
MAX_FILES = 2000
MAX_BYTES = 32 * 1024 * 1024
RECEIPT = ".mdbecker-skills.json"


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
    return json.loads(content, object_pairs_hook=unique_object)


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
        if not isinstance(name, str) or not re.fullmatch(r"[a-z][a-z0-9-]{0,63}", name):
            raise ValueError("Invalid skill name")
        if name.casefold() in names or skill.get("path") != f"skills/{name}":
            raise ValueError("Duplicate skill name or unexpected skill path")
        names.add(name.casefold())
        if f"skills/{name}/SKILL.md" not in contents:
            raise ValueError(f"Missing skill entrypoint: {name}")
        entrypoint = contents[f"skills/{name}/SKILL.md"].decode("utf-8")
        frontmatter = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|$)", entrypoint, re.S)
        if not frontmatter:
            raise ValueError(f"Missing skill metadata: {name}")
        declared_names = re.findall(r"(?m)^name:\s*([^\r\n]+)$", frontmatter.group(1))
        descriptions = re.findall(r"(?m)^description:\s*([^\r\n]+)$", frontmatter.group(1))
        if len(declared_names) != 1 or declared_names[0].strip().strip('\"\'') != name or len(descriptions) != 1 or descriptions[0].strip() in {"", ">", "|", "null", "~"} or descriptions[0].lstrip().startswith("#"):
            raise ValueError(f"Invalid skill name/description metadata: {name}")
        required = skill.get("required_files")
        actual = {path[len(f"skills/{name}/"):] for path in contents if path.startswith(f"skills/{name}/")}
        if not isinstance(required, list) or not required or len(set(required)) != len(required) or set(required) != actual:
            raise ValueError(f"Incomplete resource closure: {name}")
        for relative in required:
            safe_relative(relative)
            path = f"skills/{name}/{relative}"
            if relative.endswith(".md"):
                for target in re.findall(r"\]\(([^)]+)\)", contents[path].decode("utf-8")):
                    if "://" in target or target.startswith("#"):
                        continue
                    resolved = posixpath.normpath(posixpath.join(posixpath.dirname(path), target.split("#", 1)[0]))
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
    receipt = parse_json(receipt_content) if receipt_content is not None else {}
    if not isinstance(receipt, dict) or (receipt_content is not None and (receipt.get("schema_version") != 1 or receipt.get("package") != PACKAGE or not isinstance(receipt.get("skills"), dict))):
        raise ValueError("Invalid existing installation receipt")
    for name, record in receipt.get("skills", {}).items():
        if not re.fullmatch(r"[a-z][a-z0-9-]{0,63}", name) or not isinstance(record, dict) or not isinstance(record.get("files"), dict):
            raise ValueError("Invalid managed-skill receipt")
        for relative, checksum in record["files"].items():
            safe_relative(relative)
            if not isinstance(checksum, str) or not re.fullmatch(r"[0-9a-f]{64}", checksum):
                raise ValueError("Invalid managed-file checksum")
    proposed = {}
    before = {}
    changed = []
    for name in selected:
        prefix = f"skills/{name}/"
        proposed[name] = {path[len(prefix):]: content for path, content in contents.items() if path.startswith(prefix)}
        before[name] = tree_hashes(destination / name)
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
    try:
        if receipt_path.is_symlink() or (receipt_path.read_bytes() if receipt_path.exists() else None) != receipt_content:
            raise ValueError("Installation receipt changed; rerun preflight")
        with tempfile.TemporaryDirectory(prefix=".skills-install-", dir=destination) as temporary:
            staging = Path(temporary)
            moved = []
            try:
                for name in changed:
                    incoming = staging / "new" / name
                    for relative, content in proposed[name].items():
                        target = incoming / relative
                        target.parent.mkdir(parents=True, exist_ok=True)
                        target.write_bytes(content)
                        target.chmod(0o644)
                for name in changed:
                    check_components(project, destination)
                    if tree_hashes(destination / name) != before[name]:
                        raise ValueError(f"Skill changed during installation: {name}")
                    backup = staging / "backup" / name
                    backup.parent.mkdir(parents=True, exist_ok=True)
                    if (destination / name).exists():
                        os.replace(destination / name, backup)
                    moved.append(name)
                    os.replace(staging / "new" / name, destination / name)
                updated = dict(receipt.get("skills", {}))
                for name in selected:
                    updated[name] = {"version": manifest.get("version"), "files": {path: digest(content) for path, content in proposed[name].items()}}
                new_receipt = {"schema_version": 1, "package": PACKAGE, "skills": updated}
                prepared_receipt = staging / "receipt.json"
                prepared_receipt.write_text(json.dumps(new_receipt, indent=2) + "\n")
                if receipt_path.is_symlink():
                    raise ValueError("Receipt changed into a symlink during installation")
                os.replace(prepared_receipt, receipt_path)
            except BaseException:
                for name in reversed(moved):
                    installed = destination / name
                    if installed.exists():
                        shutil.rmtree(installed)
                    backup = staging / "backup" / name
                    if backup.exists():
                        os.replace(backup, installed)
                raise
    finally:
        lock.unlink()
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
