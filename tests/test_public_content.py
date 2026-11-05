import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from scripts.build_skills import ROOT, build, payload, prepare, release_ready
from scripts import validate_skills


SCANNER = ROOT / 'scripts/check_public_content.py'


def scanner_module():
    if not SCANNER.is_file():
        raise AssertionError('The publication-content checker has not been implemented')
    spec = importlib.util.spec_from_file_location('public_content', SCANNER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PublicContentBehaviorTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / 'candidate'
        self.root.mkdir()
        self.rules = Path(self.temporary.name) / 'private-rules.json'
        self.rules.write_text(json.dumps({'rules': [
            {'id': 'sample-rule', 'literal': 'Sample Token'},
            {'id': 'invented-ticket', 'literal': 'PRIVATE-17'},
        ]}))

    def scan(self, paths=None, exported=None, rules=True):
        return scanner_module().scan(
            self.root, paths=paths,
            private_rules=self.rules if rules else None,
            exported=exported,
        )

    def write(self, name, content):
        target = self.root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content if isinstance(content, bytes) else content.encode())
        return target

    def test_markers_in_text_paths_and_nested_encoded_snapshots_are_rejected_without_echo(self):
        self.write('notes.md', 'Safe line\nsample token\n')
        self.write('PRIVATE-17.md', 'No subject in content')
        self.write('snapshot.json', '{"embedded":"Sample\\u0020Token","nested":{"id":"PRIVATE-17"}}')
        result = self.scan(['notes.md', 'PRIVATE-17.md', 'snapshot.json'])
        self.assertFalse(result['complete'])
        self.assertEqual({entry['path'] for entry in result['findings']},
                         {'notes.md', 'PRIVATE-17.md', 'snapshot.json'})
        self.assertTrue(any(entry.get('line') == 2 for entry in result['findings']))
        self.assertTrue(any(entry.get('representation') == 'decoded-json' for entry in result['findings']))
        for entry in result['findings']:
            self.assertNotIn('content', entry)
            self.assertNotIn('match', entry)
        self.assertNotIn('Sample Token', json.dumps(result))
        self.assertNotIn(str(self.root), json.dumps(result))

    def test_exported_copies_are_checked_not_just_source_files(self):
        self.write('guide.md', 'Generic instructions')
        result = self.scan(['guide.md'], exported={
            'skills/develop/resources/example.json': b'{"subject":"Sample Token"}'})
        self.assertFalse(result['complete'])
        self.assertEqual(result['findings'][0]['scope'], 'export')

    def test_ordinary_safe_content_passes_without_claiming_publication_acceptance(self):
        self.write('guide.md', 'Use the project-approved identity and timestamp contract.')
        result = self.scan(['guide.md'])
        self.assertTrue(result['complete'])
        self.assertEqual(result['findings'], [])
        self.assertEqual(result['private_markers'], 'passed')
        self.assertEqual(result['semantic_review'], 'not_run')
        self.assertEqual(result['history_review'], 'not_run')
        self.assertFalse(result['publication_ready'])

    def test_missing_private_rules_is_explicit_not_an_all_clear(self):
        self.write('guide.md', 'Generic')
        result = self.scan(['guide.md'], rules=False)
        self.assertTrue(result['complete'])
        self.assertEqual(result['private_markers'], 'not_run')
        self.assertFalse(result['publication_ready'])

    def test_private_rules_inside_candidate_or_invalid_rules_are_rejected(self):
        inside = self.write('private-rules.json', self.rules.read_bytes())
        with self.assertRaises(ValueError):
            scanner_module().scan(self.root, paths=[], private_rules=inside)
        for record in [{'rules': []}, {'rules': [{'id': 'x', 'literal': ''}]},
                       {'rules': [{'id': 'x', 'literal': 'One'}, {'id': 'x', 'literal': 'Two'}]}]:
            self.rules.write_text(json.dumps(record))
            with self.assertRaises(ValueError):
                self.scan([])

    def test_traversal_binary_private_artifacts_and_escaping_links_block_acceptance(self):
        self.write('binary.bin', b'\x00\xff')
        self.write('reviews/private.md', 'Generic')
        outside = Path(self.temporary.name) / 'outside'
        outside.write_text('Do not read this')
        (self.root / 'linked').symlink_to(outside)
        result = self.scan(['../outside', 'binary.bin', 'reviews/private.md', 'linked'])
        self.assertFalse(result['complete'])
        self.assertTrue({'unsafe-path', 'uninspectable', 'private-artifact', 'unsafe-link'}
                        .issubset({entry['rule_id'] for entry in result['findings']}))

    def test_personal_paths_are_detected_in_source_and_decoded_json(self):
        self.write('guide.md', 'See ' + '/' + 'Users' + '/example/private/project')
        self.write('data.json', json.dumps({'path': '/' + 'home' + '/example/project'}))
        result = self.scan(['guide.md', 'data.json'], rules=False)
        self.assertFalse(result['complete'])
        self.assertEqual({entry['rule_id'] for entry in result['findings']}, {'personal-path'})

    def test_safe_discovery_links_are_inspected_without_following_them(self):
        self.write('develop/SKILL.md', 'Generic')
        directory = self.root / '.agents/skills'
        directory.mkdir(parents=True)
        (directory / 'develop').symlink_to('../../develop')
        result = self.scan(['.agents/skills/develop', 'develop/SKILL.md'])
        self.assertTrue(result['complete'])

    def test_working_candidate_includes_new_files_but_excludes_ignored_private_material(self):
        subprocess.run(['git', 'init', '-q', str(self.root)], check=True)
        self.write('.gitignore', 'private/\n')
        self.write('new.md', 'Sample Token')
        self.write('private/notes.md', 'Sample Token')
        paths = scanner_module().candidate_paths(self.root)
        self.assertIn('new.md', paths)
        self.assertNotIn('private/notes.md', paths)
        self.assertFalse(self.scan()['complete'])

    def test_nested_json_strings_and_duplicate_keys_cannot_hide_markers(self):
        embedded = '{"subject":"Sample\\u0020Token"}'
        self.write('nested.json', json.dumps({'artifact': embedded}))
        self.write('duplicate.json', '{"subject":"Sample\\u0020Token","subject":"safe"}')
        result = self.scan(['nested.json', 'duplicate.json'])
        self.assertFalse(result['complete'])
        self.assertEqual({entry['path'] for entry in result['findings']}, {'nested.json', 'duplicate.json'})
        self.assertIn('uninspectable-json', {entry['rule_id'] for entry in result['findings']})

    def test_cli_returns_nonzero_json_without_echoing_sensitive_text(self):
        subprocess.run(['git', 'init', '-q', str(self.root)], check=True)
        self.write('guide.md', 'Sample Token')
        result = subprocess.run([sys.executable, str(SCANNER), '--root', str(self.root),
                                 '--private-rules', str(self.rules)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertFalse(json.loads(result.stdout)['complete'])
        self.assertNotIn('Sample Token', result.stdout + result.stderr)


class IndexSelectionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / 'project'
        self.root.mkdir()
        subprocess.run(['git', 'init', '-q', str(self.root)], check=True)
        self.rules = Path(self.temporary.name) / 'rules.json'
        self.rules.write_text(json.dumps({'rules': [{'id': 'sample-rule', 'literal': 'Sample Token'}]}))

    def git(self, *arguments, content=None):
        return subprocess.run(['git', *arguments], cwd=self.root, input=content,
                              capture_output=True, check=True)

    def test_index_reads_staged_bytes_not_the_clean_working_file(self):
        source = self.root / 'guide.md'
        source.write_text('Sample Token')
        self.git('add', 'guide.md')
        source.write_text('Ordinary instructions')
        before = self.git('ls-files', '--stage', '-z').stdout
        module = scanner_module()
        working = module.scan(self.root, private_rules=self.rules)
        indexed = module.scan(self.root, private_rules=self.rules, input_mode='index')
        self.assertTrue(working['complete'])
        self.assertEqual(working['input_mode'], 'working')
        self.assertFalse(indexed['complete'])
        self.assertEqual(indexed['input_mode'], 'index')
        self.assertNotIn('Sample Token', json.dumps(indexed))
        self.assertEqual(before, self.git('ls-files', '--stage', '-z').stdout)
        self.assertEqual(source.read_text(), 'Ordinary instructions')

    def test_index_is_independent_of_a_changed_working_link(self):
        (self.root / 'target.md').write_text('Ordinary')
        (self.root / 'alias').symlink_to('target.md')
        self.git('add', 'target.md', 'alias')
        (self.root / 'alias').unlink()
        (self.root / 'alias').symlink_to('../outside')
        result = scanner_module().scan(self.root, input_mode='index')
        self.assertTrue(result['complete'])
        self.assertEqual((self.root / 'alias').readlink(), Path('../outside'))

    def test_escaping_and_cyclic_index_links_are_blocked(self):
        (self.root / 'outside').symlink_to('../escape')
        (self.root / 'first').symlink_to('second')
        (self.root / 'second').symlink_to('first')
        self.git('add', '.')
        result = scanner_module().scan(self.root, input_mode='index')
        self.assertFalse(result['complete'])
        self.assertEqual({entry['path'] for entry in result['findings']}, {'outside', 'first', 'second'})

    def test_conflicted_index_blocks_without_resolving_or_staging(self):
        identity = self.git('hash-object', '-w', '--stdin', content=b'Ordinary').stdout.decode().strip()
        entries = f'100644 {identity} 1\tguide.md\n100644 {identity} 2\tguide.md\n'
        self.git('update-index', '--index-info', content=entries.encode())
        before = self.git('ls-files', '--stage', '-z').stdout
        result = scanner_module().scan(self.root, input_mode='index')
        self.assertFalse(result['complete'])
        self.assertEqual({entry['rule_id'] for entry in result['findings']}, {'index-conflict'})
        self.assertEqual(before, self.git('ls-files', '--stage', '-z').stdout)

    def test_unknown_selected_index_path_is_blocked(self):
        result = scanner_module().scan(self.root, paths=['absent.md'], input_mode='index')
        self.assertFalse(result['complete'])
        self.assertEqual(result['findings'][0]['rule_id'], 'index-missing')

    def test_cli_identifies_the_requested_representation(self):
        (self.root / 'guide.md').write_text('Sample Token')
        self.git('add', 'guide.md')
        (self.root / 'guide.md').write_text('Ordinary')
        result = subprocess.run([sys.executable, str(SCANNER), '--root', str(self.root),
                                 '--input', 'index', '--private-rules', str(self.rules)],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(json.loads(result.stdout)['input_mode'], 'index')
        self.assertNotIn('Sample Token', result.stdout + result.stderr)


class PublicationBoundaryTests(unittest.TestCase):
    def test_existing_validator_rejects_personal_data_in_otherwise_valid_exported_instructions(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            inventory, unused_export, inputs = payload(ROOT)
            for relative in inputs:
                target = root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((ROOT / relative).read_bytes())
            prepare(root)
            for name in inventory['parents']:
                link = root / '.agents/skills' / name
                link.parent.mkdir(parents=True, exist_ok=True)
                link.symlink_to('../../' + name)
            source = root / 'develop/SKILL.md'
            source.write_text(source.read_text() + '\nLocal source: ' + '/' + 'Users' + '/example/private-project\n')
            prepare(root)
            with patch.object(validate_skills, 'ROOT', root), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(validate_skills.main(), 1,
                                 'Valid metadata must not allow personal paths into published skills')

    def test_each_standalone_package_contains_generic_context_and_factual_public_attribution(self):
        unused_inventory, exported, inputs = payload(ROOT)
        for name in ['develop', 'review', 'research']:
            self.assertIn(f'skills/{name}/resources/project-profile.md', exported)
        self.assertIn('NOTICE', exported)
        self.assertIn('LICENSE', exported)
        provenance = json.loads(exported['skills/develop/resources/provenance.json'])
        self.assertEqual(provenance['kind'], 'public_method_design_ledger')
        self.assertTrue(provenance['fictional_examples'])
        self.assertFalse(any('private-rules' in relative for relative in inputs))

    def test_instruction_snapshots_have_valid_identities_and_separate_quality(self):
        for directory in ['workflow-methods', 'usage-workflows']:
            baseline = json.loads((ROOT / 'evaluations' / directory / 'baseline.json').read_text())
            self.assertEqual(baseline['kind'], 'synthetic_public_instruction_snapshot')
            for record in baseline['sources'].values():
                self.assertEqual(hashlib.sha256(record['content'].encode()).hexdigest(), record['sha256'])
        status = json.loads((ROOT / 'evaluations/status.json').read_text())
        self.assertEqual(status['model_quality'], 'not_run')
        self.assertEqual(status['reference_fidelity'], 'not_run')
        self.assertNotEqual(status['release_approval'], 'passed')

    def test_source_history_does_not_become_publication_approval(self):
        module = scanner_module()
        result = module.scan(ROOT, paths=['NOTICE'], exported={})
        self.assertTrue(result['complete'])
        self.assertFalse(result['publication_ready'])
        self.assertEqual(result['history_review'], 'not_run')

    def test_legacy_quality_gates_cannot_bypass_publication_reviews(self):
        unused_inventory, unused_export, inputs = payload(ROOT)
        status = json.loads((ROOT / 'evaluations/status.json').read_text())
        for gate in ['release_approval', 'model_protocol_approval', 'manual_acceptance',
                     'deterministic', 'model_quality', 'reference_fidelity', 'transfer']:
            status[gate] = 'passed'
        status['hosts'] = {host: {gate: 'passed' for gate in ['installation', 'invocation', 'hierarchy']}
                           for host in ['codex', 'claude']}
        status['source_inputs_sha256'] = hashlib.sha256(json.dumps(inputs, sort_keys=True).encode()).hexdigest()
        status.pop('publication', None)
        self.assertFalse(release_ready(status, inputs),
                         'Legacy qualification is not semantic, rights or public-history approval')
        status['publication'] = {gate: 'passed' for gate in
                                 ['public_content', 'private_markers', 'semantic_review',
                                  'distribution_rights', 'history_review']}
        self.assertTrue(release_ready(status, inputs))
        for gate in status['publication']:
            status['publication'][gate] = 'not_run'
            self.assertFalse(release_ready(status, inputs))
            status['publication'][gate] = 'passed'

    def test_prerelease_cannot_bypass_private_content_or_history_review(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / 'candidate.zip'
            clean_source = [SimpleNamespace(stdout='a' * 40), SimpleNamespace(stdout='')]
            with patch('scripts.build_skills.subprocess.run', side_effect=clean_source):
                with self.assertRaisesRegex(ValueError, 'release blocked'):
                    build(output, 'v0.1.0-rc.1', release=True, prerelease=True)
            self.assertFalse(output.exists())

    def test_profile_exposes_requested_scoring_without_a_universal_agent_gate(self):
        profile = (ROOT / 'research/report-profile.md').read_text()
        for field in ['independent_scoring', 'requested', 'minimum_score', 'revision_limit',
                      'rubric', 'reviewer_permission', 'observed_score']:
            self.assertIn(field, profile)
        self.assertIn('complete agreed behavioral scenario set', (ROOT / 'develop/bdd.md').read_text())


if __name__ == '__main__':
    unittest.main()
