import copy
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock


ROOT = Path(__file__).resolve().parents[1]
CASE_DIRECTORY = ROOT / "evaluations/workflow-methods/bdd-prd"
TEST_RUNNER = """
import json
import sys
import unittest

suite = unittest.TestSuite(
    unittest.defaultTestLoader.loadTestsFromName(module) for module in sys.argv[1:]
)
result = unittest.TextTestRunner(stream=sys.stderr, verbosity=2).run(suite)
print(json.dumps({
    "ran": result.testsRun,
    "failures": [{"test": test.id(), "trace": trace} for test, trace in result.failures],
    "errors": [{"test": test.id(), "trace": trace} for test, trace in result.errors],
    "successful": result.wasSuccessful(),
}))
raise SystemExit(0 if result.wasSuccessful() else 1)
"""


def worked_blocks(name):
    document = (ROOT / "develop" / name).read_text()
    matches = re.findall(
        r"```(python|json) file=([^\s]+) stage=([^\s]+)\n(.*?)\n```",
        document, re.DOTALL
    )
    blocks = {}
    for language, filename, stage, content in matches:
        key = (filename, stage)
        if key in blocks:
            raise ValueError(f"Duplicate worked block: {key}")
        blocks[key] = json.loads(content) if language == "json" else content + "\n"
    return blocks


def execute_design(blocks, filename):
    namespace = {}
    exec(compile(blocks[(filename, "design")], filename, "exec"), namespace)
    return namespace


def write_artifacts(workspace, artifacts):
    for filename, content in artifacts.items():
        relative = Path(filename)
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError(f"Unsafe fixture path: {filename}")
        target = workspace / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)


def run_suite(workspace, *modules):
    completed = subprocess.run(
        [sys.executable, "-B", "-c", TEST_RUNNER, *modules],
        cwd=workspace, capture_output=True, text=True, timeout=20, check=False
    )
    summary = json.loads(completed.stdout)
    summary["exit_code"] = completed.returncode
    return summary


def intended_red(result, test_identity):
    return (
        result["exit_code"] == 1
        and not result["successful"]
        and not result["errors"]
        and len(result["failures"]) == 1
        and result["failures"][0]["test"] == test_identity
        and "assert_not_called" in result["failures"][0]["trace"]
        and "AssertionError" in result["failures"][0]["trace"]
    )


class BddPrdMethodTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bdd = worked_blocks("bdd-worked.md")
        cls.prd = worked_blocks("prd-worked.md")
        cls.event_design = execute_design(cls.prd, "event_selection.py")
        cls.csv_design = execute_design(cls.prd, "inventory_import.py")
        raw = json.loads((CASE_DIRECTORY / "cases.json").read_text())
        cls.raw = raw
        cls.cases = {case["id"]: case for case in raw["cases"]}
        cls.expected = json.loads((CASE_DIRECTORY / "expected.json").read_text())

    def assert_red_then_green(self, baseline, test_files, production_path,
                              green, modules, red_test, count):
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            write_artifacts(workspace, {production_path: baseline, **test_files})
            original_tests = {name: (workspace / name).read_bytes() for name in test_files}
            red = run_suite(workspace, *modules)
            self.assertEqual(red["ran"], count, red)
            self.assertTrue(intended_red(red, red_test), red)
            self.assertEqual((workspace / production_path).read_text(), baseline)
            write_artifacts(workspace, {production_path: green})
            passing = run_suite(workspace, *modules)
            self.assertEqual(passing["exit_code"], 0, passing)
            self.assertEqual(passing["ran"], count, passing)
            self.assertTrue(passing["successful"], passing)
            self.assertEqual(passing["failures"], [])
            self.assertEqual(passing["errors"], [])
            self.assertEqual(
                {name: (workspace / name).read_bytes() for name in test_files}, original_tests
            )

    def test_reference_bdd_executes_intended_red_then_green(self):
        self.assert_red_then_green(
            self.bdd[("intake.py", "baseline")],
            {"test_intake.py": self.bdd[("test_intake.py", "test")]},
            "intake.py", self.bdd[("intake.py", "green")], ["test_intake"],
            "test_intake.IntakeTests.test_missing_identity_never_writes", 3
        )

    def test_fictional_bdd_executes_intended_red_then_green(self):
        self.assert_red_then_green(
            self.bdd[("dispatch.py", "baseline")],
            {"test_dispatch.py": self.bdd[("test_dispatch.py", "test")]},
            "dispatch.py", self.bdd[("dispatch.py", "green")], ["test_dispatch"],
            "test_dispatch.DispatchTests.test_missing_order_identity_never_books", 3
        )

    def test_no_write_assertion_rejects_an_error_after_write(self):
        unsafe = (
            "def submit_event(record, write_event):\n"
            "    if not record.get('canonical_event_id'):\n"
            "        write_event(record)\n"
            "        return {'status': 'invalid', 'error': 'missing_canonical_event_id'}\n"
            "    return {'status': 'submitted', 'receipt_id': write_event(record)}\n"
        )
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            write_artifacts(workspace, {
                "intake.py": unsafe, "test_intake.py": self.bdd[("test_intake.py", "test")]
            })
            result = run_suite(workspace, "test_intake")
            self.assertTrue(intended_red(
                result, "test_intake.IntakeTests.test_missing_identity_never_writes"
            ), result)

    def test_held_out_bdd_executes_red_then_green(self):
        identity = "bdd-library-member-identity"
        artifacts = self.cases[identity]["artifacts"]
        expected = self.expected["cases"][identity]
        self.assert_red_then_green(
            artifacts["loan.py"],
            {"test_loan.py": artifacts["test_loan.py"],
             "test_missing_identity.py": expected["illustrative_outputs"]["test_missing_identity.py"]},
            "loan.py", expected["illustrative_outputs"]["loan.py"],
            ["test_loan", "test_missing_identity"], expected["red_test"], 3
        )

    def test_already_passing_characterization_is_not_red(self):
        artifacts = self.cases["bdd-library-member-identity"]["artifacts"]
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            write_artifacts(workspace, artifacts)
            result = run_suite(workspace, "test_loan")
            self.assertEqual(result["ran"], 1)
            self.assertTrue(result["successful"], result)
            self.assertFalse(intended_red(result, "test_loan.LoanTests.test_valid_member_preserves_receipt"))

    def test_environment_error_does_not_qualify_as_behavioral_red(self):
        artifacts = self.cases["bdd-library-environment-blocker"]["artifacts"]
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            write_artifacts(workspace, artifacts)
            result = run_suite(workspace, "test_environment")
            self.assertEqual(result["failures"], [])
            self.assertEqual(len(result["errors"]), 1, result)
            self.assertIn("ModuleNotFoundError", result["errors"][0]["trace"])
            self.assertFalse(intended_red(
                result, "test_environment.LoanEnvironmentTests.test_missing_member_never_writes"
            ))

    def test_event_acceptance_artifact_is_executable_and_order_independent(self):
        contract = self.prd[("event-contract.json", "acceptance")]
        resolve = self.event_design["resolve_event"]
        for check in contract["checks"]:
            for catalog in [contract["catalog"], list(reversed(contract["catalog"]))]:
                with self.subTest(selector=check["selector"], catalog=catalog):
                    original = copy.deepcopy((check["selector"], catalog))
                    result = resolve(check["selector"], catalog, check.get("complete", True))
                    self.assertEqual(result, check["result"])
                    self.assertEqual((check["selector"], catalog), original)

    def test_event_invalid_inputs_and_catalogs_never_select(self):
        resolve = self.event_design["resolve_event"]
        catalog = [{"id": "evt-72", "name": "Review"}]
        for selector in [None, [], {"name": None}, {"name": " \t"},
                         {"id": 72}, {"extra": "evt-72"}, {"id": "evt-72", "name": ""}]:
            with self.subTest(selector=selector):
                self.assertEqual(resolve(selector, catalog), {"status": "invalid_input"})
        invalid_catalogs = [None, {}, [None], [{"name": "Review"}],
                            [{"id": 72, "name": "Review"}],
                            [{"id": "evt-72", "name": None}],
                            [{"id": "evt-72", "name": "Review"}] * 2]
        for invalid in invalid_catalogs:
            with self.subTest(catalog=invalid):
                self.assertEqual(resolve({"id": "evt-72"}, invalid),
                                 {"status": "catalog_unavailable"})
        self.assertEqual(resolve({"name": "Review"}, []), {"status": "not_found"})
        self.assertEqual(resolve({"id": " evt-72 "}, catalog), {"status": "not_found"})
        self.assertEqual(resolve({"name": "Reviéw"}, catalog), {"status": "not_found"})

    def test_held_out_room_contract_preserves_identity_and_ambiguity(self):
        identity = "prd-campus-room-selection"
        catalog = json.loads(self.cases[identity]["artifacts"]["catalog.json"])["rooms"]
        resolve = self.event_design["resolve_event"]
        for check in self.expected["cases"][identity]["checks"]:
            with self.subTest(selector=check["selector"]):
                self.assertEqual(resolve(check["selector"], catalog, check.get("complete", True)),
                                 check["result"])

    def test_csv_valid_import_preserves_canonical_ids_and_one_write(self):
        catalog = [{"sku": "stock-21"}, {"sku": "stock-67"}]
        original = copy.deepcopy(catalog)
        writer = Mock(return_value="receipt-92")
        result = self.csv_design["import_inventory"](
            b"sku,quantity\nstock-21,2\nstock-67,4\n", catalog, writer
        )
        self.assertEqual(result, {"status": "imported", "receipt_id": "receipt-92", "count": 2})
        writer.assert_called_once_with([
            {"sku": "stock-21", "quantity": 2}, {"sku": "stock-67", "quantity": 4}
        ])
        self.assertEqual(catalog, original)

    def test_csv_accepts_bom_crlf_quoted_ids_and_quantity_boundaries(self):
        catalog = [{"sku": 'stock,"A"'}, {"sku": "stock-Z"}]
        result = self.csv_design["validate_import"](
            '\ufeffsku,quantity\r\n"stock,""A""",1\r\nstock-Z,9999\r\n'.encode(), catalog
        )
        self.assertEqual(result, {"status": "ready", "records": [
            {"sku": 'stock,"A"', "quantity": 1}, {"sku": "stock-Z", "quantity": 9999}
        ]})

    def test_csv_rejections_never_call_writer(self):
        catalog = [{"sku": "stock-21"}, {"sku": "stock-67"}]
        cases = [
            ("sku,quantity\nstock-21,1\n", "invalid_payload", None),
            (b"x" * 1_048_577, "file_too_large", None),
            (b"\xff", "invalid_utf8", None),
            (b'sku,quantity\n"stock-21,1\n', "invalid_csv", None),
            (b"quantity,sku\n1,stock-21\n", "invalid_header", None),
            (b"sku,quantity,extra\nstock-21,1,no\n", "invalid_header", None),
            (b"sku;quantity\nstock-21;1\n", "invalid_header", None),
            (b"sku,sku\nstock-21,stock-21\n", "invalid_header", None),
            (b"sku,quantity\n", "missing_rows", None),
            (b"sku,quantity\n\n", "invalid_columns", 2),
            (b"sku,quantity\nstock-21\n", "invalid_columns", 2),
            (b"sku,quantity\nstock-21,1,extra\n", "invalid_columns", 2),
            (b"sku,quantity\n,1\n", "missing_sku", 2),
            (b"sku,quantity\n ,1\n", "missing_sku", 2),
            (b"sku,quantity\nStock-21,1\n", "unknown_sku", 2),
            (b"sku,quantity\n stock-21,1\n", "unknown_sku", 2),
            (b"sku,quantity\nstock-21,1\nstock-67,0\n", "invalid_quantity", 3),
            (b"sku,quantity\nstock-21,1\nstock-21,2\n", "duplicate_sku", 3),
        ]
        for payload, error, record in cases:
            with self.subTest(error=error, record=record, payload=str(payload)[:80]):
                writer = Mock()
                result = self.csv_design["import_inventory"](payload, catalog, writer)
                expected = {"status": "invalid", "error": error}
                if record is not None:
                    expected["record"] = record
                self.assertEqual(result, expected)
                writer.assert_not_called()

    def test_csv_quantity_domain_is_not_loosely_coerced(self):
        catalog = [{"sku": "stock-21"}]
        for quantity in ["", "0", "10000", "01", "-1", "+1", "1.0", " 1", "1 ", "١", "１"]:
            with self.subTest(quantity=quantity):
                result = self.csv_design["validate_import"](
                    f"sku,quantity\nstock-21,{quantity}\n".encode(), catalog
                )
                self.assertEqual(result, {"status": "invalid", "error": "invalid_quantity", "record": 2})

    def test_csv_catalog_availability_is_a_no_write_gate(self):
        payload = b"sku,quantity\nstock-21,1\n"
        invalid_catalogs = [None, {}, [None], [{}], [{"sku": 21}], [{"sku": " "}],
                            [{"sku": "stock-21"}] * 2]
        for catalog in invalid_catalogs:
            with self.subTest(catalog=catalog):
                writer = Mock()
                self.assertEqual(self.csv_design["import_inventory"](payload, catalog, writer),
                                 {"status": "invalid", "error": "catalog_unavailable"})
                writer.assert_not_called()
        writer = Mock()
        self.assertEqual(self.csv_design["import_inventory"](
            payload, [{"sku": "stock-21"}], writer, complete=False
        ), {"status": "invalid", "error": "catalog_unavailable"})
        writer.assert_not_called()

    def test_csv_record_limits_and_first_error_order(self):
        catalog = [{"sku": f"stock-{number}"} for number in range(501)]
        first_500 = "sku,quantity\n" + "".join(f"stock-{number},1\n" for number in range(500))
        result = self.csv_design["validate_import"](first_500.encode(), catalog)
        self.assertEqual(result["status"], "ready")
        self.assertEqual(len(result["records"]), 500)
        result = self.csv_design["validate_import"]((first_500 + "stock-500,1\n").encode(), catalog)
        self.assertEqual(result, {"status": "invalid", "error": "too_many_records"})
        result = self.csv_design["validate_import"](
            b"sku,quantity\nunknown,0\nstock-0,0\n", catalog
        )
        self.assertEqual(result, {"status": "invalid", "error": "unknown_sku", "record": 2})

    def test_csv_write_failure_propagates_without_retry(self):
        writer = Mock(side_effect=RuntimeError("batch rolled back"))
        with self.assertRaisesRegex(RuntimeError, "batch rolled back"):
            self.csv_design["import_inventory"](
                b"sku,quantity\nstock-21,1\n", [{"sku": "stock-21"}], writer
            )
        writer.assert_called_once_with([{"sku": "stock-21", "quantity": 1}])

    def test_csv_byte_and_field_limits_have_explicit_boundaries(self):
        identities = [f"stock-{number}-" + "A" * 2080 for number in range(500)]
        preliminary = "sku,quantity\n" + "".join(f"{sku},1\n" for sku in identities)
        padding = 1_048_576 - len(preliminary.encode())
        self.assertGreater(padding, 0)
        identities[0] += "B" * padding
        payload = ("sku,quantity\n" + "".join(f"{sku},1\n" for sku in identities)).encode()
        self.assertEqual(len(payload), 1_048_576)
        catalog = [{"sku": sku} for sku in identities]
        result = self.csv_design["validate_import"](payload, catalog)
        self.assertEqual(result["status"], "ready")
        self.assertEqual(len(result["records"]), 500)
        self.assertEqual(self.csv_design["validate_import"](payload + b"\n", catalog),
                         {"status": "invalid", "error": "file_too_large"})
        identity = "A" * 131_072
        self.assertEqual(self.csv_design["validate_import"](
            f"sku,quantity\n{identity},1\n".encode(), [{"sku": identity}]
        ), {"status": "ready", "records": [{"sku": identity, "quantity": 1}]})
        longer = identity + "A"
        self.assertEqual(self.csv_design["validate_import"](
            f"sku,quantity\n{longer},1\n".encode(), [{"sku": longer}]
        ), {"status": "invalid", "error": "invalid_csv"})

    def test_csv_errors_use_record_ordinals_not_physical_lines(self):
        catalog = [{"sku": "stock\n21"}, {"sku": "stock-67"}]
        writer = Mock()
        result = self.csv_design["import_inventory"](
            b'sku,quantity\n"stock\n21",1\nstock-67,0\n', catalog, writer
        )
        self.assertEqual(result, {"status": "invalid", "error": "invalid_quantity", "record": 3})
        writer.assert_not_called()

    def test_held_out_library_csv_contract_has_one_atomic_boundary(self):
        identity = "prd-library-donation-csv"
        artifacts = self.cases[identity]["artifacts"]
        catalog = json.loads(artifacts["catalog.json"])["products"]
        writer_contract = json.loads(artifacts["writer-contract.json"])
        for check in self.expected["cases"][identity]["checks"]:
            with self.subTest(artifact=check["artifact"]):
                writer = Mock(return_value=writer_contract["receipt"])
                result = self.csv_design["import_inventory"](
                    artifacts[check["artifact"]].encode(), catalog, writer
                )
                self.assertEqual(result, check["result"])
                if check["written"]:
                    writer.assert_called_once_with(check["written"])
                else:
                    writer.assert_not_called()

    def test_raw_cases_and_evaluator_expectations_are_separate(self):
        self.assertEqual(set(self.raw), {"schema_version", "synthetic_only", "cases"})
        self.assertEqual(self.raw["schema_version"], 1)
        self.assertTrue(self.raw["synthetic_only"])
        self.assertEqual(set(self.expected), {"schema_version", "evaluator_only", "cases"})
        self.assertEqual(self.expected["schema_version"], 1)
        self.assertTrue(self.expected["evaluator_only"])
        self.assertEqual(set(self.cases), set(self.expected["cases"]))
        for case in self.cases.values():
            self.assertEqual(set(case), {"id", "request", "context", "artifacts"})
            for filename, content in case["artifacts"].items():
                self.assertFalse(Path(filename).is_absolute())
                self.assertNotIn("..", Path(filename).parts)
                self.assertIsInstance(content, str)
            expected = self.expected["cases"][case["id"]]
            self.assertTrue(expected["illustrative_only"])
            self.assertEqual(expected["model_evaluation"], "not_run")
            for test_name in expected["verification"]:
                self.assertTrue(callable(getattr(self, test_name)))


if __name__ == "__main__":
    unittest.main()
