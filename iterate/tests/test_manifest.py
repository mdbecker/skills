import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / 'manifest.py'


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
