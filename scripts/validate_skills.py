"""Check the published skill metadata and project discovery links."""

from pathlib import Path
import re
import sys

import yaml


ROOT = Path(__file__).resolve().parents[1]


def main():
    errors = []
    for name in ("iterate", "debate"):
        directory = ROOT / name
        path = directory / "SKILL.md"
        match = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|$)",
                         path.read_text(encoding="utf-8"), re.DOTALL)
        if not match:
            errors.append(f"{path}: missing YAML frontmatter")
            continue
        try:
            metadata = yaml.safe_load(match.group(1))
        except yaml.YAMLError as error:
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
        link = ROOT / ".agents" / "skills" / name
        if not link.is_symlink() or link.resolve() != directory.resolve():
            errors.append(f"{link}: must link to the published skill directory")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("Both skill metadata files and discovery links are valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
