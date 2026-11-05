import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

from distribution.install import HOST_DIRS, install
from scripts.build_skills import ROOT, build


class UsageBundleTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.workspace = Path(self.temporary.name)
        self.archive = self.workspace / 'skills.zip'
        build(self.archive, 'usage-contract')

    def test_each_parent_installation_contains_the_shared_usage_reference(self):
        for host, directory in HOST_DIRS.items():
            for name in ['develop', 'review', 'research']:
                with self.subTest(host=host, skill=name):
                    project = self.workspace / host / name
                    project.mkdir(parents=True)
                    install(self.archive, project, host=host, selected=[name])
                    skill = project / directory / name
                    guide = skill / 'resources/usage.md'
                    self.assertTrue(guide.is_file(), 'A standalone skill must include its usage contract')
                    self.assertEqual(guide.read_bytes(), (ROOT / 'resources/usage.md').read_bytes())
                    self.assertIn('resources/usage.md', (skill / 'SKILL.md').read_text())
                    for target in re.findall(r'\]\(([^)]+)\)', guide.read_text()):
                        if '://' in target or target.startswith('#'):
                            continue
                        resolved = (guide.parent / target.split('#', 1)[0]).resolve()
                        self.assertTrue(resolved.is_relative_to(skill.resolve()), target)
                        self.assertTrue(resolved.is_file(), target)
                    self.assertEqual({path.name for path in skill.parent.iterdir() if path.is_dir()}, {name})
                    self.assertFalse((project / '.ai-state').exists())

    def helper(self, project, *arguments):
        script = project / '.agents/skills/develop/scripts/manifest.py'
        return subprocess.run([sys.executable, '-B', str(script), *arguments], cwd=project,
                              text=True, capture_output=True, timeout=15)

    def test_readonly_installed_helper_commands_do_not_create_state(self):
        project = self.workspace / 'readonly'
        project.mkdir()
        install(self.archive, project, selected=['develop'])
        for arguments, status in [(('--help',), 0), (('status',), 1), (('list',), 1)]:
            with self.subTest(arguments=arguments):
                result = self.helper(project, *arguments)
                self.assertEqual(result.returncode, status, result.stderr)
                self.assertFalse((project / '.ai-state').exists())
                self.assertFalse((project / '.gitignore').exists())
                self.assertFalse((project / 'testbed').exists())

    def test_explicit_helper_targets_ignore_recency_and_action_like_names(self):
        project = self.workspace / 'targets'
        project.mkdir()
        install(self.archive, project, selected=['develop'])
        for identity in ['status', 'stock']:
            result = self.helper(project, 'init', identity, '--impact', 'Synthetic existing feature')
            self.assertEqual(result.returncode, 0, result.stderr)
        selected = project / '.ai-state/status.json'
        other = project / '.ai-state/stock.json'
        os.utime(selected, (1, 1))
        os.utime(other, (2, 2))
        original_selected = selected.read_bytes()
        original_other = other.read_bytes()
        result = self.helper(project, 'status', 'status', '-v')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('feature:      status', result.stdout)
        self.assertEqual(selected.read_bytes(), original_selected)
        self.assertEqual(other.read_bytes(), original_other)
        result = self.helper(project, 'park', 'status', 'edge', 'Optional progress display later')
        self.assertEqual(result.returncode, 0, result.stderr)
        state = json.loads(selected.read_text())
        self.assertEqual(state['deferred_backlog']['edge_cases'][-1]['description'], 'Optional progress display later')
        self.assertEqual(other.read_bytes(), original_other)
        result = self.helper(project, 'phase', 'status', 'TWEAKING')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(selected.read_text())['project_metadata']['current_phase'], 'TWEAKING')
        self.assertEqual(other.read_bytes(), original_other)

    def test_status_displays_a_readable_stage_without_changing_stored_phase(self):
        project = self.workspace / 'stage'
        project.mkdir()
        install(self.archive, project, selected=['develop'])
        self.assertEqual(self.helper(project, 'init', 'example', '--impact', 'Readable stage').returncode, 0)
        self.assertEqual(self.helper(project, 'phase', 'example', 'TWEAKING').returncode, 0)
        state = project / '.ai-state/example.json'
        original = state.read_bytes()
        result = self.helper(project, 'status', 'example')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertRegex(result.stdout, r'(?m)^stage:\s+Refine with feedback$')
        self.assertEqual(json.loads(state.read_text())['project_metadata']['current_phase'], 'TWEAKING')
        self.assertEqual(state.read_bytes(), original)

    def test_implicit_status_discloses_recency_without_writing(self):
        project = self.workspace / 'selection'
        project.mkdir()
        install(self.archive, project, selected=['develop'])
        for identity in ['older', 'newer']:
            self.assertEqual(self.helper(project, 'init', identity, '--impact', 'Source selection').returncode, 0)
        older = project / '.ai-state/older.json'
        newer = project / '.ai-state/newer.json'
        os.utime(older, (1, 1))
        os.utime(newer, (2, 2))
        original = {path.name: path.read_bytes() for path in [older, newer]}
        result = self.helper(project, 'status', '-v')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('feature:      newer', result.stdout)
        self.assertRegex(result.stdout, r'(?m)^selection:.*modification time')
        self.assertEqual({path.name: path.read_bytes() for path in [older, newer]}, original)


if __name__ == '__main__':
    unittest.main()
