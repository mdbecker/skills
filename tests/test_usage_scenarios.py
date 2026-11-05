import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / 'evaluations/usage-workflows'


class UsageScenarioGovernanceTests(unittest.TestCase):
    def load(self, name):
        path = DIRECTORY / name
        self.assertTrue(path.is_file(), 'The evaluator corpus must be present as independent saved inputs')
        return json.loads(path.read_text())

    def test_raw_cases_and_criteria_are_separate_and_frozen(self):
        corpus = self.load('cases.json')
        expected = self.load('expected.json')
        freeze = self.load('freeze.json')
        self.assertTrue(corpus['synthetic_only'])
        self.assertTrue(expected['evaluator_only'])
        self.assertEqual({case['id'] for case in corpus['cases']}, set(expected['cases']))
        for case in corpus['cases']:
            self.assertEqual(set(case), {'id', 'request', 'context', 'artifacts'})
            self.assertNotIn('expected', case)
            for relative, content in case['artifacts'].items():
                path = Path(relative)
                self.assertFalse(path.is_absolute())
                self.assertNotIn('..', path.parts)
                self.assertIsInstance(content, str)
                if relative.endswith('.json'):
                    json.loads(content)
        for relative, checksum in freeze['corpus_hashes'].items():
            path = DIRECTORY / relative
            self.assertTrue(path.resolve().is_relative_to(DIRECTORY.resolve()))
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), checksum)
        self.assertEqual(freeze['model_protocol_approval'], 'pending')

    def test_all_prd_requirements_have_sources_and_independent_criteria(self):
        traceability = self.load('traceability.json')
        cases = {case['id'] for case in self.load('cases.json')['cases']}
        expected = self.load('expected.json')['cases']
        self.assertEqual({entry['id'] for entry in traceability['requirements']},
                         {'U' + str(number).zfill(2) for number in range(1, 15)})
        for entry in traceability['requirements']:
            self.assertTrue(entry['sources'])
            self.assertTrue(set(entry['cases']).issubset(cases))
            for relative in entry['sources']:
                self.assertTrue((ROOT / relative).is_file(), relative)
            for identity in entry['cases']:
                self.assertTrue(expected[identity]['required_observations'])
                self.assertTrue(expected[identity]['forbidden_actions'])

    def test_unperformed_assistant_and_user_checks_are_not_passing_results(self):
        results = self.load('results.json')
        self.assertEqual(results['assistant_routing'], 'not_run')
        self.assertEqual(results['human_comprehension'], 'not_run')
        self.assertEqual(results['live_host_invocation'], 'not_run')
        self.assertEqual(results['model_protocol_approval'], 'pending')
        self.assertIsNone(results['model_tokens'])
        self.assertIsNone(results['provider_cost'])
        self.assertFalse(results['behavioral_quality_acceptance'])


if __name__ == '__main__':
    unittest.main()
