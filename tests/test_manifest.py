import importlib.util
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / 'develop/scripts/manifest.py'


class ManifestTests(unittest.TestCase):
    def run_cli(self, directory, *args, succeeds=True):
        result = subprocess.run([sys.executable, str(SCRIPT), *args], cwd=directory,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode == 0, succeeds, result.stderr)
        return result

    def test_replacing_commands_preserves_restart_order(self):
        with tempfile.TemporaryDirectory() as directory:
            self.run_cli(directory, 'init', 'demo', '--impact', 'Restart the environment')
            for label in ('start', 'seed', 'run'):
                self.run_cli(directory, 'testbed', 'demo', 'add', '--label', label,
                             '--cmd', label + '-v1')
            for label in ('start', 'seed', 'run', 'start'):
                self.run_cli(directory, 'testbed', 'demo', 'add', '--label', label,
                             '--cmd', label + '-v2')
                output = self.run_cli(directory, 'testbed', 'demo', 'list').stdout
                self.assertEqual([line.split(']')[0] for line in output.splitlines()],
                                 ['[start', '[seed', '[run'])
            self.assertEqual(output.splitlines(),
                             ['[start] start-v2', '[seed] seed-v2', '[run] run-v2'])
            self.run_cli(directory, 'testbed', 'demo', 'add', '--label', 'stop', '--cmd', 'stop')
            self.assertEqual(self.run_cli(directory, 'testbed', 'demo', 'list').stdout.splitlines(),
                             output.splitlines() + ['[stop] stop'])

    def test_replacement_collapses_legacy_duplicates_at_first_position(self):
        with tempfile.TemporaryDirectory() as directory:
            self.run_cli(directory, 'init', 'demo', '--impact', 'Resume legacy state')
            path = Path(directory, '.ai-state/demo.json')
            fixture = json.loads(path.read_text())
            fixture['implementation_state']['test_bed_commands'] = [
                {'label': 'start', 'command': 'old'},
                {'label': 'seed', 'command': 'seed'},
                {'label': 'start', 'command': 'older duplicate'},
            ]
            path.write_text(json.dumps(fixture))
            self.run_cli(directory, 'testbed', 'demo', 'add', '--label', 'start', '--cmd', 'new')
            self.assertEqual(self.run_cli(directory, 'testbed', 'demo', 'list').stdout.splitlines(),
                             ['[start] new', '[seed] seed'])

    def test_state_directory_symlink_is_rejected_without_writes(self):
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as outside:
            marker = Path(outside, 'keep.txt')
            marker.write_text('unchanged')
            Path(directory, '.ai-state').symlink_to(outside, target_is_directory=True)
            for arguments in [('init', 'demo', '--impact', 'demo'), ('list',), ('status',)]:
                result = self.run_cli(directory, *arguments, succeeds=False)
                self.assertIn('not a symlink', result.stderr)
            self.assertEqual(list(Path(outside).iterdir()), [marker])
            self.assertEqual(marker.read_text(), 'unchanged')

    def test_manifest_symlinks_are_rejected_without_changing_target(self):
        with tempfile.TemporaryDirectory() as directory:
            self.run_cli(directory, 'init', 'real', '--impact', 'Existing feature')
            target = Path(directory, '.ai-state/real.json')
            original = target.read_bytes()
            alias = Path(directory, '.ai-state/alias.json')
            alias.symlink_to(target)
            for arguments in [('status', 'alias'), ('set', 'alias', 'impact', 'changed')]:
                result = self.run_cli(directory, *arguments, succeeds=False)
                self.assertIn('not symlinks', result.stderr)
            self.assertTrue(alias.is_symlink())
            self.assertEqual(target.read_bytes(), original)

    def test_workflow_and_editable_records(self):
        with tempfile.TemporaryDirectory() as directory:
            def run(*args, succeeds=True):
                result = subprocess.run([sys.executable, str(SCRIPT), *args], cwd=directory,
                                        capture_output=True, text=True)
                self.assertEqual(result.returncode == 0, succeeds, result.stderr)
                return result.stdout
            run('init', '../escaped', '--impact', 'demo', succeeds=False)
            self.assertFalse(Path(directory, 'escaped.json').exists())
            run('init', 'demo', '--impact', 'demo')
            for phase in ['HAPPY_PATH', 'TEST_BED', 'TWEAKING', 'TESTING', 'FINALIZATION']:
                run('phase', 'demo', phase)
            state = Path(directory, '.ai-state/demo.json')
            self.assertEqual(len(json.loads(state.read_text())['project_metadata']['phase_history']), 5)
            run('park', 'demo', 'edge', 'example')
            run('resolve', 'demo', 'edge', '1', '--waive', 'unneeded')
            run('resolve', 'demo', 'edge', '1')
            self.assertNotIn('waived:', run('status', 'demo', '-v'))
            run('testbed', 'demo', 'add', '--label', 'start', '--cmd', 'old')
            run('testbed', 'demo', 'add', '--label', 'start', '--cmd', 'new')
            self.assertEqual(run('testbed', 'demo', 'list').strip(), '[start] new')
            run('testbed', 'demo', 'remove', '--label', 'start')
            self.assertIn('no test bed commands', run('testbed', 'demo', 'list'))
            Path(directory, 'tool.py').touch()
            run('tool', 'add', '--name', 'demo', '--path', 'tool.py', '--desc', 'demo')
            run('tool', 'update', '--name', 'demo', '--usage', 'new invocation')
            self.assertIn('new invocation', run('tool', 'list'))

    def test_failed_atomic_replace_preserves_original(self):
        spec = importlib.util.spec_from_file_location('manifest', SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory, 'state.json')
            target.write_text('original')
            with patch.object(module.os, 'replace', side_effect=OSError('interrupted')):
                with self.assertRaises(OSError):
                    module.atomic_write(target, 'replacement')
            self.assertEqual(target.read_text(), 'original')
            self.assertEqual(list(Path(directory).iterdir()), [target])

    def registry_commands(self):
        return [('tool', 'list'),
                ('tool', 'add', '--name', 'new', '--path', 'tool.py', '--desc', 'new'),
                ('tool', 'update', '--name', 'existing', '--desc', 'updated')]

    def test_registry_ancestor_links_preserve_external_storage(self):
        for ancestor in ('testbed', 'testbed/tools'):
            for populated in (False, True):
                with self.subTest(ancestor=ancestor, populated=populated), tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as outside:
                    project = Path(directory)
                    external = Path(outside)
                    (project / 'tool.py').write_text('inert reference')
                    (external / 'keep.txt').write_text('unchanged')
                    registry = external / ('tools/registry.json' if ancestor == 'testbed' else 'registry.json')
                    if populated:
                        registry.parent.mkdir(parents=True, exist_ok=True)
                        registry.write_text('[{"name":"existing","path":"tool.py","description":"external sentinel"}]')
                    before = {entry.relative_to(external): entry.read_bytes() for entry in external.rglob('*') if entry.is_file()}
                    link = project / ancestor
                    link.parent.mkdir(parents=True, exist_ok=True)
                    link.symlink_to(external, target_is_directory=True)
                    for command in self.registry_commands():
                        result = self.run_cli(project, *command, succeeds=False)
                        self.assertIn('unsafe registry storage', result.stderr)
                        self.assertNotIn('Traceback', result.stderr)
                        self.assertNotIn('external sentinel', result.stdout)
                        self.assertTrue(link.is_symlink())
                        after = {entry.relative_to(external): entry.read_bytes() for entry in external.rglob('*') if entry.is_file()}
                        self.assertEqual(before, after)

    def test_registry_leaf_links_preserve_links_and_targets(self):
        for placement in ('external', 'inside', 'broken'):
            with self.subTest(placement=placement), tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as outside:
                project = Path(directory)
                (project / 'tool.py').write_text('inert reference')
                target = (project if placement == 'inside' else Path(outside)) / 'saved-registry.json'
                if placement != 'broken':
                    target.write_text('[{"name":"existing","path":"tool.py","description":"private sentinel"}]')
                before = target.read_bytes() if target.exists() else None
                link = project / 'testbed/tools/registry.json'
                link.parent.mkdir(parents=True)
                link.symlink_to(target)
                for command in self.registry_commands():
                    result = self.run_cli(project, *command, succeeds=False)
                    self.assertIn('unsafe registry storage', result.stderr)
                    self.assertNotIn('private sentinel', result.stdout)
                    self.assertTrue(link.is_symlink())
                    self.assertEqual(target.read_bytes() if target.exists() else None, before)

    def test_registry_invalid_components_and_inside_ancestor_link(self):
        for placement in ('testbed-file', 'tools-file', 'registry-directory', 'inside-link'):
            with self.subTest(placement=placement), tempfile.TemporaryDirectory() as directory:
                project = Path(directory)
                (project / 'tool.py').write_text('inert reference')
                if placement == 'testbed-file':
                    occupied = project / 'testbed'
                    occupied.write_text('keep')
                elif placement == 'tools-file':
                    (project / 'testbed').mkdir()
                    occupied = project / 'testbed/tools'
                    occupied.write_text('keep')
                elif placement == 'registry-directory':
                    occupied = project / 'testbed/tools/registry.json'
                    occupied.mkdir(parents=True)
                else:
                    occupied = project / 'shared-tools'
                    occupied.mkdir()
                    (occupied / 'keep.txt').write_text('keep')
                    (project / 'testbed').mkdir()
                    (project / 'testbed/tools').symlink_to(occupied, target_is_directory=True)
                for command in self.registry_commands():
                    result = self.run_cli(project, *command, succeeds=False)
                    self.assertIn('unsafe registry storage', result.stderr)
                    self.assertNotIn('Traceback', result.stderr)
                if placement in ('testbed-file', 'tools-file'):
                    self.assertEqual(occupied.read_text(), 'keep')
                if placement == 'inside-link':
                    self.assertEqual((occupied / 'keep.txt').read_text(), 'keep')
                    self.assertFalse((occupied / 'registry.json').exists())

    def test_local_registry_preserves_explicit_external_references(self):
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as outside:
            project = Path(directory)
            reference = Path(outside) / 'tool.py'
            reference.write_text('raise RuntimeError("must never execute")\n')
            before = reference.read_bytes()
            self.run_cli(project, 'tool', 'list')
            self.assertFalse((project / 'testbed').exists())
            self.run_cli(project, 'tool', 'update', '--name', 'missing', '--desc', 'missing', succeeds=False)
            self.assertFalse((project / 'testbed').exists())
            self.run_cli(project, 'tool', 'add', '--name', 'external', '--path', str(reference), '--desc', 'reference')
            self.run_cli(project, 'tool', 'update', '--name', 'external', '--usage', 'stored, not executed')
            result = self.run_cli(project, 'tool', 'list')
            self.assertIn(str(reference), result.stdout)
            self.assertIn('stored, not executed', result.stdout)
            self.assertEqual(reference.read_bytes(), before)
            self.assertTrue((project / 'testbed/tools/registry.json').is_file())

    def test_missing_key_guidance_preserves_state_and_user_restoration(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            self.run_cli(project, 'init', 'demo', '--impact', 'preserve state')
            state = project / '.ai-state/demo.json'
            valid = state.read_bytes()
            damaged = json.loads(valid)
            del damaged['architecture_decisions']
            state.write_text(json.dumps(damaged))
            before = state.read_bytes()
            for command in [('status', 'demo'), ('set', 'demo', 'impact', 'changed')]:
                result = self.run_cli(project, *command, succeeds=False)
                self.assertIn('architecture_decisions', result.stderr)
                self.assertIn('stop and preserve', result.stderr)
                self.assertIn('restore a known-good local copy', result.stderr)
                self.assertNotIn('fix by hand', result.stderr)
                self.assertEqual(state.read_bytes(), before)
            self.run_cli(project, 'init', 'demo', '--impact', 'replacement', succeeds=False)
            self.assertEqual(state.read_bytes(), before)
            state.write_text('{')
            self.run_cli(project, 'status', 'demo', succeeds=False)
            self.run_cli(project, 'set', 'demo', 'impact', 'changed', succeeds=False)
            self.assertEqual(state.read_text(), '{')
            state.write_bytes(valid)
            self.run_cli(project, 'status', 'demo')


class ManifestValidationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.project = Path(self.temporary.name)
        completed = self.run_cli('init', 'probe', '--impact', 'Preserve malformed state')
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.state = self.project / '.ai-state/probe.json'
        self.valid = json.loads(self.state.read_text())

    def run_cli(self, *arguments):
        return subprocess.run([sys.executable, '-B', str(SCRIPT), *arguments], cwd=self.project,
                              text=True, capture_output=True, timeout=10)

    def assert_rejected_without_writes(self, content, field):
        for command in [('set', 'probe', 'next_step', 'Continue'),
                        ('phase', 'probe', 'TWEAKING'),
                        ('park', 'probe', 'edge', 'Concern'),
                        ('decision', 'probe', '--title', 'Choice', '--context', 'Saved context', '--option', 'Keep',
                         '--decision', 'Keep', '--rationale', 'Preserve behavior')]:
            with self.subTest(command=command):
                self.state.write_text(content)
                original = self.state.read_bytes()
                completed = self.run_cli(*command)
                self.assertEqual(completed.returncode, 1, completed.stdout + completed.stderr)
                self.assertEqual(self.state.read_bytes(), original)
                self.assertIn(field, completed.stderr)
                self.assertIn('stop and preserve', completed.stderr)
                self.assertIn('restore a known-good local copy', completed.stderr)
                self.assertNotIn('Traceback', completed.stderr)

    def test_malformed_required_sections_cannot_be_rewritten(self):
        for section in ['project_metadata', 'core_objective', 'implementation_state',
                        'deferred_backlog', 'testing_strategy', 'architecture_decisions']:
            with self.subTest(section=section):
                malformed = deepcopy(self.valid)
                malformed[section] = None
                self.assert_rejected_without_writes(json.dumps(malformed), section)

    def test_nested_fields_and_every_list_entry_are_validated(self):
        cases = [
            ('core_objective', 'impact_target', None, 'core_objective.impact_target'),
            ('core_objective', 'strict_scope_exclusions', ['valid', 2], 'strict_scope_exclusions[1]'),
            ('implementation_state', 'test_bed_commands', [{'label': 'start', 'command': 'run'},
                                                         {'label': 'bad'}], 'test_bed_commands[1].command'),
            ('deferred_backlog', 'edge_cases', [{'description': 'valid', 'is_resolved': False},
                                             {'description': 'bad', 'is_resolved': 'false'}], 'edge_cases[1].is_resolved'),
            ('project_metadata', 'phase_history', [{'from': 'ARCHITECTURE', 'to': 'UNKNOWN',
                                                  'at': 'saved'}], 'phase_history[0].to'),
            ('testing_strategy', 'required_integration_assertions', [False], 'required_integration_assertions[0]'),
        ]
        for section, key, value, field in cases:
            with self.subTest(field=field):
                malformed = deepcopy(self.valid)
                malformed[section][key] = value
                self.assert_rejected_without_writes(json.dumps(malformed), field)
        malformed = deepcopy(self.valid)
        del malformed['core_objective']['impact_target']
        self.assert_rejected_without_writes(json.dumps(malformed), 'core_objective.impact_target')

    def test_decision_ids_reject_boolean_and_nonpositive_values(self):
        decision = {'id': 1, 'title': '', 'context': '', 'options_considered': [],
                    'decision_made': '', 'rationale': ''}
        for identity in [True, 0, -1, '1']:
            malformed = deepcopy(self.valid)
            malformed['architecture_decisions'] = [decision, dict(decision, id=identity)]
            self.assert_rejected_without_writes(json.dumps(malformed), 'architecture_decisions[1].id')

    def test_duplicate_json_keys_and_invalid_roots_preserve_bytes(self):
        duplicated = json.dumps(self.valid)[:-1] + ', "core_objective": {"impact_target": "duplicate"}}'
        self.assert_rejected_without_writes(duplicated, 'core_objective')
        for content in ['null', '[]', '42', '{']:
            self.assert_rejected_without_writes(content, 'manifest')

    def test_private_invalid_values_are_not_echoed(self):
        malformed = deepcopy(self.valid)
        malformed['project_metadata']['current_phase'] = 'private-invalid-phase-sentinel'
        self.state.write_text(json.dumps(malformed))
        completed = self.run_cli('status', 'probe')
        self.assertEqual(completed.returncode, 1)
        self.assertNotIn('private-invalid-phase-sentinel', completed.stdout + completed.stderr)
        self.assertIn('project_metadata.current_phase', completed.stderr)

    def test_optional_omissions_and_extra_fields_are_not_backfilled_by_reads(self):
        self.valid['project_metadata'].pop('next_step')
        self.valid['project_metadata'].pop('phase_history')
        self.valid['implementation_state'].pop('test_bed_commands')
        self.valid['extension'] = {'future': ['saved', None]}
        self.state.write_text(json.dumps(self.valid))
        original = self.state.read_bytes()
        for command in [('status', 'probe'), ('testbed', 'probe', 'list'), ('render', 'probe')]:
            completed = self.run_cli(*command)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(self.state.read_bytes(), original)
        self.assertEqual(self.run_cli('set', 'probe', 'next_step', 'Continue').returncode, 0)
        updated = json.loads(self.state.read_text())
        self.assertEqual(updated['extension'], self.valid['extension'])
        self.assertNotIn('phase_history', updated['project_metadata'])

    def test_save_rejects_invalid_values_before_timestamp_or_file_mutation(self):
        spec = importlib.util.spec_from_file_location('state_validation_probe', SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        malformed = deepcopy(self.valid)
        malformed['core_objective'] = None
        original = self.state.read_bytes()
        before = deepcopy(malformed)
        with patch.object(module, 'STATE_DIR', self.project / '.ai-state'):
            with self.assertRaises(SystemExit):
                module.save('probe', malformed)
        self.assertEqual(malformed, before)
        self.assertEqual(self.state.read_bytes(), original)

    def test_save_does_not_normalize_non_json_extension_values(self):
        spec = importlib.util.spec_from_file_location('state_extension_probe', SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        for extension in [('not', 'a JSON array'), {1: 'not a JSON key'}, {'not a JSON value'}]:
            with self.subTest(extension=extension):
                malformed = deepcopy(self.valid)
                malformed['extension'] = extension
                before = deepcopy(malformed)
                original = self.state.read_bytes()
                with patch.object(module, 'STATE_DIR', self.project / '.ai-state'):
                    with self.assertRaises(SystemExit):
                        module.save('probe', malformed)
                self.assertEqual(malformed, before)
                self.assertEqual(self.state.read_bytes(), original)
