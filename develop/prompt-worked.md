# Worked coordinated prompt edit

## Contents

- [Scope and baseline](#scope-and-baseline)
- [Coordinated edits](#coordinated-edits)
- [Independently fictional application-owned mappings](#independently-fictional-application-owned-mappings)
- [Executable fictional fixture](#executable-fictional-fixture)
- [Complete observations and failure paths](#complete-observations-and-failure-paths)
- [Verification boundary](#verification-boundary)

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
{"summary":"The document records a delayed handoff.","certainty":"supported","evidence":[{"source":"notice","reference":"notice-alpha","quote":"handoff delayed"}]}
```

```json
{"summary":"The cause cannot be established from supplied material.","certainty":"uncertain","evidence":[]}
```

The TL;DR contract is: “Replay accepted summary, certainty and verified evidence
identities/timestamp meanings only. Preserve uncertainty for downstream reasoning.”
None of these model-facing resources delegates timestamp ownership to the model.

## Independently fictional application-owned mappings

The fictional document-processing and equipment examples define distinct identity,
source-time and acceptance contracts. The fixture owns these policies only;
the target's current contract always wins.

| Profile / source | Canonical identity | Authoritative time | Different meaning |
|---|---|---|---|
| documents / notice | document_key -> document_id, exact string | issued_at -> document_issued | occurrence_at is not document issuance. |
| documents / receipt | receipt_key -> receipt_id, positive integer | received_at -> document_received | processed_at is later processing, not receipt. |
| equipment / notice | DocumentId -> document_id, exact string | IssuedAt -> document_issued | Receipt processing is separate. |
| equipment / receipt | ReceiptId -> receipt_id, exact string | ProcessedAt -> processing | Processing does not establish issuance. |

Application context supplies canonical metadata. The model can select only a
supplied source/reference and returns no application-owned fields. Unknown identity,
missing authoritative time or forged enrichment fails before any accepted event.
There is no shared universal source schema or default null/link field.

## Executable fictional fixture

Exact substring checking is a deliberately strict fixture policy. It is not a
replacement for a target's redaction/reconciliation/fuzzy-match order or a claim
that accepted evidence is adjudicated interpretation. A target may retain explicitly
unverified evidence only under its actual contract. No model/data calls occur here.

```python
import hashlib
import json
from datetime import datetime


PROFILES = {
    "documents": {
        "notice": ("document_key", "document_id", str, "issued_at", "document_issued"),
        "receipt": ("receipt_key", "receipt_id", int, "received_at", "document_received"),
    },
    "equipment": {
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

## Complete observations and failure paths

For documents, notice-alpha has document_key DOC-ORBIT, text "handoff delayed",
issued_at 2026-10-04T10:00:00Z and occurrence_at 2026-10-03T08:00:00Z. Receipt-beta
has receipt_key 208, text "review completed", received_at 2026-10-04T11:00:00Z and
processed_at 2026-10-05T12:00:00Z. Application subject DOCUMENT-ORBIT accepts supplied
citations with document_id or receipt_id and their separate authoritative meanings.
No linked receipt field is added to a notice, and no time is inferred from its quote.

The equipment profile uses independent string IDs for documents and receipts. Its
fixture wire/final contract differs from documents' numeric receipt key. Missing
issuance cannot be filled by a known processing time. An uncertain empty-evidence
result is a valid nonclaim; a supported result requires accepted supplied evidence.

Both profiles reject forged timestamps, extra/coerced fields, unknown references,
false quotes and malformed accepted events. Failed/repair events stay out of exact
run/step replay. Only independently accepted outputs enter display and compact
replay. Every model-visible surface advances the registered logical identity/hash;
resource filenames stay stable under the mapped contract.

## Verification boundary

`tests/test_prompt_backlog_methods.py` exercises actual fixture rejection, canonical
metadata enrichment, final shape, uncertainty, accepted-only exact-run replay and
logical version/hash. Held-out fictional cases and evaluator-only expectations are
not package dependencies. Deterministic results do not certify generation quality,
real project integration, host invocation or agent adherence.
