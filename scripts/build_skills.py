#!/usr/bin/env python3
"""Export self-contained skill bundles from explicit canonical sources."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import tempfile
import zipfile


ROOT = Path(__file__).resolve().parents[1]


def digest(content):
    return hashlib.sha256(content).hexdigest()


def payload(root=ROOT):
    inventory_content = (root / "inventory.json").read_bytes()
    inventory = json.loads(inventory_content)
    names = inventory["parents"] + inventory["compatibility"]
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

    def add(source, destination, transform=None):
        if not source.resolve().is_relative_to(root.resolve()) or source.is_symlink() or any(parent.is_symlink() for parent in source.parents if parent.is_relative_to(root)) or not source.is_file():
            raise ValueError(f"Missing or non-regular canonical source: {source}")
        identity = source.relative_to(root).as_posix()
        if identity not in captured:
            captured[identity] = source.read_bytes()
        content = captured[identity]
        inputs[identity] = digest(content)
        if destination in result:
            raise ValueError(f"Duplicate export destination: {destination}")
        result[destination] = transform(content) if transform else content

    def method(content):
        body = re.sub(rb"\A---\r?\n.*?\r?\n---\r?\n", b"", content, count=1, flags=re.S)
        body = body.replace(b"](resources/", b"](../")
        body = body.replace(b"alongside this `SKILL.md`", b"beside this bundled `method.md`")
        body = body.replace(b"from the installed skill directory", b"from this bundled method's directory")
        return b"Bundled canonical method: resolve its helper beside this file; normalize parent arguments to the legacy invocation.\n\n" + body

    shared = [root / relative for relative in inventory["common_resources"]]
    for name in names:
        prefix = f"skills/{name}/"
        add(root / name / "SKILL.md", prefix + "SKILL.md")
        for relative in inventory["owned_resources"][name]:
            source = root / name / relative
            add(source, prefix + source.relative_to(root / name).as_posix())
        for source in shared:
            add(source, prefix + "resources/" + source.relative_to(root / "resources").as_posix())
        if name == "iterate":
            add(root / "iterate/manifest.py", prefix + "manifest.py")
        for legacy in inventory.get("method_exports", {}).get(name, []):
            if legacy not in inventory["compatibility"]:
                raise ValueError("Undeclared canonical method export")
            add(root / legacy / "SKILL.md", prefix + f"resources/{legacy}/method.md", method)
            if legacy == "iterate":
                add(root / "iterate/manifest.py", prefix + "resources/iterate/manifest.py")
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
    gates = [status.get(key) for key in ("release_approval", "model_protocol_approval", "manual_acceptance", "deterministic", "model_quality", "reference_fidelity", "transfer")]
    for host in ("codex", "claude"):
        record = status.get("hosts", {}).get(host, {})
        if not isinstance(record, dict):
            return False
        gates.extend(record.get(key) for key in ("installation", "invocation", "hierarchy"))
    fingerprint_matches = isinstance(inputs, dict) and status.get("source_inputs_sha256") == digest(json.dumps(inputs, sort_keys=True).encode())
    return all(gate == "passed" for gate in gates) and fingerprint_matches


def prepare(root=ROOT):
    inventory, files, unused_inputs = payload(root)
    for name in inventory["parents"] + inventory["compatibility"]:
        prefix = f"skills/{name}/resources/"
        for path, content in files.items():
            if path.startswith(prefix):
                target = root / name / "resources" / path[len(prefix):]
                current = root / name
                for component in target.relative_to(current).parts:
                    current = current / component
                    if current.is_symlink():
                        raise ValueError(f"Generated resource path is a symlink: {current}")
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(content)
    return inventory


def build(output, version="dev", root=ROOT, release=False, prerelease=False):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}", version):
        raise ValueError("Version must be a safe release label")
    inventory, files, inputs = payload(root)
    status = qualification(root)
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=True).stdout.strip()
    dirty = bool(subprocess.run(["git", "status", "--porcelain"], cwd=root, capture_output=True, text=True, check=True).stdout)
    if release and dirty:
        raise ValueError("Release archives require a clean committed source snapshot")
    if release and not prerelease and not release_ready(status, inputs):
        raise ValueError("Stable release blocked: required approval, host or model-quality gates have not passed; use an explicitly labeled prerelease")
    manifest = {"schema_version": 1, "package": inventory["package"], "version": version,
                "commit": commit, "source_state": "working-tree" if dirty else "committed", "prerelease": prerelease,
                "host_profiles": {"codex": ".agents/skills", "claude": ".claude/skills"},
                "skills": [{"name": name, "path": f"skills/{name}", "kind": "parent" if name in inventory["parents"] else "compatibility",
                            "required_files": sorted(path[len(f"skills/{name}/"):] for path in files if path.startswith(f"skills/{name}/"))}
                           for name in inventory["parents"] + inventory["compatibility"]],
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
