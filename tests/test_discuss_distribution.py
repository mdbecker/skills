import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest
import zipfile

from distribution.install import HOST_DIRS, install
from scripts.build_skills import ROOT, build, payload


DIRECTORY = ROOT / 'evaluations/review/discuss-ballots'


class DiscussDistributionTests(unittest.TestCase):
    def test_evaluation_inputs_have_matching_frozen_identities(self):
        self.assert_frozen_corpus(DIRECTORY)

    def assert_frozen_corpus(self, directory):
        freeze = json.loads((directory / 'freeze.json').read_text())
        required = {'cases.json', 'expected.json', 'baseline.json'}
        self.assertTrue(required.issubset(freeze['corpus_hashes']))
        for relative, checksum in freeze['corpus_hashes'].items():
            source = directory / relative
            self.assertTrue(source.resolve().is_relative_to(directory.resolve()))
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), checksum)

        corpus = json.loads((directory / 'cases.json').read_text())
        criteria = json.loads((directory / 'expected.json').read_text())
        self.assertEqual(corpus['schema_version'], freeze['schema_version'])
        self.assertEqual(criteria['schema_version'], freeze['schema_version'])
        identifiers = [case['id'] for case in corpus['cases']]
        self.assertEqual(len(identifiers), len(set(identifiers)))
        self.assertEqual(set(identifiers), set(criteria['cases']))
        self.assertEqual(set(identifiers), set(freeze['case_ids']))
        self.assertTrue(corpus['synthetic_only'])
        self.assertTrue(criteria['evaluator_only'])
        for case in corpus['cases']:
            for relative, content in case['artifacts'].items():
                path = Path(relative)
                self.assertFalse(path.is_absolute())
                self.assertNotIn('..', path.parts)
                self.assertIsInstance(content, str)
                if path.suffix == '.json':
                    json.loads(content)

        baseline = json.loads((directory / 'baseline.json').read_text())
        identity = hashlib.sha256(json.dumps(baseline['source_inputs'], sort_keys=True).encode()).hexdigest()
        self.assertEqual(identity, baseline['source_inputs_sha256'])

    def test_missing_required_freeze_entries_are_rejected(self):
        for missing in ('cases.json', 'expected.json', 'baseline.json'):
            with self.subTest(missing=missing):
                with tempfile.TemporaryDirectory() as temporary:
                    directory = Path(temporary)
                    for relative in ('freeze.json', 'cases.json', 'expected.json', 'baseline.json'):
                        shutil.copyfile(DIRECTORY / relative, directory / relative)
                    freeze = json.loads((directory / 'freeze.json').read_text())
                    del freeze['corpus_hashes'][missing]
                    (directory / 'freeze.json').write_text(json.dumps(freeze))
                    changed = json.loads((directory / missing).read_text())
                    changed['mutation'] = True
                    (directory / missing).write_text(json.dumps(changed))
                    with self.assertRaises(AssertionError):
                        self.assert_frozen_corpus(directory)

    def test_review_installs_complete_without_evaluator_material_on_both_hosts(self):
        unused_inventory, exported, inputs = payload(ROOT)
        self.assertFalse(any(Path(relative).parts[0] == 'evaluations' for relative in inputs))
        prefix = 'skills/review/'
        expected = {relative[len(prefix):]: content for relative, content in exported.items()
                    if relative.startswith(prefix)}
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            archive = workspace / 'skills.zip'
            build(archive, 'discuss-distribution-test')
            with zipfile.ZipFile(archive) as bundle:
                self.assertFalse(any('evaluations' in Path(relative).parts for relative in bundle.namelist()))
            for host, location in HOST_DIRS.items():
                with self.subTest(host=host):
                    project = workspace / host
                    project.mkdir()
                    result = install(archive, project, host=host, selected=['review'])
                    self.assertEqual(result['installed'], ['review'])
                    directory = project / location / 'review'
                    actual = {source.relative_to(directory).as_posix(): source.read_bytes()
                              for source in directory.rglob('*') if source.is_file()}
                    self.assertEqual(actual, expected)
                    siblings = {source.name for source in directory.parent.iterdir() if source.is_dir()}
                    self.assertEqual(siblings, {'review'})
                    repeated = install(archive, project, host=host, selected=['review'])
                    self.assertEqual(repeated['installed'], [])
                    self.assertEqual(repeated['unchanged'], ['review'])


if __name__ == '__main__':
    unittest.main()
