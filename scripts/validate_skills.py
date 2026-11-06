"""Validate publication source and self-contained skill packages."""

from pathlib import Path
import argparse
import hashlib
import json
import re
import sys

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from distribution.install import parse_skill_metadata
from scripts.source_access import SourceSnapshot, validate_inputs, _git
from scripts.navigation import markdown_navigation, resolve_target, relocate_markdown, validate_documents
from scripts.inventory import source_paths


def _current_locators(snapshot):
    source = 'evaluations/workflow-methods/traceability.json'
    if source not in snapshot.entries:
        return
    current = 'evaluations/workflow-methods/current-locators.json'
    snapshot.eligible(current)
    snapshot.eligible(source)
    mapping = json.loads(snapshot.read(current))
    original = snapshot.read(source)
    if (mapping.get('schema_version') != 1 or mapping.get('path_base') != 'repository_root'
            or mapping.get('historical_ledger') != {'path': 'traceability.json', 'sha256': hashlib.sha256(original).hexdigest()}):
        raise ValueError('Current locator map has an invalid historical binding')
    aliases = mapping.get('aliases')
    if not isinstance(aliases, dict):
        raise ValueError('Current locator aliases must be explicit')
    used = set()
    for requirement in json.loads(original)['requirements']:
        for locator in requirement['instruction_or_reference'] + requirement['worked_case']:
            target = locator
            if '/references/' in locator:
                if locator not in aliases:
                    raise ValueError('Missing explicit current locator alias')
                target = aliases[locator]
                used.add(locator)
            resolved, fragment = resolve_target('root.md', target)
            if resolved is None or fragment:
                raise ValueError('Current locators must be repository file paths')
            snapshot.eligible(resolved)
        for module in requirement.get('verification_modules', []):
            snapshot.eligible(module.replace('.', '/') + '.py')
    if used != set(aliases):
        raise ValueError('Unused or incomplete current locator aliases')


def _current_paths(snapshot):
    def require(target, base='root.md'):
        resolved, fragment = resolve_target(base, target)
        if resolved is None or fragment:
            raise ValueError('Declared current locators must be local file paths')
        snapshot.eligible(resolved)

    if 'inventory.json' in snapshot.entries:
        snapshot.eligible('inventory.json')
        for target in source_paths(json.loads(snapshot.read('inventory.json'))):
            require(target)
    for source in snapshot.entries:
        if source.startswith('.github/workflows/') and source.endswith(('.yml', '.yaml')):
            snapshot.eligible(source)
            workflow = yaml.safe_load(snapshot.read(source))
            for job in workflow.get('jobs', {}).values():
                for step in job.get('steps', []):
                    for target in re.findall(r'\bpython[0-9.]*\s+((?:scripts|distribution)/[\w./-]+\.py)', step.get('run', '')):
                        require(target)
                    for target in re.findall(r'\s-r\s+([\w./-]+\.txt)', step.get('run', '')):
                        require(target)
        if source == 'evaluations/matrix.json':
            snapshot.eligible(source)
            for row in json.loads(snapshot.read(source)).get('rows', []):
                for field in ('method', 'deterministic_tests', 'validation_extension', 'acceptance', 'qualification', 'contract'):
                    if field in row:
                        require(row[field])
        if source.startswith('evaluations/') and source.endswith('/traceability.json') and source != 'evaluations/workflow-methods/traceability.json':
            snapshot.eligible(source)
            data = json.loads(snapshot.read(source))
            if 'test_suite' in data:
                require(data['test_suite'])
            if 'test_results' in data:
                require(data['test_results'], source)
            for row in data.get('requirements', data.get('rows', [])):
                for field in ('sources', 'implementation', 'references'):
                    for target in row.get(field, []):
                        require(target)
                if 'worked' in row:
                    require(row['worked'])
        if source == 'evaluations/status.json':
            snapshot.eligible(source)
            for record in json.loads(snapshot.read(source)).values():
                if isinstance(record, dict) and 'qualification_record' in record:
                    require(record['qualification_record'])


def validate_source(root=ROOT, snapshot='index'):
    errors = []
    try:
        view = SourceSnapshot(root, snapshot)
        excluded = view.ignored(view.entries)
        if excluded:
            return ['Tracked publication files conflict with ignore rules']
        for source in view.entries:
            if Path(source).suffix.lower() not in {'.md', '.markdown'}:
                continue
            try:
                view.eligible(source)
                edges, unused_anchors = markdown_navigation(view.read(source).decode('utf-8'))
                for edge in edges:
                    try:
                        target, fragment = resolve_target(source, edge['target'])
                        if target is None:
                            continue
                        view.eligible(target)
                        if fragment and fragment not in markdown_navigation(view.read(target).decode('utf-8'))[1]:
                            raise ValueError('Missing target anchor')
                    except (ValueError, UnicodeError, KeyError) as error:
                        errors.append(f'{source}:{edge["line"]}: {error}')
            except (ValueError, UnicodeError, KeyError) as error:
                errors.append(f'{source}: {error}')
        try:
            _current_locators(view)
            _current_paths(view)
        except (ValueError, KeyError, TypeError, yaml.YAMLError) as error:
            errors.append(f'Current locators: {error}')
    except (ValueError, OSError) as error:
        errors.append(str(error))
    return errors


def main(argv=()):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', action='store_true')
    parser.add_argument('--snapshot', choices=['HEAD', 'index'], default='HEAD')
    arguments = parser.parse_args(argv)
    if arguments.source:
        errors = validate_source(ROOT, arguments.snapshot)
        if errors:
            print('\n'.join(errors), file=sys.stderr)
            return 1
        print(f'All Markdown and current locators in {arguments.snapshot} satisfy source policy.')
        return 0
    from scripts.build_skills import payload
    errors = []
    try:
        inventory, exported, inputs = payload(ROOT)
    except (ValueError, OSError, KeyError) as error:
        print(str(error), file=sys.stderr)
        return 1
    errors.extend(validate_documents(exported))
    discovery = ROOT / ".agents/skills"
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
            expected_identity = f'{name}/{relative}'
            safe = (local.resolve().is_relative_to(directory.resolve()) and not local.is_symlink()
                    and not any(parent.is_symlink() for parent in local.parents if parent.is_relative_to(directory))
                    and local.is_file())
            matches = safe and (local.read_bytes() == content if relative.startswith('resources/')
                       else hashlib.sha256(local.read_bytes()).hexdigest() == inputs.get(expected_identity))
            if not matches:
                errors.append(f"{local}: missing/stale resource; run scripts/build_skills.py --prepare")
                continue
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
    raise SystemExit(main(sys.argv[1:]))
