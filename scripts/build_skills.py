#!/usr/bin/env python3
"""Export self-contained skill bundles from explicit canonical sources."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import zipfile


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from distribution.install import parse_json, parse_skill_metadata, read_archive, safe_relative


def digest(content):
    return hashlib.sha256(content).hexdigest()


def payload(root=ROOT):
    inventory_content = (root / "inventory.json").read_bytes()
    inventory = json.loads(inventory_content)
    names = inventory["parents"]
    if inventory.get("schema_version") != 1 or len(set(names)) != len(names):
        raise ValueError("Invalid or duplicate export inventory")
    if any(not re.fullmatch(r"[a-z][a-z0-9-]{0,63}", name) for name in names):
        raise ValueError("Invalid exported skill name")
    relative_sources = inventory["common_resources"] + [relative for name in names for relative in inventory["owned_resources"][name]]
    for relative in relative_sources:
        if not isinstance(relative, str) or Path(relative).is_absolute() or ".." in Path(relative).parts or "\\" in relative or ":" in relative:
            raise ValueError("Inventory resources must use bounded relative paths")
    result = {}
    inputs = {"inventory.json": digest(inventory_content),
              "scripts/build_skills.py": digest((root / "scripts/build_skills.py").read_bytes())}
    captured = {"inventory.json": inventory_content}

    def add(source, destination):
        if not source.resolve().is_relative_to(root.resolve()) or source.is_symlink() or any(parent.is_symlink() for parent in source.parents if parent.is_relative_to(root)) or not source.is_file():
            raise ValueError(f"Missing or non-regular canonical source: {source}")
        identity = source.relative_to(root).as_posix()
        if identity not in captured:
            captured[identity] = source.read_bytes()
        content = captured[identity]
        inputs[identity] = digest(content)
        if destination is None:
            return
        if destination.endswith('/SKILL.md'):
            parse_skill_metadata(content, source.parent.name)
        if destination in result:
            raise ValueError(f"Duplicate export destination: {destination}")
        result[destination] = content

    add(root / 'distribution/__init__.py', None)
    shared = [root / relative for relative in inventory["common_resources"]]
    for name in names:
        prefix = f"skills/{name}/"
        add(root / name / "SKILL.md", prefix + "SKILL.md")
        for relative in inventory["owned_resources"][name]:
            source = root / name / relative
            add(source, prefix + source.relative_to(root / name).as_posix())
        for source in shared:
            add(source, prefix + "resources/" + source.relative_to(root / "resources").as_posix())
    for source, target in [("distribution/README.md", "README.md"), ("distribution/install.py", "install.py"),
                           ("LICENSE", "LICENSE"), ("NOTICE", "NOTICE")]:
        add(root / source, target)
    for identity, checksum in inputs.items():
        source = root / identity
        if not source.resolve().is_relative_to(root.resolve()) or source.is_symlink() or digest(source.read_bytes()) != checksum:
            raise ValueError(f"Canonical source changed during export: {identity}")
    return inventory, result, inputs


def qualification(root=ROOT):
    status = json.loads((root / "evaluations/status.json").read_text())
    if not isinstance(status, dict) or type(status.get("schema_version")) is not int or status.get("schema_version") != 1 or not isinstance(status.get("hosts"), dict):
        raise ValueError("Invalid qualification record")
    return status


def release_ready(status, inputs):
    if not publication_ready(status):
        return False
    gates = [status.get(key) for key in ("release_approval", "model_protocol_approval", "manual_acceptance", "deterministic", "model_quality", "reference_fidelity", "transfer")]
    for host in ("codex", "claude"):
        record = status.get("hosts", {}).get(host, {})
        if not isinstance(record, dict):
            return False
        gates.extend(record.get(key) for key in ("installation", "invocation", "hierarchy"))
    fingerprint_matches = isinstance(inputs, dict) and status.get("source_inputs_sha256") == digest(json.dumps(inputs, sort_keys=True).encode())
    return all(gate == "passed" for gate in gates) and fingerprint_matches


def publication_ready(status):
    publication = status.get('publication', {})
    return isinstance(publication, dict) and all(publication.get(gate) == 'passed' for gate in
        ('public_content', 'private_markers', 'semantic_review', 'distribution_rights', 'history_review'))


def _checked_preparation_path(root, relative, directory=False):
    parts = safe_relative(relative).parts
    current = root
    for index, component in enumerate(parts):
        current = current / component
        if current.is_symlink() or not current.resolve().is_relative_to(root.resolve()):
            raise ValueError(f"Unsafe preparation path: {current}")
        if current.exists():
            expected_directory = directory or index < len(parts) - 1
            if expected_directory and not current.is_dir() or not expected_directory and not current.is_file():
                raise ValueError(f"Non-regular preparation path: {current}")
    return current


def _file_state(path):
    if path.is_symlink():
        raise ValueError(f"Linked preparation file: {path}")
    if not path.exists():
        return None
    if not path.is_file():
        raise ValueError(f"Non-regular preparation file: {path}")
    before = path.stat()
    content = path.read_bytes()
    after = path.stat()
    attributes = lambda metadata: (metadata.st_dev, metadata.st_ino, metadata.st_size,
                                   metadata.st_mtime_ns, metadata.st_ctime_ns, stat.S_IMODE(metadata.st_mode))
    if attributes(before) != attributes(after):
        raise ValueError(f"Preparation file changed during inspection: {path}")
    return {"identity": (after.st_dev, after.st_ino), "sha256": digest(content),
            "mode": stat.S_IMODE(after.st_mode)}


def _validate_preparation_receipt(receipt, package):
    if (not isinstance(receipt, dict) or type(receipt.get("schema_version")) is not int
            or receipt["schema_version"] != 1 or receipt.get("package") != package
            or not isinstance(receipt.get("skills"), dict)):
        raise ValueError("Invalid preparation ownership receipt")
    for name, record in receipt["skills"].items():
        if not re.fullmatch(r"[a-z][a-z0-9-]{0,63}", name) or not isinstance(record, dict) or not isinstance(record.get("files"), dict):
            raise ValueError("Invalid preparation skill record")
        for relative, metadata in record["files"].items():
            parts = safe_relative(relative).parts
            if (len(parts) < 2 or parts[0] != "resources" or ':' in relative or '__pycache__' in parts
                    or not isinstance(metadata, dict) or not isinstance(metadata.get("sha256"), str)
                    or not re.fullmatch(r"[0-9a-f]{64}", metadata["sha256"])
                    or type(metadata.get("mode")) is not int or not 0 <= metadata["mode"] <= 0o7777):
                raise ValueError(f"Invalid preparation file record: {name}/{relative}")


def _resource_files(root, name):
    directory = _checked_preparation_path(root, f"{name}/resources", directory=True)
    result = {}
    for path in directory.rglob('*') if directory.exists() else []:
        if path.is_symlink():
            raise ValueError(f"Linked generated resource: {path}")
        if '__pycache__' in path.relative_to(directory).parts:
            continue
        if path.is_dir():
            continue
        if not path.is_file():
            raise ValueError(f"Non-regular generated resource: {path}")
        result[path.relative_to(root / name).as_posix()] = path
    return result


def _preparation_plan(root, inventory, files, receipt):
    updated = json.loads(json.dumps(receipt))
    operations = []
    expected = {}
    for name in inventory["parents"]:
        prefix = f"skills/{name}/"
        desired = {relative[len(prefix):]: content for relative, content in files.items()
                   if relative.startswith(prefix + 'resources/')}
        actual = _resource_files(root, name)
        previous = receipt["skills"].get(name, {}).get("files", {})
        records = {}
        for relative in sorted(set(desired) | set(actual) | set(previous)):
            target = _checked_preparation_path(root, f"{name}/{relative}")
            prior = previous.get(relative)
            if relative not in desired and relative not in previous and relative in actual:
                raise ValueError(f"Unknown generated file; preserve and inspect: {target}")
            if prior and target.exists() and stat.S_IMODE(target.stat().st_mode) != prior["mode"]:
                raise ValueError(f"Modified generated-file mode; preserve: {target}")
            before = _file_state(target)
            if prior and before and before["sha256"] != prior["sha256"]:
                raise ValueError(f"Modified generated file; preserve: {target}")
            if relative in desired:
                checksum = digest(desired[relative])
                if before and not prior and before["sha256"] != checksum:
                    raise ValueError(f"Unowned generated file differs from source; preserve: {target}")
                records[relative] = dict(prior or {}, sha256=checksum, mode=before["mode"] if before else None)
                expected[f"{name}/{relative}"] = before
                if before is None or before["sha256"] != checksum:
                    operations.append({"relative": f"{name}/{relative}", "before": before,
                                       "content": desired[relative], "record": records[relative]})
            elif before:
                operations.append({"relative": f"{name}/{relative}", "before": before,
                                   "content": None, "record": None})
        updated["skills"][name] = dict(receipt["skills"].get(name, {}), files=records)
    return updated, operations, expected


def _verify_preparation_sources(root, inputs):
    for relative, checksum in inputs.items():
        path = _checked_preparation_path(root, relative)
        if not path.is_file() or digest(path.read_bytes()) != checksum:
            raise ValueError(f"Canonical source changed during preparation: {relative}")


def _make_preparation_parents(root, target, created):
    current = root
    for component in target.parent.relative_to(root).parts:
        current = current / component
        _checked_preparation_path(root, current.relative_to(root).as_posix(), directory=True)
        if not current.exists():
            current.mkdir()
            metadata = current.stat()
            created.append((current, (metadata.st_dev, metadata.st_ino)))


def _rollback_preparation(root, applied, staging):
    unsafe = False
    for operation in reversed(applied):
        try:
            target = _checked_preparation_path(root, operation["relative"])
            current = _file_state(target)
            removed = operation["removed"]
            if not removed.exists() and operation["before"] is not None:
                if current != operation["before"]:
                    unsafe = True
                continue
            if current is not None:
                if current != operation.get("replacement"):
                    unsafe = True
                    continue
                discarded = staging / 'discarded' / operation["relative"]
                discarded.parent.mkdir(parents=True, exist_ok=True)
                os.replace(target, discarded)
                if _file_state(discarded) != operation["replacement"]:
                    os.link(discarded, target)
                    unsafe = True
                    continue
            if removed.exists():
                if _file_state(removed) != operation["before"]:
                    unsafe = True
                os.link(removed, target)
        except (ValueError, OSError):
            unsafe = True
    return unsafe


def _apply_preparation(root, inventory, inputs, receipt_path, receipt_before, updated, operations, expected):
    staging = Path(tempfile.mkdtemp(prefix='.prepared-resources-', dir=receipt_path.parent))
    staging_identity = (staging.stat().st_dev, staging.stat().st_ino)
    created = []
    applied = []
    preserve_recovery = False
    try:
        for operation in operations:
            relative = operation["relative"]
            target = _checked_preparation_path(root, relative)
            operation["removed"] = staging / 'removed' / relative
            operation["removed"].parent.mkdir(parents=True, exist_ok=True)
            if operation["before"]:
                backup = staging / 'backup' / relative
                backup.parent.mkdir(parents=True, exist_ok=True)
                backup.write_bytes(target.read_bytes())
                backup.chmod(operation["before"]["mode"])
                if digest(backup.read_bytes()) != operation["before"]["sha256"]:
                    raise ValueError(f"Generated file changed during backup: {target}")
            if operation["content"] is not None:
                incoming = staging / 'new' / relative
                incoming.parent.mkdir(parents=True, exist_ok=True)
                incoming.write_bytes(operation["content"])
                if operation["before"]:
                    incoming.chmod(operation["before"]["mode"])
                operation["incoming"] = incoming
                operation["replacement"] = _file_state(incoming)
                operation["record"]["mode"] = operation["replacement"]["mode"]
                expected[relative] = operation["replacement"]
        _verify_preparation_sources(root, inputs)
        if _file_state(receipt_path) != receipt_before:
            raise ValueError("Preparation receipt changed during planning")
        for operation in operations:
            target = _checked_preparation_path(root, operation["relative"])
            if _file_state(target) != operation["before"]:
                raise ValueError(f"Generated file changed during preparation: {target}")
            _make_preparation_parents(root, target, created)
            applied.append(operation)
            if operation["before"]:
                os.replace(target, operation["removed"])
            if operation["content"] is not None:
                os.link(operation["incoming"], target)
        _verify_preparation_sources(root, inputs)
        for operation in applied:
            if operation["before"] and _file_state(operation["removed"]) != operation["before"]:
                raise ValueError("A generated original changed during preparation")
        for name in inventory["parents"]:
            actual = _resource_files(root, name)
            if set(actual) != set(updated["skills"][name]["files"]):
                raise ValueError(f"Generated-file inventory changed during preparation: {name}")
        for relative, state in expected.items():
            if _file_state(_checked_preparation_path(root, relative)) != state:
                raise ValueError(f"Generated output changed during preparation: {relative}")
        if _file_state(_checked_preparation_path(root, 'dist/.prepared-resources.json')) != receipt_before:
            raise ValueError("Preparation receipt changed before commit")
        content = (json.dumps(updated, indent=2, sort_keys=True) + '\n').encode()
        if receipt_before is None or digest(content) != receipt_before["sha256"]:
            staged_receipt = staging / 'receipt.json'
            staged_receipt.write_bytes(content)
            if receipt_before:
                staged_receipt.chmod(receipt_before["mode"])
            with staged_receipt.open('rb') as stream:
                os.fsync(stream.fileno())
            os.replace(staged_receipt, receipt_path)
    except BaseException as error:
        preserve_recovery = _rollback_preparation(root, applied, staging)
        for directory, identity in reversed(created):
            try:
                _checked_preparation_path(root, directory.relative_to(root).as_posix(), directory=True)
                metadata = directory.stat()
                if (metadata.st_dev, metadata.st_ino) == identity:
                    directory.rmdir()
            except OSError:
                pass
            except ValueError:
                preserve_recovery = True
        if preserve_recovery:
            raise ValueError(f"Preparation failed; competing edits preserved; recover originals from {staging}") from error
        raise
    finally:
        if not preserve_recovery:
            try:
                _checked_preparation_path(root, staging.relative_to(root).as_posix(), directory=True)
                metadata = staging.stat()
                if (metadata.st_dev, metadata.st_ino) == staging_identity:
                    shutil.rmtree(staging)
            except (OSError, ValueError):
                pass


def prepare(root=ROOT):
    root = Path(root).absolute()
    if root.is_symlink() or not root.is_dir():
        raise ValueError("Preparation requires an ordinary repository directory")
    inventory, files, inputs = payload(root)
    bookkeeping = _checked_preparation_path(root, 'dist', directory=True)
    bookkeeping.mkdir(exist_ok=True)
    lock = _checked_preparation_path(root, 'dist/.prepared-resources.lock')
    descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    os.close(descriptor)
    lock_state = _file_state(lock)
    try:
        receipt_path = _checked_preparation_path(root, 'dist/.prepared-resources.json')
        receipt_before = _file_state(receipt_path)
        receipt = parse_json(receipt_path.read_bytes()) if receipt_before else {
            "schema_version": 1, "package": inventory["package"], "skills": {}}
        _validate_preparation_receipt(receipt, inventory["package"])
        updated, operations, expected = _preparation_plan(root, inventory, files, receipt)
        _apply_preparation(root, inventory, inputs, receipt_path, receipt_before, updated, operations, expected)
        return inventory
    finally:
        try:
            if _file_state(_checked_preparation_path(root, 'dist/.prepared-resources.lock')) == lock_state:
                lock.unlink()
        except (OSError, ValueError):
            pass


def build(output, version="dev", root=ROOT, release=False, prerelease=False):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}", version):
        raise ValueError("Version must be a safe release label")
    inventory, files, inputs = payload(root)
    status = qualification(root)
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=True).stdout.strip()
    dirty = bool(subprocess.run(["git", "status", "--porcelain"], cwd=root, capture_output=True, text=True, check=True).stdout)
    if release and dirty:
        raise ValueError("Release archives require a clean committed source snapshot")
    if release and not publication_ready(status):
        raise ValueError("Public release blocked: content, private-marker, semantic, rights and history reviews are required, including for prereleases")
    if release and not prerelease and not release_ready(status, inputs):
        raise ValueError("Stable release blocked: required approval, host or model-quality gates have not passed; use an explicitly labeled prerelease")
    manifest = {"schema_version": 1, "package": inventory["package"], "version": version,
                "commit": commit, "source_state": "working-tree" if dirty else "committed", "prerelease": prerelease,
                "host_profiles": {"codex": ".agents/skills", "claude": ".claude/skills"},
                "skills": [{"name": name, "path": f"skills/{name}", "kind": "parent",
                            "required_files": sorted(path[len(f"skills/{name}/"):] for path in files if path.startswith(f"skills/{name}/"))}
                           for name in inventory["parents"]],
                "files": {name: digest(content) for name, content in sorted(files.items())},
                "source_inputs": inputs, "qualification": status}
    files["manifest.json"] = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode()
    output = Path(output)
    if output.is_symlink() or output.with_suffix(output.suffix + ".sha256").is_symlink():
        raise ValueError("Archive and checksum destinations must not be symlinks")
    output.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=".skills-export-", dir=output.parent)
    os.close(descriptor)
    try:
        with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for name, content in sorted(files.items()):
                entry = zipfile.ZipInfo(name, date_time=(2020, 1, 1, 0, 0, 0))
                entry.compress_type = zipfile.ZIP_DEFLATED
                entry.external_attr = (stat.S_IFREG | 0o644) << 16
                archive.writestr(entry, content)
        read_archive(temporary)
        os.replace(temporary, output)
    finally:
        if Path(temporary).exists():
            Path(temporary).unlink()
    checksum = digest(output.read_bytes())
    output.with_suffix(output.suffix + ".sha256").write_text(f"{checksum}  {output.name}\n")
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "dist/skills-dev.zip")
    parser.add_argument("--version", default="dev")
    parser.add_argument("--prepare", action="store_true", help="Prepare ignored local resource closures before export")
    parser.add_argument("--release", action="store_true")
    parser.add_argument("--prerelease", action="store_true")
    arguments = parser.parse_args()
    try:
        if arguments.prepare:
            prepare()
        manifest = build(arguments.output, arguments.version, release=arguments.release, prerelease=arguments.prerelease)
    except (ValueError, OSError, KeyError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"error: {error}\n")
    print(json.dumps({"archive": str(arguments.output), "version": manifest["version"],
                      "source_state": manifest["source_state"], "skills": [skill["name"] for skill in manifest["skills"]],
                      "stable_release_ready": release_ready(manifest["qualification"], manifest["source_inputs"])}, indent=2))


if __name__ == "__main__":
    main()
