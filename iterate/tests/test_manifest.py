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
