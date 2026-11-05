"""Inspect publication candidates without certifying privacy or public history."""

import argparse
import json
from pathlib import Path
import posixpath
import re
import subprocess
import sys


PERSONAL_PATH = re.compile(r'(?:/(?:Users|home)/[A-Za-z0-9_.-]+/|[A-Za-z]:\\Users\\[A-Za-z0-9_.-]+\\)')
PRIVATE_DIRECTORIES = {'reviews', 'reports', 'archive', '.git', '.ai-state', '.aws', '.venv'}


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate JSON key')
        result[key] = value
    return result


def invalid_constant(value):
    raise ValueError('Non-finite JSON constant')


def strict_json(text):
    return json.loads(text, object_pairs_hook=unique_object, parse_constant=invalid_constant)


def candidate_paths(root):
    completed = subprocess.run(
        ['git', 'ls-files', '--cached', '--others', '--exclude-standard', '-z'],
        cwd=root, capture_output=True, check=True,
    )
    return sorted(set(name for name in completed.stdout.decode('utf-8').split('\0') if name))


def load_rules(root, path):
    if path is None:
        return []
    path = Path(path)
    if path.is_symlink() or path.resolve().is_relative_to(root.resolve()):
        raise ValueError('Private rules must be an ordinary file outside the candidate')
    record = strict_json(path.read_text(encoding='utf-8'))
    if not isinstance(record, dict) or set(record) != {'rules'} or not isinstance(record['rules'], list) or not record['rules']:
        raise ValueError('Private rules must contain a nonempty rules list')
    identities = set()
    result = []
    for rule in record['rules']:
        if (not isinstance(rule, dict) or set(rule) != {'id', 'literal'}
                or not isinstance(rule['id'], str) or not re.fullmatch(r'[a-z][a-z0-9-]{0,63}', rule['id'])
                or rule['id'] in identities or not isinstance(rule['literal'], str) or not rule['literal'].strip()):
            raise ValueError('Private rule identity or literal is invalid')
        identities.add(rule['id'])
        result.append((rule['id'], rule['literal'].casefold()))
    return result


def index_entries(root):
    completed = subprocess.run(['git', 'ls-files', '--stage', '-z'], cwd=root,
                               capture_output=True, check=True)
    entries = []
    for record in completed.stdout.decode('utf-8').split('\0'):
        if not record:
            continue
        metadata, separator, path = record.partition('\t')
        fields = metadata.split()
        if (not separator or len(fields) != 3 or not re.fullmatch(r'[0-7]{6}', fields[0])
                or not re.fullmatch(r'(?:[0-9a-f]{40}|[0-9a-f]{64})', fields[1])
                or fields[2] not in {'0', '1', '2', '3'}):
            raise ValueError('Index metadata is invalid')
        entries.append((path, fields[0], fields[1], fields[2]))
    return entries


def index_link_valid(path, target, links, names):
    if not target:
        return False
    current = posixpath.normpath(posixpath.join(posixpath.dirname(path), target))
    visited = set()
    for unused_iteration in range(len(links) + 1):
        if (posixpath.isabs(current) or current == '..' or current.startswith('../')
                or '\\' in current or ':' in current):
            return False
        parts = current.split('/')
        linked = next(('/'.join(parts[:index]) for index in range(1, len(parts) + 1)
                       if '/'.join(parts[:index]) in links), None)
        if linked is None:
            return current in names or any(name.startswith(current + '/') for name in names)
        if linked in visited:
            return False
        visited.add(linked)
        destination = links[linked]
        if posixpath.isabs(destination) or '\\' in destination or ':' in destination:
            return False
        suffix = current[len(linked):].lstrip('/')
        current = posixpath.normpath(posixpath.join(posixpath.dirname(linked), destination, suffix))
    return False


def scan(root, paths=None, private_rules=None, exported=None, input_mode='working'):
    root = Path(root).absolute()
    if root.is_symlink() or not root.is_dir():
        raise ValueError('Candidate must be an ordinary directory')
    if input_mode not in {'working', 'index'}:
        raise ValueError('Unknown input representation')
    rules = load_rules(root, private_rules)
    entries = index_entries(root) if input_mode == 'index' else []
    paths = (sorted({entry[0] for entry in entries}) if input_mode == 'index'
             else candidate_paths(root)) if paths is None else list(paths)
    findings = []
    inspected = 0

    def report(path, rule_id, scope, line=None, representation='text'):
        entry = {'path': path, 'rule_id': rule_id, 'scope': scope,
                 'line': line, 'representation': representation}
        if entry not in findings:
            findings.append(entry)

    def inspect_text(path, text, scope, representation='text'):
        folded = text.casefold()
        for rule_id, literal in rules:
            position = folded.find(literal)
            if position >= 0:
                line = text[:position].count('\n') + 1 if representation == 'text' else None
                report(path, rule_id, scope, line, representation)
        match = PERSONAL_PATH.search(text)
        if match:
            line = text[:match.start()].count('\n') + 1 if representation == 'text' else None
            report(path, 'personal-path', scope, line, representation)

    def inspect_bytes(path, content, scope):
        nonlocal inspected
        inspected += 1
        inspect_text(path, path, scope, 'path')
        try:
            if b'\0' in content:
                raise UnicodeError('Binary content')
            text = content.decode('utf-8')
        except UnicodeError:
            report(path, 'uninspectable', scope)
            return
        inspect_text(path, text, scope)
        if Path(path).suffix == '.json':
            try:
                decoded = strict_json(text)
            except (ValueError, TypeError):
                report(path, 'uninspectable-json', scope)
                return
            inspect_decoded(path, decoded, scope)

    def inspect_decoded(path, value, scope, depth=0):
        if depth > 32:
            report(path, 'uninspectable-json', scope, representation='decoded-json')
            return
        if isinstance(value, dict):
            for key, item in value.items():
                inspect_text(path, key, scope, 'decoded-json')
                inspect_decoded(path, item, scope, depth + 1)
        elif isinstance(value, list):
            for item in value:
                inspect_decoded(path, item, scope, depth + 1)
        elif isinstance(value, str):
            inspect_text(path, value, scope, 'decoded-json')
            if value.lstrip().startswith(('{', '[', '"')):
                try:
                    nested = strict_json(value)
                except ValueError:
                    return
                inspect_decoded(path, nested, scope, depth + 1)

    def bounded(path, scope):
        if not isinstance(path, str):
            report('<invalid-path>', 'unsafe-path', scope, representation='path')
            return False
        relative = Path(path)
        if (relative.is_absolute() or '..' in relative.parts
                or '\\' in path or not relative.parts):
            report('<invalid-path>', 'unsafe-path', scope, representation='path')
            return False
        if (relative.parts[0] in PRIVATE_DIRECTORIES or relative.name.startswith('PRD_')
                or relative.name == 'PRD.md' or relative.name.startswith('.env') and relative.name != '.env.example'
                or relative.name == 'private-rules.json'):
            report(path, 'private-artifact', scope, representation='path')
            return False
        return True

    indexed = {}
    links = {}
    if input_mode == 'index':
        entry_names = {entry[0] for entry in entries}
        for relative in paths:
            if relative not in entry_names and bounded(relative, 'source'):
                report(relative, 'index-missing', 'source', representation='index')
        for relative, mode, identity, stage in entries:
            if relative not in paths:
                continue
            if stage != '0' or relative in indexed:
                report(relative, 'index-conflict', 'source', representation='index')
                continue
            if not bounded(relative, 'source'):
                continue
            if mode not in {'100644', '100755', '120000'}:
                report(relative, 'uninspectable', 'source', representation='index')
                continue
            content = subprocess.run(['git', 'cat-file', 'blob', identity], cwd=root,
                                     capture_output=True, check=True).stdout
            indexed[relative] = (mode, content)
            if mode == '120000':
                try:
                    target = content.decode('utf-8')
                    if '\0' in target:
                        raise UnicodeError('Invalid link')
                except UnicodeError:
                    report(relative, 'unsafe-link', 'source', representation='index')
                    continue
                links[relative] = target
        for relative, (mode, content) in sorted(indexed.items()):
            if mode == '120000':
                inspect_text(relative, relative + '\n' + links.get(relative, ''), 'source', 'link')
                if relative not in links or not index_link_valid(relative, links[relative], links, set(indexed)):
                    report(relative, 'unsafe-link', 'source', representation='index')
                inspected += 1
            elif any('/'.join(Path(relative).parts[:index]) in links
                     for index in range(1, len(Path(relative).parts))):
                report(relative, 'unsafe-link', 'source', representation='index')
            else:
                inspect_bytes(relative, content, 'source')
    for relative in sorted(set(paths)) if input_mode == 'working' else []:
        if not bounded(relative, 'source'):
            continue
        source = root / relative
        if any(parent.is_symlink() for parent in source.parents if parent.is_relative_to(root)):
            report(relative, 'unsafe-link', 'source', representation='path')
            continue
        if source.is_symlink():
            target = str(source.readlink())
            inspect_text(relative, relative + '\n' + target, 'source', 'link')
            if not source.resolve().is_relative_to(root.resolve()) or not source.exists():
                report(relative, 'unsafe-link', 'source', representation='link')
            inspected += 1
        elif not source.exists():
            continue
        elif not source.is_file():
            report(relative, 'uninspectable', 'source')
        else:
            inspect_bytes(relative, source.read_bytes(), 'source')
    for relative, content in sorted((exported or {}).items()):
        if bounded(relative, 'export'):
            inspect_bytes(relative, content, 'export')
    marker_ids = {identity for identity, unused_literal in rules}
    marker_status = ('failed' if any(entry['rule_id'] in marker_ids for entry in findings)
                     else 'blocked' if findings else 'passed') if rules else 'not_run'
    return {'schema_version': 1, 'input_mode': input_mode, 'complete': not findings, 'inspected': inspected,
            'findings': findings, 'private_markers': marker_status,
            'semantic_review': 'not_run', 'history_review': 'not_run', 'publication_ready': False,
            'limits': 'Content checks do not approve semantic privacy, distribution rights, source history or publication.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--private-rules', type=Path)
    parser.add_argument('--input', choices=['working', 'index'], default='working')
    parser.add_argument('--with-export', action='store_true')
    parser.add_argument('--archive', type=Path)
    arguments = parser.parse_args()
    try:
        exported = {}
        if arguments.input == 'index' and arguments.with_export:
            raise ValueError('Working exports must be inspected separately from indexed source')
        if arguments.with_export or arguments.archive:
            sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        if arguments.with_export:
            from scripts.build_skills import payload
            unused_inventory, exported, unused_inputs = payload(arguments.root)
        if arguments.archive:
            from distribution.install import read_archive
            unused_manifest, archived = read_archive(arguments.archive)
            if any(name in exported and exported[name] != content for name, content in archived.items()):
                raise ValueError('Different source and archive payloads require separate inspection')
            exported.update(archived)
        result = scan(arguments.root, private_rules=arguments.private_rules, exported=exported,
                      input_mode=arguments.input)
    except (OSError, ValueError, TypeError, subprocess.CalledProcessError):
        print(json.dumps({'input_mode': arguments.input, 'complete': False, 'error': 'Content inspection is blocked; check inputs privately.',
                          'publication_ready': False}))
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result['complete'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
