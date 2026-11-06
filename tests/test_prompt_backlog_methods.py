import ast
import copy
import hashlib
import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "evaluations/workflow-methods/prompt-backlog"


def execute_fixture(source, label):
    syntax = ast.parse(source, filename=label)
    allowed_imports = {"datetime", "hashlib", "json"}
    for statement in syntax.body:
        if not isinstance(statement, (ast.Import, ast.ImportFrom, ast.FunctionDef, ast.Assign)):
            raise ValueError("fixture must contain definitions only")
    for node in ast.walk(syntax):
        if isinstance(node, ast.Import) and any(alias.name not in allowed_imports for alias in node.names):
            raise ValueError("fixture import outside inert allowlist")
        if isinstance(node, ast.ImportFrom) and (node.module not in allowed_imports or node.level):
            raise ValueError("fixture import outside inert allowlist")
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in {"open", "eval", "exec", "compile", "input", "__import__", "getattr", "setattr"}:
                raise ValueError("fixture side-effect boundary")
        if isinstance(node, ast.Attribute) and node.attr.startswith("__"):
            raise ValueError("fixture cannot access runtime internals")
    namespace = {}
    exec(compile(syntax, label, "exec"), namespace)
    return namespace


def worked_fixture(filename):
    document = (ROOT / "develop" / filename).read_text()
    sources = re.findall(r"```python\n(.*?)\n```", document, re.DOTALL)
    if not sources:
        raise ValueError("worked fixture missing")
    namespace = {}
    for index, source in enumerate(sources):
        namespace.update(execute_fixture(source, f"synthetic/{filename}/{index}"))
    return namespace


def load_corpus():
    inputs = json.loads((CORPUS / "cases.json").read_text())
    expected = json.loads((CORPUS / "expected.json").read_text())
    return inputs, {case["id"]: case for case in inputs["cases"]}, expected


def artifact_json(case, filename):
    return json.loads(case["artifacts"][filename])


def profile_from_case(case):
    identity_types = {"str": str, "int": int}
    return {source: (mapping[0], mapping[1], identity_types[mapping[2]], mapping[3], mapping[4])
            for source, mapping in artifact_json(case, "profile.json").items()}


def revised_pack():
    return {
        "generation": "Summarize only supplied evidence; supported requires citations, otherwise uncertain.",
        "hint": json.dumps({"summary": "Insufficient evidence", "certainty": "uncertain", "evidence": []}),
        "replay": "Compact accepted summary, certainty and verified evidence with timestamp meanings.",
    }


class PromptContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = worked_fixture("prompt-worked.md")
        cls.inputs, cls.cases, cls.expected = load_corpus()

    def setUp(self):
        self.profile = self.fixture["PROFILES"]["documents"]
        self.context = {
            "notice-alpha": {"source": "notice", "text": "handoff delayed", "document_key": "DOC-ORBIT",
                         "issued_at": "2026-10-04T10:00:00Z", "occurrence_at": "2026-10-03T08:00:00Z"},
            "receipt-beta": {"source": "receipt", "text": "review completed", "receipt_key": 208,
                       "received_at": "2026-10-04T11:00:00Z", "processed_at": "2026-10-05T12:00:00Z"},
        }
        self.wire = {"summary": "The report and note describe a review", "certainty": "supported",
                     "evidence": [{"source": "notice", "reference": "notice-alpha", "quote": "handoff delayed"},
                                  {"source": "receipt", "reference": "receipt-beta", "quote": "review completed"}]}
        self.pack = revised_pack()
        self.journal = []

    def accept(self, wire=None, context=None, profile=None, subject_id="DOCUMENT-ORBIT"):
        selected_wire = self.wire if wire is None else wire
        raw = selected_wire if type(selected_wire) is str else json.dumps(selected_wire)
        return self.fixture["accept_and_record"](
            raw, self.context if context is None else context,
            self.profile if profile is None else profile, subject_id,
            self.pack, 2, self.journal, "document-run-orbit")

    def test_reference_identity_timestamp_enrichment_and_consumers(self):
        before = copy.deepcopy(self.context)
        output = self.accept()
        self.assertEqual(output["subject_id"], "DOCUMENT-ORBIT")
        report, note = output["evidence"]
        self.assertEqual(report["document_id"], "DOC-ORBIT")
        self.assertNotIn("receipt_id", report)
        self.assertEqual(note["receipt_id"], 208)
        self.assertEqual(report["source_timestamp"], before["notice-alpha"]["issued_at"])
        self.assertNotEqual(report["source_timestamp"], before["notice-alpha"]["occurrence_at"])
        self.assertEqual(note["source_timestamp"], before["receipt-beta"]["received_at"])
        self.assertNotEqual(note["source_timestamp"], before["receipt-beta"]["processed_at"])
        display = self.fixture["display"](output, self.profile)
        self.assertEqual(display["evidence_times"], [("document_issued", "2026-10-04T10:00:00Z"),
                                                   ("document_received", "2026-10-04T11:00:00Z")])
        replay = json.loads(self.fixture["accepted_replay"](self.journal, "document-run-orbit", self.profile))
        self.assertEqual(replay[0]["evidence"], output["evidence"])
        self.assertEqual(replay[0]["certainty"], "supported")
        self.assertNotIn("prompt", replay[0])
        self.assertEqual(self.context, before)
        for citation in self.wire["evidence"]:
            self.assertEqual(set(citation), {"source", "reference", "quote"})

    def test_wire_rejects_forgery_coercion_duplicates_and_invalid_evidence(self):
        invalid = []
        for field, value in [("subject_id", "FORGED"), ("prompt", {}), ("source_timestamp", "2026-01-01T00:00:00Z"),
                             ("certainty", True), ("certainty", "confirmed"), ("summary", " "), ("summary", 42),
                             ("evidence", {}), ("evidence", []), ("evidence", ["citation"])]:
            candidate = copy.deepcopy(self.wire)
            candidate[field] = value
            invalid.append(candidate)
        for field, value in [("source_timestamp", "2026-01-01T00:00:00Z"), ("document_id", "FORGED"),
                             ("unexpected_link", 999), ("reference", "invented"), ("reference", 208),
                             ("source", "receipt"), ("source", "unknown"), ("quote", "not in source")]:
            candidate = copy.deepcopy(self.wire)
            candidate["evidence"][0][field] = value
            invalid.append(candidate)
        candidate = copy.deepcopy(self.wire)
        del candidate["certainty"]
        invalid.append(candidate)
        invalid.extend(["not json", '{"summary":"first","summary":"second","certainty":"uncertain","evidence":[]}',
                        '{"summary":"ok","certainty":"supported","evidence":[{"source":"notice","reference":"notice-alpha","quote":"handoff delayed","quote":"handoff delayed"}]}'])
        for candidate in invalid:
            with self.subTest(candidate=candidate):
                with self.assertRaises(ValueError):
                    self.accept(candidate)
                self.assertEqual(self.journal, [])

    def test_missing_authoritative_times_never_fall_back(self):
        for reference, field in [("notice-alpha", "issued_at"), ("receipt-beta", "received_at")]:
            for replacement in [None, "", "2026-01-01T10:00:00", "2026-01-01"]:
                with self.subTest(reference=reference, replacement=replacement):
                    context = copy.deepcopy(self.context)
                    context[reference][field] = replacement
                    with self.assertRaises(ValueError):
                        self.accept(context=context)
                    self.assertEqual(self.journal, [])
            context = copy.deepcopy(self.context)
            del context[reference][field]
            with self.assertRaises(KeyError):
                self.accept(context=context)
            self.assertEqual(self.journal, [])

    def test_canonical_identity_is_application_supplied_and_strict(self):
        for reference, field, value in [("notice-alpha", "document_key", ""), ("notice-alpha", "document_key", 48),
                                         ("receipt-beta", "receipt_key", True), ("receipt-beta", "receipt_key", "208"),
                                         ("receipt-beta", "receipt_key", 0)]:
            with self.subTest(reference=reference, value=value):
                context = copy.deepcopy(self.context)
                context[reference][field] = value
                with self.assertRaises(ValueError):
                    self.accept(context=context)
                self.assertEqual(self.journal, [])
        for subject in ["", None, 48]:
            with self.assertRaises(ValueError):
                self.accept(subject_id=subject)
            self.assertEqual(self.journal, [])

    def test_final_validator_rejects_invalid_shape_metadata_and_time_meaning(self):
        output = self.accept()
        invalid = []
        for field, value in [("unexpected_link", 208), ("source_timestamp", "2026-10-04T10:00:00"),
                             ("timestamp_kind", "event_occurred"), ("document_id", True), ("extra", "value")]:
            candidate = copy.deepcopy(output)
            candidate["evidence"][0][field] = value
            invalid.append(candidate)
        for field, value in [("certainty", True), ("certainty", "maybe"), ("evidence", []),
                             ("subject_id", ""), ("extra", "value")]:
            candidate = copy.deepcopy(output)
            candidate[field] = value
            invalid.append(candidate)
        for field, value in [("version", True), ("name", "evidence-summary.v1"), ("sha256", "not-a-hash")]:
            candidate = copy.deepcopy(output)
            candidate["prompt"][field] = value
            invalid.append(candidate)
        for candidate in invalid:
            with self.subTest(candidate=candidate):
                with self.assertRaises(ValueError):
                    self.fixture["validate_final"](candidate, self.profile)

    def test_uncertain_empty_evidence_survives_accepted_replay_and_display(self):
        uncertain = {"summary": "Cause is not established", "certainty": "uncertain", "evidence": []}
        output = self.accept(uncertain)
        self.assertEqual(self.fixture["display"](output, self.profile),
                         {"summary": "Cause is not established", "certainty": "uncertain", "evidence_times": []})
        replay = json.loads(self.fixture["accepted_replay"](self.journal, "document-run-orbit", self.profile))
        self.assertEqual(replay, [{"subject_id": "DOCUMENT-ORBIT", **uncertain}])

    def test_replay_rejects_malformed_accepted_output_instead_of_downgrading(self):
        output = self.accept()
        malformed = copy.deepcopy(output)
        malformed["evidence"][0]["source"] = []
        self.journal.append({"event": "validated_response", "run_key": "document-run-orbit",
                             "step": "summary", "output": malformed})
        with self.assertRaises(ValueError):
            self.fixture["accepted_replay"](self.journal, "document-run-orbit", self.profile)

    def test_every_model_visible_surface_changes_hash_and_registered_identity(self):
        baseline = {"generation": "Return summary and evidence", "hint": '{"summary":"ok","evidence":[]}',
                    "replay": "Compact accepted summary and evidence"}
        previous = self.fixture["prompt_metadata"](baseline, 1)
        current = self.fixture["prompt_metadata"](self.pack, 2)
        self.assertEqual(previous["name"], "evidence-summary.v1")
        self.assertEqual(current["name"], "evidence-summary.v2")
        self.assertEqual(current["version"], 2)
        self.assertNotEqual(previous["sha256"], current["sha256"])
        encoded = json.dumps(self.pack, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
        self.assertEqual(current["sha256"], hashlib.sha256(encoded).hexdigest())
        for surface in self.pack:
            changed = dict(self.pack)
            changed[surface] += " changed behavior"
            self.assertNotEqual(self.fixture["prompt_metadata"](changed, 2)["sha256"], current["sha256"])
        self.assertEqual(self.accept()["prompt"], current)

    def test_equipment_issued_and_processing_times_are_separate_without_domain_fields(self):
        context = {
            "notice-0": {"source": "notice", "text": "permit issued", "DocumentId": "NOTICE-71",
                         "IssuedAt": "2026-09-08T09:00:00Z", "ProcessedAt": "2026-09-09T14:00:00Z"},
            "receipt-0": {"source": "receipt", "text": "notice indexed", "ReceiptId": "INTAKE-71",
                          "ProcessedAt": "2026-09-09T14:00:00Z"},
        }
        wire = {"summary": "The issued notice was indexed", "certainty": "supported",
                "evidence": [{"source": "notice", "reference": "notice-0", "quote": "permit issued"},
                             {"source": "receipt", "reference": "receipt-0", "quote": "notice indexed"}]}
        profile = self.fixture["PROFILES"]["equipment"]
        output = self.accept(wire, context, profile, "PERMIT-71")
        self.assertEqual(self.fixture["display"](output, profile)["evidence_times"],
                         [("document_issued", "2026-09-08T09:00:00Z"), ("processing", "2026-09-09T14:00:00Z")])
        self.assertEqual(output["evidence"][0]["document_id"], "NOTICE-71")
        self.assertEqual(output["evidence"][1]["receipt_id"], "INTAKE-71")
        for citation in output["evidence"]:
            self.assertNotIn("receipt_key", citation)
        del context["notice-0"]["IssuedAt"]
        before = copy.deepcopy(self.journal)
        with self.assertRaises(KeyError):
            self.accept(wire, context, profile, "PERMIT-71")
        self.assertEqual(self.journal, before)

    def test_heldout_museum_source_exposes_baseline_bug_and_revised_mapping(self):
        identity = "prompt-museum-issued-processing"
        case = self.cases[identity]
        criteria = self.expected["cases"][identity]["deterministic"]
        context = artifact_json(case, "context.json")
        baseline = execute_fixture(case["artifacts"]["adapter.py"], "synthetic/museum/adapter.py")
        previous = baseline["accept"](case["artifacts"]["wire.json"], context["sources"])
        self.assertEqual(previous["evidence"][0]["source_timestamp"], criteria["processing"])
        profile = profile_from_case(case)
        wire = artifact_json(case, "wire.json")
        wire["certainty"] = "supported"
        wire["evidence"].append({"source": "catalog", "reference": "catalog-q", "quote": "catalog entry processed"})
        output = self.fixture["accept_and_record"](json.dumps(wire), context["sources"], profile,
                                                   context["subject_id"], self.pack, criteria["new_version"],
                                                   self.journal, context["run_key"])
        self.assertEqual(output["subject_id"], criteria["subject_id"])
        self.assertEqual(output["evidence"][0]["letter_id"], criteria["letter_id"])
        self.assertEqual(output["evidence"][0]["source_timestamp"], criteria["issued"])
        self.assertEqual(output["evidence"][1]["source_timestamp"], criteria["processing"])
        self.assertNotEqual(output["evidence"][0]["source_timestamp"], previous["evidence"][0]["source_timestamp"])
        self.assertEqual(output["prompt"]["name"], "evidence-summary.v2")
        self.assertEqual(self.fixture["display"](output, profile)["certainty"], "supported")
        self.assertEqual(len(json.loads(self.fixture["accepted_replay"](self.journal, context["run_key"], profile))), 1)

    def test_heldout_freight_filters_failures_repairs_wrong_runs_and_steps(self):
        identity = "prompt-freight-accepted-replay"
        case = self.cases[identity]
        criteria = self.expected["cases"][identity]["deterministic"]
        context = artifact_json(case, "context.json")
        events = artifact_json(case, "attempts.json")
        profile = profile_from_case(case)
        baseline = execute_fixture(case["artifacts"]["journal.py"], "synthetic/freight/journal.py")
        self.assertEqual(baseline["replay"](events, context["run_key"]), criteria["sentinels"][:3])
        self.assertEqual(json.loads(self.fixture["accepted_replay"](events, context["run_key"], profile)),
                         criteria["failed_only_replay"])
        before = copy.deepcopy(events)
        with self.assertRaises(ValueError):
            self.fixture["accept_and_record"](case["artifacts"]["wire.json"], context["sources"], profile,
                                               context["subject_id"], self.pack, criteria["new_version"],
                                               events, context["run_key"])
        self.assertEqual(events, before)
        repaired = {"summary": "Arrival cannot be established", "certainty": "uncertain", "evidence": []}
        output = self.fixture["accept_and_record"](json.dumps(repaired), context["sources"], profile,
                                                   context["subject_id"], self.pack, criteria["new_version"],
                                                   events, context["run_key"])
        events.extend([{"event": "validated_response", "run_key": "other-run", "step": "summary", "output": "not parsed"},
                       {"event": "validated_response", "run_key": context["run_key"], "step": "other", "output": "not parsed"}])
        replay = self.fixture["accepted_replay"](events, context["run_key"], profile)
        self.assertEqual(json.loads(replay), [{"subject_id": context["subject_id"], **repaired}])
        self.assertEqual(output["prompt"]["name"], "evidence-summary.v5")
        for sentinel in criteria["sentinels"]:
            self.assertNotIn(sentinel, replay)


class BacklogContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = worked_fixture("backlog-worked.md")
        cls.inputs, cls.cases, cls.expected = load_corpus()

    def register(self, identity, pages=None, evidence=None):
        case = self.cases[identity]
        requirements = artifact_json(case, "requirements.json")
        selected_pages = artifact_json(case, "pages.json") if pages is None else pages
        selected_evidence = artifact_json(case, "inspection.json") if evidence is None else evidence
        result = self.fixture["reconcile"](requirements, selected_pages, selected_evidence)
        return {row["id"]: row for row in result}

    def test_equipment_warehouse_source_proves_baseline_and_only_partial_increment(self):
        records = [{"sku": "SKU-71", "quantity": "2", "threshold": "5", "supplier_id": "SUP-71"},
                   {"sku": "SKU-72", "quantity": "8", "threshold": "5", "supplier_id": "SUP-72"}]
        stock = [self.fixture["normalize_stock"](record) for record in records]
        self.assertEqual(stock[0], {"sku": "SKU-71", "quantity": 2, "threshold": 5, "supplier_id": "SUP-71"})
        self.assertEqual(self.fixture["select_alerts"](stock), ["SKU-71"])
        self.assertNotIn("dispatch", self.fixture)
        requirements = [{"id": "STOCK-A", "source": "S1#alerts", "source_priority": "0.5", "scope_state": "approved",
                         "baseline": ["stock-engine"], "increment": ["threshold-selection", "dispatch"], "dependencies": ["access approval"]},
                        {"id": "STOCK-E", "source": "S1#expiry", "source_priority": "1.5", "scope_state": "approved",
                         "baseline": ["stock-engine"], "increment": ["expiry-export"], "dependencies": []},
                        {"id": "STOCK-V", "source": "D1 versus draft", "source_priority": "3", "scope_state": "conflict",
                         "baseline": ["stock-engine"], "increment": ["vendor-write"], "dependencies": ["scope decision"]},
                        {"id": "STOCK-R", "source": "S1#acknowledgment", "source_priority": "2", "scope_state": "approved",
                         "baseline": ["stock-engine"], "increment": ["acknowledgment"], "dependencies": ["supplier gateway owner"]}]
        baseline = {"key": "STOCK-20", "status": "Done", "priority": "Low", "scope": ["stock-engine"],
                    "roles": {requirement["id"]: "supporting" for requirement in requirements}}
        primary = {"key": "STOCK-31", "status": "In Progress", "priority": "High", "scope": ["threshold-selection", "dispatch"],
                   "roles": {"STOCK-A": "primary"}}
        export = {"key": "STOCK-44", "status": "To Do", "priority": "Unassigned", "scope": ["expiry-export"],
                  "roles": {"STOCK-E": "primary"}}
        validation = {"key": "STOCK-52", "status": "To Do", "priority": "Low", "scope": ["review"],
                      "roles": {"STOCK-A": "validation", "STOCK-E": "validation"}}
        pages = [{"cursor": None, "next_cursor": "page-2", "items": [baseline, primary]},
                 {"cursor": "page-2", "next_cursor": None, "items": [export, validation]}]
        evidence = {"verified": ["stock-engine", "threshold-selection"], "local_complete": True,
                    "uninspected": ["supplier gateway"], "approved_validation": []}
        register = {row["id"]: row for row in self.fixture["reconcile"](requirements, pages, evidence)}
        self.assertEqual(register["STOCK-A"]["coverage"], "partial")
        self.assertEqual(register["STOCK-A"]["primary"], ["STOCK-31"])
        self.assertEqual(register["STOCK-A"]["validation_state"], "outstanding")
        self.assertEqual(register["STOCK-E"]["primary"], ["STOCK-44"])
        self.assertEqual(register["STOCK-V"]["scope_state"], "conflict")
        self.assertEqual(register["STOCK-R"]["ownership"], "gap")
        self.assertEqual(register["STOCK-R"]["implementation_elsewhere"], "unknown")
        partial = {row["id"]: row for row in self.fixture["reconcile"](requirements, pages[:1], evidence)}
        self.assertEqual(partial["STOCK-E"]["ownership"], "unknown")
        self.assertEqual(partial["STOCK-R"]["ownership"], "unknown")

    def test_heldout_campus_source_executes_shared_engine_and_partial_delivery(self):
        case = self.cases["backlog-campus-complete-coverage"]
        source = execute_fixture(case["artifacts"]["scheduler.py"], "synthetic/campus/scheduler.py")
        self.assertEqual(source["normalize_room"]({"room_id": "HALL-Q7", "capacity": "24"}),
                         {"room_id": "HALL-Q7", "capacity": 24})
        reservations = [{"reservation_id": "RS-Q71", "room_id": "HALL-Q7", "cancelled": True},
                        {"reservation_id": "RS-Q72", "room_id": "HALL-Q7", "cancelled": False},
                        {"reservation_id": "RS-Q73", "room_id": "HALL-Q8", "cancelled": True}]
        self.assertEqual(source["select_cancellation"](reservations, "HALL-Q7"), ["RS-Q71"])
        self.assertNotIn("send_cancellation", source)
        self.assertNotIn("export_accessible_rooms", source)
        with self.assertRaises(ValueError):
            source["normalize_room"]({"room_id": "", "capacity": 24})
        evidence = artifact_json(case, "inspection.json")
        self.assertEqual(evidence["verified"], ["room-index", "cancel-selection"])

    def test_heldout_campus_complete_register_matches_roles_priorities_and_gaps(self):
        identity = "backlog-campus-complete-coverage"
        register = self.register(identity)
        expected = self.expected["cases"][identity]["deterministic"]
        self.assertEqual(set(register), set(expected))
        for requirement, fields in expected.items():
            with self.subTest(requirement=requirement):
                for field, value in fields.items():
                    self.assertEqual(register[requirement][field], value)
                self.assertTrue(register[requirement]["pagination_complete"])
                self.assertEqual(register[requirement]["baseline_implemented"], ["room-index"])
                self.assertEqual(register[requirement]["tracker_status"]["ROOM-10"], "Done")
        self.assertEqual(register["ROOM-B"]["validation"], ["ROOM-32"])
        self.assertEqual(register["ROOM-B"]["validation_state"], "outstanding")
        self.assertEqual(register["ROOM-D"]["primary"], [])

    def test_incomplete_pages_change_unseen_owners_to_unknown_not_gaps(self):
        identity = "backlog-campus-complete-coverage"
        pages = artifact_json(self.cases[identity], "pages.json")[:1]
        register = self.register(identity, pages=pages)
        self.assertEqual(register["ROOM-A"]["ownership"], "existing")
        self.assertEqual(register["ROOM-A"]["coverage"], "partial")
        for requirement in ["ROOM-B", "ROOM-C", "ROOM-D"]:
            self.assertEqual(register[requirement]["ownership"], "unknown")
            self.assertFalse(register[requirement]["pagination_complete"])
        self.assertEqual(register["ROOM-B"]["primary"], [])
        self.assertEqual(register["ROOM-A"]["validation_state"], "unknown")

    def test_heldout_course_source_and_incomplete_register_preserve_unknowns(self):
        identity = "backlog-course-incomplete-inventory"
        case = self.cases[identity]
        source = execute_fixture(case["artifacts"]["credentials.py"], "synthetic/course/credentials.py")
        for completed in [True, False]:
            result = source["normalize_completion"]({"learner_id": "LEARNER-W3", "completed": completed})
            self.assertEqual(result, {"learner_id": "LEARNER-W3", "completed": completed})
            self.assertEqual(source["award_preview"](result), {"learner_id": "LEARNER-W3", "eligible": completed})
        self.assertNotIn("deliver_award", source)
        self.assertNotIn("partner_send", source)
        register = self.register(identity)
        expected = self.expected["cases"][identity]["deterministic"]
        self.assertEqual(set(register), set(expected))
        for requirement, fields in expected.items():
            with self.subTest(requirement=requirement):
                for field, value in fields.items():
                    self.assertEqual(register[requirement][field], value)
                self.assertFalse(register[requirement]["pagination_complete"])
                self.assertEqual(register[requirement]["tracker_status"]["CERT-60"], "Done")

    def test_authority_inventory_excludes_superseded_duplicates_and_retains_conflicts(self):
        for identity in ["backlog-campus-complete-coverage", "backlog-course-incomplete-inventory"]:
            case = self.cases[identity]
            ledger = artifact_json(case, "authority.json")["sources"]
            current_definitions = [source for source in ledger if source["role"] == "definitions" and source["disposition"] == "current"]
            self.assertEqual(len(current_definitions), 1)
            register = self.register(identity)
            superseded_ids = {repeated for source in ledger if source["disposition"] == "superseded"
                              for repeated in source.get("repeats", [])}
            self.assertTrue(superseded_ids.issubset(register))
            self.assertEqual(len(register), len(artifact_json(case, "requirements.json")))
            conflicts = [row for row in register.values() if row["scope_state"] == "conflict"]
            self.assertEqual(len(conflicts), 1)
            self.assertTrue(conflicts[0]["dependencies"])
            signed = next(source for source in ledger if source["role"] == "signed_scope")
            proposal = next(source for source in ledger if source["disposition"] == "unresolved_conflict")
            self.assertLess(signed["date"], proposal["date"])
            self.assertIn(signed["id"], conflicts[0]["source"])
            self.assertIn(proposal["id"], conflicts[0]["source"])

    def test_reconciliation_does_not_mutate_inputs_or_turn_done_support_into_delivery(self):
        case = self.cases["backlog-campus-complete-coverage"]
        requirements = artifact_json(case, "requirements.json")
        pages = artifact_json(case, "pages.json")
        evidence = artifact_json(case, "inspection.json")
        before = copy.deepcopy((requirements, pages, evidence))
        register = self.fixture["reconcile"](requirements, pages, evidence)
        self.assertEqual((requirements, pages, evidence), before)
        for row in register:
            self.assertNotIn("ROOM-10", row["primary"])
            self.assertEqual(row["supporting"], ["ROOM-10"])
            self.assertNotEqual(row["coverage"], "implemented")
        evidence["approved_validation"] = ["ROOM-A"]
        approved = self.fixture["reconcile"](requirements, pages, evidence)[0]
        self.assertEqual(approved["validation_state"], "approved")
        self.assertEqual(approved["coverage"], "partial")
        self.assertEqual(approved["tracker_status"]["ROOM-14"], "In Progress")

    def test_page_chain_rejects_skips_duplicates_and_rows_after_terminal(self):
        identity = "backlog-campus-complete-coverage"
        pages = artifact_json(self.cases[identity], "pages.json")
        skipped = copy.deepcopy(pages)
        skipped[1]["cursor"] = "different-query"
        after_terminal = copy.deepcopy(pages)
        after_terminal[0]["next_cursor"] = None
        duplicated = copy.deepcopy(pages)
        duplicated[1]["items"].append(copy.deepcopy(duplicated[0]["items"][0]))
        for invalid in [skipped, after_terminal, duplicated]:
            with self.assertRaises(ValueError):
                self.register(identity, pages=invalid)
        self.assertEqual(self.fixture["inspect_pages"]([]), ([], False))

    def test_overlapping_primary_owners_require_resolution_not_arbitrary_selection(self):
        identity = "backlog-campus-complete-coverage"
        pages = artifact_json(self.cases[identity], "pages.json")
        extra = copy.deepcopy(pages[0]["items"][1])
        extra["key"] = "ROOM-99"
        pages[1]["items"].append(extra)
        row = self.register(identity, pages=pages)["ROOM-A"]
        self.assertEqual(row["ownership"], "overlap")
        self.assertEqual(row["primary"], ["ROOM-14", "ROOM-99"])


class PromptBacklogCorpusTests(unittest.TestCase):
    def test_traceability_maps_every_case_to_real_executable_tests_and_resources(self):
        traceability = json.loads((CORPUS / "traceability.json").read_text())
        unused_inputs, cases, unused_expected = load_corpus()
        self.assertEqual(set(traceability["cases"]), set(cases))
        syntax = ast.parse(Path(__file__).read_text())
        available_tests = {f"{definition.name}.{method.name}"
                           for definition in syntax.body if isinstance(definition, ast.ClassDef)
                           for method in definition.body if isinstance(method, ast.FunctionDef) and method.name.startswith("test_")}
        for mapping in traceability["requirements"]:
            self.assertTrue(mapping["tests"])
            self.assertTrue(set(mapping["tests"]).issubset(available_tests))
            for relative in mapping["references"] + [mapping["worked"]]:
                path = ROOT / relative
                self.assertTrue(path.resolve().is_relative_to(ROOT))
                self.assertTrue(path.is_file())
        for tests in traceability["cases"].values():
            self.assertTrue(tests)
            self.assertTrue(set(tests).issubset(available_tests))

    def test_cases_are_independent_raw_inputs_and_expectations_are_not_model_results(self):
        inputs, cases, expected = load_corpus()
        self.assertEqual(inputs["schema_version"], 1)
        self.assertIs(inputs["synthetic_only"], True)
        self.assertEqual(expected["schema_version"], 1)
        self.assertIs(expected["evaluator_only"], True)
        self.assertEqual(set(cases), set(expected["cases"]))
        self.assertEqual(len(cases), len(inputs["cases"]))
        for identity, case in cases.items():
            self.assertEqual(set(case), {"id", "request", "context", "artifacts"})
            self.assertIs(expected["cases"][identity]["illustrative_criteria_not_model_results"], True)
            self.assertNotIn("model_result", expected["cases"][identity])
            for relative, content in case["artifacts"].items():
                path = Path(relative)
                self.assertFalse(path.is_absolute())
                self.assertNotIn("..", path.parts)
                self.assertIsInstance(content, str)
                if relative.endswith(".json"):
                    json.loads(content)
                if relative.endswith(".py"):
                    execute_fixture(content, f"synthetic/{identity}/{relative}")

    def test_frozen_baseline_source_hashes_are_internally_consistent(self):
        baseline = json.loads((ROOT / "evaluations/workflow-methods/baseline.json").read_text())
        for filename in ["develop/prompt.md", "develop/backlog.md"]:
            frozen = baseline["sources"][filename]
            self.assertEqual(hashlib.sha256(frozen["content"].encode()).hexdigest(), frozen["sha256"])
            current = ROOT / filename
            self.assertNotEqual(current.read_text(), frozen["content"])


if __name__ == "__main__":
    unittest.main()
