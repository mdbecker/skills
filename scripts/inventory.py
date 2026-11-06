"""Canonical source inventory shared by authoring commands."""

from pathlib import Path
from distribution.install import valid_skill_name

def source_paths(inventory):
    names = inventory["parents"]
    if inventory.get("schema_version") != 1 or len(set(names)) != len(names):
        raise ValueError("Invalid or duplicate export inventory")
    if any(not valid_skill_name(name) for name in names):
        raise ValueError("Invalid exported skill name")
    relative_sources = inventory["common_resources"] + [relative for name in names for relative in inventory["owned_resources"][name]]
    for relative in relative_sources:
        if not isinstance(relative, str) or Path(relative).is_absolute() or ".." in Path(relative).parts or "\\" in relative or ":" in relative:
            raise ValueError("Inventory resources must use bounded relative paths")
    paths = ['inventory.json', '.gitignore', 'scripts/build_skills.py', 'scripts/validate_skills.py',
             'scripts/inventory.py', 'scripts/source_access.py', 'scripts/navigation.py',
             'requirements-dev.txt', 'distribution/__init__.py', 'distribution/README.md',
             'distribution/install.py', 'LICENSE', 'NOTICE'] + inventory['common_resources']
    for name in names:
        paths.append(f'{name}/SKILL.md')
        paths.extend(f'{name}/{relative}' for relative in inventory['owned_resources'][name])
    return list(dict.fromkeys(paths))
