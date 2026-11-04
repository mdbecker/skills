# Worked coordinated prompt edit

## Scope and baseline

This synthetic application already has generation instructions, a wire hint, a
strict validator, application enrichment, accepted-event replay and a display
consumer. These are mapped seams, not instructions to add a pipeline to another
project. The baseline returns `summary` and `evidence`; it cannot distinguish a
supported summary from an uncertain one. The bounded increment adds required
`certainty` (`supported` or `uncertain`) across those seams. No model calls,
source acquisition, persistent storage or production changes are demonstrated.

## Coordinated edits

| Existing application seam | Baseline → revision / observable result |
|---|---|
| `prompts/summary.txt` | Add the certainty decision, keeping source selection and uncertainty in generation behavior; no identity/time derivation. |
| `prompts/summary-json.txt` | Add exactly one required enum field and both supported/uncertain wire examples; no enrichment fields. |
| `validation.py` | Require exact keys/types, reject coercion/duplicates, require evidence for supported output, validate supplied source/reference and quote. |
| `evidence.py` | Resolve canonical IDs and authoritative timestamps from application context only; missing metadata fails before acceptance; retain final strict validation. |
| `prompts/summary-tldr.txt` / accepted reader | Include certainty in compact accepted replay; failed output, errors and repairs remain outside the replay boundary. |
| `display.py` | Render certainty and evidence timestamp meaning without calling either timestamp an event occurrence. |
| `registry.py` / request metadata | Keep resource filenames stable; logical `evidence-summary.v1` → `evidence-summary.v2`, version `1` → `2`, SHA-256 recomputed over defined model-visible surfaces. |

The revised generation text is: “Summarize only supplied evidence. Set certainty
to supported only when cited evidence supports the summary; otherwise uncertain.
Do not fill missing information by inference. Return only summary, certainty,
evidence.” The wire hint returns:

```json
{"summary":"The report describes a delayed handoff.","certainty":"supported","evidence":[{"source":"report","reference":"report-0","quote":"handoff delayed"}]}
```

```json
{"summary":"The cause cannot be established from supplied material.","certainty":"uncertain","evidence":[]}
```

The TL;DR contract is: “Replay accepted summary, certainty and verified evidence
identities/timestamp meanings only. Preserve uncertainty for downstream reasoning.”
None of these model-facing resources delegates timestamp ownership to the model.

## Application-owned source mapping

| Profile / source | Supplied canonical identity | Authoritative evidence timestamp | Distinct, not substituted |
|---|---|---|---|
| Reference / report | `Id` → `report_id`; `clinical_note_key=null` | `CreatedDate` → report creation | `Date_of_Event__c` is event occurrence. |
| Reference / clinical note | `DurableKey` → `clinical_note_key` | `ServiceInstant` → note service | `CreationInstant` is note creation; service is not automatically event occurrence. |
| Nonclinical municipal permit / notice | `DocumentId` → `document_id` | `IssuedAt` → document issuance | Receipt processing is a separate activity, not document issuance. |
| Nonclinical municipal permit / receipt | `ReceiptId` → `receipt_id` | `ProcessedAt` → intake processing | Neither this nor `IssuedAt` establishes when the building work occurred. |

The application supplies the subject identity and the source-context reference
map; a model may select a supplied reference, never create an authoritative ID.
Unknown or inconsistent references fail. The strict application output includes
source timestamps, but the model wire does not. Reference-only clinical fields
are not present in the municipal final output.

## Executable synthetic fixture

This deliberately small in-memory fixture realizes all mapped seams. Exact
substring quote checking illustrates the boundary, not a replacement for an
existing project's reconciliation/redaction/fuzzy-match order. Tests execute this
fence with local synthetic inputs; they do not treat it as production code.

```python
import hashlib
import json
from datetime import datetime


PROFILES = {
    "reference": {
        "report": ("Id", "report_id", str, "CreatedDate", "report_created"),
        "clinical_note": ("DurableKey", "clinical_note_key", int, "ServiceInstant", "note_service"),
    },
    "municipal": {
        "notice": ("DocumentId", "document_id", str, "IssuedAt", "document_issued"),
        "receipt": ("ReceiptId", "receipt_id", str, "ProcessedAt", "processing"),
    },
}


def exact_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate key")
        result[key] = value
    return result


def exact_keys(value, keys):
    if type(value) is not dict or set(value) != set(keys):
        raise ValueError("invalid object shape")


def nonblank(value):
    if type(value) is not str or not value.strip():
        raise ValueError("nonblank string required")


def validate_time(value):
    nonblank(value)
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if "T" not in value or parsed.tzinfo is None:
        raise ValueError("timezone-bearing source timestamp required")


def prompt_metadata(pack, version):
    exact_keys(pack, {"generation", "hint", "replay"})
    for text in pack.values():
        nonblank(text)
    if type(version) is not int or version < 1:
        raise ValueError("invalid prompt version")
    visible = json.dumps(pack, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return {"name": f"evidence-summary.v{version}", "version": version,
            "sha256": hashlib.sha256(visible.encode("utf-8")).hexdigest()}


def validate_wire(raw, context, profile):
    output = json.loads(raw, object_pairs_hook=exact_object)
    exact_keys(output, {"summary", "certainty", "evidence"})
    nonblank(output["summary"])
    if type(output["certainty"]) is not str or output["certainty"] not in {"supported", "uncertain"}:
        raise ValueError("invalid certainty")
    if type(output["evidence"]) is not list:
        raise ValueError("evidence must be a list")
    if output["certainty"] == "supported" and not output["evidence"]:
        raise ValueError("supported output requires evidence")
    for citation in output["evidence"]:
        exact_keys(citation, {"source", "reference", "quote"})
        for value in citation.values():
            nonblank(value)
        if citation["source"] not in profile or citation["reference"] not in context:
            raise ValueError("unknown source reference")
        supplied = context[citation["reference"]]
        if supplied["source"] != citation["source"] or citation["quote"] not in supplied["text"]:
            raise ValueError("source or quote mismatch")
    return output


def validate_final(output, profile):
    exact_keys(output, {"subject_id", "summary", "certainty", "evidence", "prompt"})
    nonblank(output["subject_id"])
    nonblank(output["summary"])
    if type(output["certainty"]) is not str or output["certainty"] not in {"supported", "uncertain"}:
        raise ValueError("invalid final certainty")
    if type(output["evidence"]) is not list or (output["certainty"] == "supported" and not output["evidence"]):
        raise ValueError("invalid final evidence")
    exact_keys(output["prompt"], {"name", "version", "sha256"})
    metadata = output["prompt"]
    if type(metadata["version"]) is not int or metadata["version"] < 1:
        raise ValueError("invalid final version")
    if metadata["name"] != f"evidence-summary.v{metadata['version']}":
        raise ValueError("invalid logical identity")
    if type(metadata["sha256"]) is not str or len(metadata["sha256"]) != 64 or any(character not in "0123456789abcdef" for character in metadata["sha256"]):
        raise ValueError("invalid hash")
    for citation in output["evidence"]:
        if type(citation) is not dict or type(citation.get("source")) is not str or citation["source"] not in profile:
            raise ValueError("invalid final source")
        unused_input, identity_field, identity_type, unused_time, meaning = profile[citation["source"]]
        keys = {"source", "quote", identity_field, "source_timestamp", "timestamp_kind"}
        if citation["source"] == "report" and identity_field == "report_id":
            keys.add("clinical_note_key")
            if citation.get("clinical_note_key") is not None:
                raise ValueError("report note key must be null")
        exact_keys(citation, keys)
        if type(citation[identity_field]) is not identity_type:
            raise ValueError("invalid canonical identity")
        if identity_type is str:
            nonblank(citation[identity_field])
        elif citation[identity_field] < 1:
            raise ValueError("invalid canonical key")
        nonblank(citation["quote"])
        validate_time(citation["source_timestamp"])
        if citation["timestamp_kind"] != meaning:
            raise ValueError("timestamp meaning mismatch")
    return output


def accept_and_record(raw, context, profile, subject_id, pack, version, journal, run_key):
    nonblank(run_key)
    wire = validate_wire(raw, context, profile)
    enriched = []
    for citation in wire["evidence"]:
        supplied = context[citation["reference"]]
        input_identity, output_identity, unused_type, input_time, meaning = profile[citation["source"]]
        evidence = {"source": citation["source"], "quote": citation["quote"],
                    output_identity: supplied[input_identity],
                    "source_timestamp": supplied[input_time], "timestamp_kind": meaning}
        if citation["source"] == "report" and output_identity == "report_id":
            evidence["clinical_note_key"] = None
        enriched.append(evidence)
    output = {"subject_id": subject_id, "summary": wire["summary"], "certainty": wire["certainty"],
              "evidence": enriched, "prompt": prompt_metadata(pack, version)}
    validate_final(output, profile)
    journal.append({"event": "validated_response", "run_key": run_key, "step": "summary", "output": output})
    return output


def accepted_replay(journal, run_key, profile):
    outputs = [validate_final(entry["output"], profile) for entry in journal
               if entry["event"] == "validated_response" and entry["run_key"] == run_key and entry["step"] == "summary"]
    return json.dumps([{key: output[key] for key in ("subject_id", "summary", "certainty", "evidence")}
                       for output in outputs], sort_keys=True)


def display(output, profile):
    validate_final(output, profile)
    return {"summary": output["summary"], "certainty": output["certainty"],
            "evidence_times": [(citation["timestamp_kind"], citation["source_timestamp"])
                               for citation in output["evidence"]]}
```

## Reference output and failure result

Application subject `CASE-48` has report `report-0`: `Id=R-48`, text “handoff
delayed”, `CreatedDate=2026-10-04T10:00:00Z`, and
`Date_of_Event__c=2026-10-03T08:00:00Z`. Note `note-0` has `DurableKey=208`, text
“review completed”, `ServiceInstant=2026-10-04T11:00:00Z`, and
`CreationInstant=2026-10-05T12:00:00Z`. Event occurrence remains October 3; the
note service and note creation are October 4 and October 5 respectively.

With the first wire example, acceptance produces `subject_id=CASE-48`, supported
certainty and report evidence `{source: report, report_id: R-48,
clinical_note_key: null, quote: handoff delayed,
source_timestamp: 2026-10-04T10:00:00Z, timestamp_kind: report_created}` plus the
application's v2 prompt metadata. A supplied note citation similarly receives key
208 and **service** timestamp `2026-10-04T11:00:00Z`, never its creation timestamp.
Display and compact replay retain certainty and those meanings.

A model citation containing `source_timestamp`, an invented reference, a false
quote, or a supported answer with no evidence is rejected with no accepted event.
Missing `CreatedDate` or `ServiceInstant` fails even when an event/creation date
is present. Failed/repair/error events do not enter replay. A subsequent repaired
output enters only after it independently passes the same acceptance boundary.

## Nonclinical complete output

Municipal subject `PERMIT-71` contains notice reference `notice-0`, identity
`NOTICE-71`, text “permit issued”, `IssuedAt=2026-09-08T09:00:00Z`; receipt
reference `receipt-0`, identity `INTAKE-71`, text “notice indexed”,
`ProcessedAt=2026-09-09T14:00:00Z`. Building work occurrence is not supplied.
The revised wire is supported summary “The issued notice was indexed” with both
supplied citations. Final evidence has respectively `document_id=NOTICE-71`,
`timestamp_kind=document_issued` and `receipt_id=INTAKE-71`,
`timestamp_kind=processing`, using their separate authoritative timestamps.
There is no `clinical_note_key`, `CreatedDate` or `ServiceInstant` in this domain's
wire/final output. Processing cannot substitute for issuance. If the issuance
field is unavailable, that citation cannot be accepted, even though receipt
processing is known. An uncertain empty-evidence result remains a valid nonclaim.

## Verification boundary

The repository's `tests/test_prompt_backlog_methods.py` executes this fixture:
strict rejection, enrichment ownership, final shape, accepted-only exact-run replay,
downstream uncertainty, and logical identity/version/hash changes. Independent
held-out raw inputs and evaluator-only illustrative expectations live in the
repository evaluation corpus, not this distributed reference. Deterministic tests
establish these fixture consequences, not generation quality, real application
integration or model adherence. No live model evaluation is implied.
