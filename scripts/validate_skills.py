"""Check the published skill metadata and project discovery links."""

from pathlib import Path
import re
import sys

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from distribution.install import parse_skill_metadata
from scripts.build_skills import payload
from scripts.check_public_content import scan


def main():
    errors = []
    try:
        inventory, exported, unused_inputs = payload(ROOT)
    except (ValueError, OSError, KeyError) as error:
        print(str(error), file=sys.stderr)
        return 1
    discovery = ROOT / ".agents/skills"
    content_check = scan(ROOT, paths=unused_inputs, exported=exported)
    for finding in content_check['findings']:
        errors.append(f"{finding['path']}: publication content rule {finding['rule_id']}")
    entries = discovery.iterdir() if discovery.is_dir() else []
    actual = {entry.name for entry in entries if entry.is_symlink() or entry.is_dir()}
    if actual != set(inventory["parents"]):
        errors.append(f"{discovery}: discovery entries must match the export inventory")
    for name in inventory["parents"]:
        directory = ROOT / name
        path = directory / "SKILL.md"
        match = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|$)",
                         path.read_text(encoding="utf-8"), re.DOTALL)
        if not match:
            errors.append(f"{path}: missing YAML frontmatter")
            continue
        try:
            metadata = yaml.safe_load(match.group(1) + '\n')
            portable = parse_skill_metadata(path.read_bytes(), name)
        except (yaml.YAMLError, ValueError) as error:
            errors.append(f"{path}: {error}")
            continue
        if not isinstance(metadata, dict):
            errors.append(f"{path}: frontmatter must be a mapping")
            continue
        if metadata.get("name") != name:
            errors.append(f"{path}: name must match its directory")
        description = metadata.get("description")
        if not isinstance(description, str) or not description.strip():
            errors.append(f"{path}: description must be a nonempty string")
        if {key: metadata.get(key) for key in ('name', 'description')} != portable:
            errors.append(f"{path}: YAML and portable metadata interpretations disagree")
        link = ROOT / ".agents" / "skills" / name
        if not link.is_symlink() or link.resolve() != directory.resolve():
            errors.append(f"{link}: must link to the published skill directory")
        prefix = f"skills/{name}/"
        for archive_path, content in exported.items():
            if not archive_path.startswith(prefix):
                continue
            relative = archive_path[len(prefix):]
            local = directory / relative
            if not local.resolve().is_relative_to(directory.resolve()) or local.is_symlink() or not local.is_file() or local.read_bytes() != content:
                errors.append(f"{local}: missing/stale resource; run scripts/build_skills.py --prepare")
                continue
            if local.suffix == ".md":
                for target in re.findall(r"\]\(([^)]+)\)", content.decode("utf-8")):
                    if "://" in target or target.startswith("#"):
                        continue
                    resolved = (local.parent / target.split("#", 1)[0]).resolve()
                    if not resolved.is_relative_to(directory.resolve()) or not resolved.is_file():
                        errors.append(f"{local}: unresolved/out-of-package reference {target}")
        expected_resources = {path[len(prefix):] for path in exported if path.startswith(prefix + "resources/")}
        actual_resources = {path.relative_to(directory).as_posix() for path in (directory / "resources").rglob("*")
                            if path.is_file() and "__pycache__" not in path.parts}
        if actual_resources != expected_resources:
            errors.append(f"{directory / 'resources'}: unexpected or missing generated resources")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"All {len(inventory['parents'])} entrypoints, discovery links and complete exported resources are valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
