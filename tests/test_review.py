import ast
import json
from pathlib import Path
import tomllib
import unittest

from scripts.build_skills import ROOT, payload


class FocusedReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        directory = ROOT / "evaluations/review"
        inputs = json.loads((directory / "cases.json").read_text())
        cls.cases = {case["id"]: case for case in inputs["cases"]}
        cls.expected = json.loads((directory / "expected.json").read_text())

    def test_cases_separate_raw_inputs_from_evaluator_criteria(self):
        self.assertTrue(self.expected["evaluator_only"])
        self.assertTrue(self.expected["illustrative_not_agent_outputs"])
        self.assertEqual(set(self.cases), set(self.expected["cases"]))
        for case in self.cases.values():
            self.assertEqual(set(case), {"id", "request", "context", "artifacts"})
            for relative in case["artifacts"]:
                path = Path(relative)
                self.assertFalse(path.is_absolute())
                self.assertNotIn("..", path.parts)

    def test_dependency_gap_is_packaging_evidence_not_an_import_failure(self):
        for identity, missing in [("code-cleanroom-rereview", True),
                                  ("code-existing-consumer", False)]:
            with self.subTest(case=identity):
                artifacts = self.cases[identity]["artifacts"]
                imports = {alias.name.split(".")[0]
                           for node in ast.walk(ast.parse(artifacts["client.py"]))
                           if isinstance(node, ast.Import) for alias in node.names}
                dependencies = set(tomllib.loads(artifacts["pyproject.toml"])["project"]["dependencies"])
                self.assertEqual(imports, {"pyarrow"})
                self.assertEqual(bool(imports - dependencies), missing)

    def test_cleanup_changes_with_actual_consumer_evidence(self):
        for identity, entrypoint in [("code-cleanroom-rereview", "read_rows"),
                                     ("code-existing-consumer", "read_rows_legacy")]:
            with self.subTest(case=identity):
                artifacts = self.cases[identity]["artifacts"]
                callers = ast.parse(artifacts["caller.py"])
                imported = {alias.name for node in ast.walk(callers)
                            if isinstance(node, ast.ImportFrom) for alias in node.names}
                called = {node.func.id for node in ast.walk(callers)
                          if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)}
                self.assertEqual(imported, {entrypoint})
                self.assertEqual(called, {entrypoint})
                functions = {node.name for node in ast.parse(artifacts["client.py"]).body
                             if isinstance(node, ast.FunctionDef)}
                self.assertTrue(imported.issubset(functions))

    def test_rereview_retains_every_prior_id_and_has_real_snapshot_evidence(self):
        artifacts = self.cases["code-cleanroom-rereview"]["artifacts"]
        baseline = ast.parse(artifacts["baseline.py"])
        current = ast.parse(artifacts["client.py"])
        assignments = lambda tree: {target.id for node in tree.body if isinstance(node, ast.Assign)
                                    for target in node.targets if isinstance(target, ast.Name)}
        self.assertIn("LEGACY_DELIMITER", assignments(baseline))
        self.assertNotIn("LEGACY_DELIMITER", assignments(current))
        baseline_functions = {node.name for node in baseline.body if isinstance(node, ast.FunctionDef)}
        current_functions = {node.name for node in current.body if isinstance(node, ast.FunctionDef)}
        self.assertIn("read_rows_legacy", baseline_functions & current_functions)
        previous_ids = {entry["id"] for entry in json.loads(artifacts["previous.json"])}
        output = self.expected["cases"]["code-cleanroom-rereview"]
        self.assertEqual(set(output["prior_dispositions"]), previous_ids)
        aliases = {alias for finding in output["findings"] for alias in finding.get("aliases", [])}
        self.assertTrue(aliases.issubset(previous_ids))

    def test_retry_sources_demonstrate_the_terminal_event_consequence(self):
        source = self.cases["smells-terminal-policy"]["artifacts"]["retries.py"]
        functions = {}
        exec(compile(source, "synthetic/retries.py", "exec"), functions)
        for policy in ["first_policy", "second_policy"]:
            for attempt in [1, 2]:
                with self.subTest(policy=policy, attempt=attempt):
                    events = []
                    self.assertEqual(functions[policy](attempt, events.append), "retry")
                    self.assertEqual(events, [])
        first_events = []
        second_events = []
        self.assertEqual(functions["first_policy"](3, first_events.append), "done")
        self.assertEqual(functions["second_policy"](3, second_events.append), "done")
        self.assertEqual(first_events, ["terminal"])
        self.assertEqual(second_events, [])

    def test_audit_ledger_covers_real_inputs_and_dto_is_actually_used(self):
        artifacts = self.cases["smells-terminal-policy"]["artifacts"]
        coverage = self.expected["cases"]["smells-terminal-policy"]["coverage"]
        self.assertEqual(set(coverage), set(artifacts))
        model = ast.parse(artifacts["models.py"])
        names = {node.name for node in model.body if isinstance(node, ast.ClassDef)}
        api = ast.parse(artifacts["api.py"])
        used = {node.func.id for node in ast.walk(api)
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)}
        self.assertEqual(names, {"Outcome"})
        self.assertIn("Outcome", used)

    def test_representative_cases_and_answers_are_not_exported(self):
        unused_inventory, exported, inputs = payload(ROOT)
        self.assertFalse(any(path.startswith("evaluations/review/") for path in inputs))
        self.assertFalse(any("evaluations/" in path for path in exported))
        self.assertIn("skills/review/source-coverage.md", exported)


if __name__ == "__main__":
    unittest.main()
