import hashlib
import json
from pathlib import Path
import re
import tempfile
import unittest
import zipfile

from distribution.install import HOST_DIRS, install
from scripts.build_skills import ROOT, build


class CombinationDocumentationTests(unittest.TestCase):
    def test_each_package_alone_has_identical_guide_and_local_references(self):
        names = json.loads((ROOT / 'inventory.json').read_text())
        guide = (ROOT / 'resources/combinations.md').read_bytes()
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            archive = workspace / 'skills.zip'
            build(archive, 'combination-test')
            for host in HOST_DIRS:
                for name in names['parents'] + names['compatibility']:
                    with self.subTest(host=host, package=name):
                        project = workspace / host / name
                        project.mkdir(parents=True)
                        install(archive, project, host=host, selected=[name])
                        directory = project / HOST_DIRS[host] / name
                        installed_guide = directory / 'resources/combinations.md'
                        self.assertEqual(installed_guide.read_bytes(), guide)
                        entries = {entry.name for entry in directory.parent.iterdir() if entry.is_dir()}
                        self.assertEqual(entries, {name})
                        anchors = set(re.findall(r'<a id="([^"]+)"', guide.decode()))
                        self.assertEqual(anchors, {'c01', 'c02', 'c03', 'c04', 'c05'})
                        for target in re.findall(r'\]\(([^)]+)\)', guide.decode()):
                            reference, separator, fragment = target.partition('#')
                            resolved = (installed_guide.parent / reference).resolve() if reference else installed_guide.resolve()
                            self.assertTrue(resolved.is_relative_to(directory.resolve()), target)
                            self.assertTrue(resolved.is_file(), target)
                            if separator:
                                self.assertIn(fragment, anchors)
                        entrypoint = (directory / 'SKILL.md').read_text()
                        self.assertIn('resources/combinations.md', entrypoint)
                        if name == 'develop':
                            method = (directory / 'resources/iterate/method.md').read_text()
                            self.assertIn('](../combinations.md)', method)
                        if name == 'review':
                            method = (directory / 'resources/debate/method.md').read_text()
                            self.assertIn('](../combinations.md)', method)
            with zipfile.ZipFile(archive) as bundle:
                self.assertFalse(any('evaluations/' in name for name in bundle.namelist()))

    def test_readme_targets_canonical_recipe_anchors(self):
        readme = (ROOT / 'README.md').read_text()
        guide = (ROOT / 'resources/combinations.md').read_text()
        for target in re.findall(r'\]\((resources/combinations\.md(?:#[^)]+)?)\)', readme):
            path, separator, fragment = target.partition('#')
            self.assertTrue((ROOT / path).is_file())
            if separator:
                self.assertIn(f'<a id="{fragment}">', guide)
        self.assertIn('### Delivery coverage: C01', readme)
        self.assertIn('### Coordinated prompt changes: C03', readme)
        self.assertNotIn('**Ready handoff:**', readme)

    def test_composition_corpus_is_frozen_and_expected_routes_are_private(self):
        freeze = json.loads((ROOT / 'evaluations/combinations-freeze.json').read_text())
        fixtures = json.loads((ROOT / 'evaluations/fixtures.json').read_text())
        expected = json.loads((ROOT / 'evaluations/expected.json').read_text())
        artifacts = json.loads((ROOT / 'evaluations/artifacts.json').read_text())
        actual = {case['id']: case for case in fixtures['cases']}
        self.assertEqual(len(freeze['case_ids']), 14)
        for identity in freeze['case_ids']:
            self.assertIn(identity, actual)
            self.assertIn(identity, artifacts['cases'])
            self.assertNotIn('acceptable_routes', actual[identity])
            criteria = expected['cases'][identity]
            self.assertTrue(criteria['acceptable_routes'])
            self.assertTrue(criteria['required_facts_and_artifacts'])
            self.assertTrue(criteria['forbidden_actions'])
            self.assertTrue(criteria['stop_behavior'])
        for name, checksum in freeze['corpus_hashes'].items():
            self.assertEqual(hashlib.sha256((ROOT / 'evaluations' / name).read_bytes()).hexdigest(), checksum)
        self.assertEqual(freeze['model_protocol_approval'], 'pending')
        self.assertTrue(expected['evaluator_only'])
