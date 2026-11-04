import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

import yaml

from distribution import install as installer
from scripts.build_skills import ROOT, build, payload, prepare


class MetadataContractTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.workspace = Path(self.temporary.name)
        self.source = self.workspace / 'source'
        self.source.mkdir()
        inventory, unused_files, inputs = payload(ROOT)
        for relative in inputs:
            target = self.source / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((ROOT / relative).read_bytes())
        status = self.source / 'evaluations/status.json'
        status.parent.mkdir(parents=True, exist_ok=True)
        status.write_bytes((ROOT / 'evaluations/status.json').read_bytes())
        discovery = self.source / '.agents/skills'
        discovery.mkdir(parents=True)
        for name in inventory['parents']:
            (discovery / name).symlink_to(self.source / name, target_is_directory=True)
        prepare(self.source)
        self.archive = self.workspace / 'skills.zip'
        spec = importlib.util.spec_from_file_location('metadata_authoring_validator', ROOT / 'scripts/validate_skills.py')
        self.validator = importlib.util.module_from_spec(spec)
        with patch.object(sys, 'path', [str(ROOT / 'scripts'), *sys.path]):
            spec.loader.exec_module(self.validator)

    def document(self, fields):
        return ('---\n' + fields + '\n---\n\n# Synthetic skill\n').encode()

    def set_metadata(self, fields):
        content = self.document(fields)
        (self.source / 'develop/SKILL.md').write_bytes(content)
        return content

    def source_identity(self, command, **kwargs):
        output = '1' * 40 + '\n' if command == ['git', 'rev-parse', 'HEAD'] else ' M develop/SKILL.md\n'
        return subprocess.CompletedProcess(command, 0, stdout=output)

    def build_archive(self):
        with patch('scripts.build_skills.subprocess.run', side_effect=self.source_identity):
            return build(self.archive, 'metadata-test', root=self.source)

    def validate_authoring(self):
        errors = io.StringIO()
        with patch.object(self.validator, 'ROOT', self.source), contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(errors):
            result = self.validator.main()
        return result, errors.getvalue()

    def rewritten_archive(self, fields):
        self.build_archive()
        with zipfile.ZipFile(self.archive) as archive:
            contents = {name: archive.read(name) for name in archive.namelist()}
        contents['skills/develop/SKILL.md'] = self.document(fields)
        manifest = json.loads(contents['manifest.json'])
        manifest['files'] = {name: hashlib.sha256(content).hexdigest() for name, content in contents.items()
                             if name != 'manifest.json'}
        contents['manifest.json'] = json.dumps(manifest).encode()
        target = self.workspace / 'rewritten.zip'
        with zipfile.ZipFile(target, 'w') as archive:
            for name, content in contents.items():
                archive.writestr(name, content)
        return target

    def test_inline_comments_roundtrip_through_authoring_export_and_installation(self):
        expected = self.set_metadata('name: develop # ordinary inline comment\ndescription: Keep source bytes # comment')
        result, errors = self.validate_authoring()
        self.assertEqual(result, 0, errors)
        self.build_archive()
        try:
            installer.read_archive(self.archive)
        except ValueError as error:
            self.fail(f'Authoring-accepted metadata was rejected by installation: {error}')
        project = self.workspace / 'project'
        project.mkdir()
        self.assertEqual(installer.install(self.archive, project, selected=['develop'])['installed'], ['develop'])
        self.assertEqual((project / '.agents/skills/develop/SKILL.md').read_bytes(), expected)

    def test_supported_scalar_semantics_match_yaml_and_preserve_source_bytes(self):
        fields = [
            'name: "develop" # comment\ndescription: "Keep # symbols" # outside',
            "name: 'develop'\ndescription: 'It''s literal # content'",
            'name: develop\ndescription: "Unicode \\u03bb and \\nline"',
            'name: develop\ndescription: |\n  First line\n  Second line',
            'name: develop\ndescription: |-\n  First line\n\n  Second paragraph',
            'name: develop\ndescription: >\n  First line\n  continues\n\n  Second paragraph',
            'name: develop\ndescription: >-\n  First line\n  continues',
            'name: develop\nmetadata:\n  label: ordinary\n  name: nested\ndescription: Top-level description',
            'name: develop\ndescription: 1e3',
            'name: develop\ndescription: 12:99',
            'name: develop\ndescription: 0o12',
            'name: develop\ndescription: YeS',
        ]
        parser = getattr(installer, 'parse_skill_metadata', None)
        self.assertTrue(callable(parser), 'A shared portable metadata contract is required')
        for header in fields:
            for crlf in [False, True]:
                with self.subTest(header=header, crlf=crlf):
                    content = self.document(header)
                    if crlf:
                        content = content.replace(b'\n', b'\r\n')
                    (self.source / 'develop/SKILL.md').write_bytes(content)
                    expected = yaml.safe_load(header + '\n')
                    try:
                        parsed = parser(content, 'develop')
                    except ValueError as error:
                        self.fail(f'Supported YAML string was rejected: {error}')
                    self.assertEqual(parsed, {key: expected[key] for key in ['name', 'description']})
                    result, errors = self.validate_authoring()
                    self.assertEqual(result, 0, errors)
                    self.build_archive()
                    unused_manifest, files = installer.read_archive(self.archive)
                    self.assertEqual(files['skills/develop/SKILL.md'], content)

    def test_invalid_or_unsupported_metadata_cannot_replace_an_archive(self):
        self.build_archive()
        original = self.archive.read_bytes()
        checksum = self.archive.with_suffix('.zip.sha256')
        original_checksum = checksum.read_bytes()
        fields = [
            'name: develop', 'name: develop\ndescription: ""',
            'name: develop\ndescription: null', 'name: develop\ndescription: false',
            'name: develop\ndescription: 42', 'name: develop\ndescription: [one]',
            'name: develop\ndescription: {key: value}', 'name: develop\ndescription: *alias',
            'name: develop\ndescription: !tag value',
            'name: develop\ndescription: first\ndescription: second',
            'name: develop\nname: develop\ndescription: duplicate name',
            'name: develop\ndescription: >+\n  Unsupported keep chomping',
            'name: develop\ndescription: |2\n  Unsupported explicit indentation',
            'name: develop\ndescription: "Unsupported \\x41 escape"',
            'name: develop\ndescription: "multiline\n  quoted scalar"',
        ]
        for header in fields:
            with self.subTest(header=header):
                self.set_metadata(header)
                with self.assertRaises(ValueError):
                    self.build_archive()
                self.assertEqual(self.archive.read_bytes(), original)
                self.assertEqual(checksum.read_bytes(), original_checksum)
                result, unused_errors = self.validate_authoring()
                self.assertEqual(result, 1)

    def test_archive_metadata_rejects_empty_and_nonstrings(self):
        for scalar in ['""', "''", 'null', 'false', '42', '[one]', '{key: value}']:
            with self.subTest(scalar=scalar):
                target = self.rewritten_archive('name: develop\ndescription: ' + scalar)
                with self.assertRaises(ValueError):
                    installer.read_archive(target)

    def test_invalid_metadata_blocks_preparation_without_touching_outputs(self):
        before = {path.relative_to(self.source): path.read_bytes() for path in self.source.rglob('*')
                  if path.is_file() and ('resources' in path.parts or path.name == '.prepared-resources.json')}
        self.set_metadata('name: develop\ndescription: false')
        with self.assertRaises(ValueError):
            prepare(self.source)
        after = {path.relative_to(self.source): path.read_bytes() for path in self.source.rglob('*')
                 if path.is_file() and ('resources' in path.parts or path.name == '.prepared-resources.json')}
        self.assertEqual(after, before)

    def test_standalone_installer_runs_without_authoring_dependencies(self):
        self.build_archive()
        unused_manifest, files = installer.read_archive(self.archive)
        script = self.workspace / 'install.py'
        script.write_bytes(files['install.py'])
        project = self.workspace / 'standalone'
        project.mkdir()
        result = subprocess.run([sys.executable, '-I', '-S', str(script), '--archive', str(self.archive),
                                 '--project', str(project), '--host', 'codex', '--dry-run'],
                                cwd=project, text=True, capture_output=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['planned'], ['develop', 'review', 'research'])

    def test_known_legacy_archive_still_verifies(self):
        archive = ROOT / 'dist/skills-df4469e.zip'
        if not archive.is_file():
            self.skipTest('Recorded legacy archive is unavailable')
        manifest, unused_files = installer.read_archive(archive)
        self.assertEqual(manifest['schema_version'], 1)
        self.assertEqual([entry['name'] for entry in manifest['skills']],
                         ['develop', 'review', 'research', 'iterate', 'debate'])

    def test_portable_json_rejects_nonfinite_numbers(self):
        for number in ['NaN', 'Infinity', '-Infinity', '1e999']:
            with self.subTest(number=number):
                with self.assertRaises(ValueError):
                    installer.parse_json('{"number":' + number + '}')
