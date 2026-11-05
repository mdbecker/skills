"""Small fictional saved-evidence projects; expectations live outside this builder."""

from copy import deepcopy
import hashlib
import html
import importlib.util
import inspect
import json
from pathlib import Path
import sys


REPOSITORY = Path(__file__).resolve().parents[2]
PROFILES = {
    "fictional-reliability": "Fictional service-reliability reference report",
    "reliability-study": "Fictional reliability transfer report",
}

ASSEMBLER_SOURCE = '''import html
import json
from pathlib import Path


def assemble(root, staged, correction=False, fail=False, svg=None):
    root = Path(root)
    evidence = json.loads((root / "evidence/cohorts.json").read_text())
    presentation = json.loads((root / "presentation.json").read_text())
    public_policy = json.loads((root / "public-policy.json").read_text())
    ledger = json.loads((root / "ledger.json").read_text())
    if correction:
        corrected = json.loads((root / "evidence/correction.json").read_text())
        ledger[0]["value"] = corrected["A"]["numerator"]
        evidence["A"]["numerator"] = corrected["A"]["numerator"]
    rows = []
    for entry in ledger:
        value = entry["value"]
        rendered = "Unavailable" if value is None else (
            json.dumps(value, sort_keys=True) if isinstance(value, dict) else str(value))
        status = entry["status"]
        if entry["id"] in public_policy["additional_withheld"]:
            rendered = "Withheld (complementary disclosure)"
            status = "withheld-complementary"
        rows.append('<tr data-evidence="' + entry["id"] + '"><th scope="row">' +
                    html.escape(entry["id"]) + '</th><td class="value">' +
                    html.escape(rendered) + '</td><td class="denominator">' +
                    str(entry["denominator"]) + '</td><td class="status">' +
                    status + '</td></tr>')
    bars = []
    for cohort in ("A", "B"):
        record = evidence[cohort]
        percentage = format(record["numerator"] / record["denominator"] * 100, ".4f").rstrip("0").rstrip(".")
        label = "Cohort " + cohort + " — " + record["selection"] + " — " + str(record["numerator"]) + "/" + str(record["denominator"]) + " (" + percentage + "%)"
        bars.append('<div class="cohort-bar" data-cohort="' + cohort + '"><p class="bar-label">' + html.escape(label) + '</p><div class="bar-track"><span class="bar" style="width:' + percentage + '%" aria-hidden="true"></span></div></div>')
    graph = json.loads((root / "diagrams/workflow.json").read_text())
    labels = {node["id"]: node["label"] for node in graph["nodes"]}
    equivalent = "".join("<li>" + html.escape(labels[edge["from"]] + " → " +
                       labels[edge["to"]] + ": " + edge["label"] + " (" +
                       edge["kind"] + ")") + "</li>" for edge in graph["edges"])
    archive = json.loads((root / "evidence/archive.json").read_text())
    css = ":root{--ink:" + presentation["palette"][0] + ";--accent:" + presentation["palette"][1] + "}"
    output = (root / "templates/report.html").read_text()
    replacements = {
        "{{TITLE}}": html.escape(evidence["title"]),
        "{{STYLE}}": css,
        "{{ROWS}}": "".join(rows),
        "{{BARS}}": "".join(bars),
        "{{DIAGRAM}}": svg or (root / "diagrams/workflow.svg").read_text(),
        "{{DIAGRAM_TEXT}}": equivalent,
        "{{ARCHIVE}}": html.escape(archive["text"]),
        "{{COHORT_SUMMARY}}": "Cohort A is " + evidence["A"]["selection"] + " (" +
            str(evidence["A"]["numerator"]) + "/" + str(evidence["A"]["denominator"]) +
            "); cohort B is " + evidence["B"]["selection"] + " (" +
            str(evidence["B"]["numerator"]) + "/" + str(evidence["B"]["denominator"]) +
            "). Different selections do not establish improvement.",
    }
    for marker, value in replacements.items():
        output = output.replace(marker, value)
    Path(staged).write_text(output, encoding="utf-8")
    if fail:
        raise RuntimeError("synthetic assembler failure after staging")
    return {"status": "completed", "presentation": presentation}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Assemble the existing fictional saved-evidence fixture into a staged file")
    parser.add_argument("--output", required=True)
    parser.add_argument("--correction", action="store_true")
    parser.add_argument("--fail", action="store_true")
    arguments = parser.parse_args()
    project = Path(__file__).resolve().parents[1]
    destination = Path(arguments.output)
    if not destination.is_absolute():
        destination = project / destination
    if destination.is_symlink() or not destination.resolve().is_relative_to(project) or destination == project / "report.html":
        parser.error("--output must be a staged regular file within this fixture, not the live report")
    print(json.dumps(assemble(project, destination, arguments.correction, arguments.fail), sort_keys=True))
'''

CHECKER_SOURCE = '''import html
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import re


class RenderedEvidence(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.rows = {}
        self.identity = None
        self.cell = None
        self.cells = []
        self.text = ""
        self.row_attributes = []
        self.in_diagram = False
        self.in_item = False
        self.diagram_text = []
        self.item = ""
        self.in_cohorts = False
        self.cohort_summary = ""
        self.bars = {}
        self.bar_cohort = None
        self.in_bar_label = False
        self.public_strings = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        self.public_strings.extend(value for name, value in attrs if value is not None)
        if "data-evidence" in attributes:
            if tag != "tr" or self.identity is not None or set(attributes) != {"data-evidence"}:
                raise ValueError("Evidence may only be encoded in its approved table row")
            self.identity = attributes["data-evidence"]
            if self.identity in self.rows:
                raise ValueError("Duplicate rendered evidence")
            self.cells = []
            self.row_attributes = []
        elif self.identity is not None:
            if tag not in {"th", "td"} or self.cell is not None:
                raise ValueError("Unapproved bar, percentage, tooltip or embedded encoding")
            expected = {"scope": "row"} if tag == "th" else {"class": (
                "value" if len(self.cells) == 1 else "denominator" if len(self.cells) == 2 else "status")}
            if attributes != expected:
                raise ValueError("Unapproved row attributes or indirect disclosure")
            self.cell = tag
            self.text = ""
        if attributes.get("id") == "diagram-text":
            self.in_diagram = True
        if attributes.get("id") == "cohort-summary":
            self.in_cohorts = True
        if "data-cohort" in attributes:
            if attributes != {"class": "cohort-bar", "data-cohort": attributes["data-cohort"]} or attributes["data-cohort"] in self.bars:
                raise ValueError("Duplicate or unapproved graphical cohort encoding")
            self.bar_cohort = attributes["data-cohort"]
            self.bars[self.bar_cohort] = {"label": "", "width": None}
        if attributes.get("class") == "bar-label":
            if self.bar_cohort is None or attributes != {"class": "bar-label"}:
                raise ValueError("Unapproved graphical label")
            self.in_bar_label = True
        if attributes.get("class") == "bar":
            if self.bar_cohort is None or set(attributes) != {"class", "style", "aria-hidden"} or attributes["aria-hidden"] != "true":
                raise ValueError("Unapproved graphical bar or tooltip")
            if self.bars[self.bar_cohort]["width"] is not None or not attributes["style"].startswith("width:"):
                raise ValueError("Duplicate or unapproved bar width")
            self.bars[self.bar_cohort]["width"] = attributes["style"][6:]
        if self.in_diagram and tag == "li":
            self.in_item = True
            self.item = ""

    def handle_data(self, data):
        self.public_strings.append(data)
        if self.cell is not None:
            self.text += data
        if self.in_item:
            self.item += data
        if self.in_cohorts:
            self.cohort_summary += data
        if self.in_bar_label:
            self.bars[self.bar_cohort]["label"] += data

    def handle_endtag(self, tag):
        if self.cell == tag:
            self.cells.append(self.text)
            self.cell = None
        if tag == "tr" and self.identity is not None:
            if len(self.cells) != 4:
                raise ValueError("Missing rendered value, denominator or status")
            self.rows[self.identity] = self.cells
            self.identity = None
        if tag == "li" and self.in_item:
            self.diagram_text.append(self.item)
            self.in_item = False
        if tag == "ul" and self.in_diagram:
            self.in_diagram = False
        if tag == "p" and self.in_cohorts:
            self.in_cohorts = False
        if tag == "p" and self.in_bar_label:
            self.in_bar_label = False


def check(root, staged, correction=False):
    root = Path(root)
    evidence = json.loads((root / "evidence/cohorts.json").read_text())
    if correction:
        evidence["A"]["numerator"] = json.loads((root / "evidence/correction.json").read_text())["A"]["numerator"]
    expected = {
        "cohort-a": (evidence["A"]["numerator"], evidence["A"]["denominator"], "exact"),
        "cohort-b": (evidence["B"]["numerator"], evidence["B"]["denominator"], "exact"),
        "partition-total": (evidence["partition"]["total"], 20, "exact"),
        "partition-disclosed": (evidence["partition"]["disclosed"], 20, "exact"),
        "partition-suppressed": (evidence["partition"]["suppressed"], 20, "suppressed"),
        "unavailable-intersection": (evidence["intersection"], 120, "unavailable"),
        "established-zero": (evidence["established_zero"], 120, "exact"),
        "blank-cell": (evidence["blank"], 120, "unavailable"),
        "labeled-aggregate": (evidence["labeled_aggregate"], 24, "reconstructed"),
        "overlap-first": (evidence["overlap"][0]["count"], evidence["overlap"][0]["denominator"], "exact"),
        "overlap-second": (evidence["overlap"][1]["count"], evidence["overlap"][1]["denominator"], "exact"),
        "diagnostic-first": (json.loads((root / "evidence/diagnostic-first.json").read_text())["saved"], 120, "disputed"),
        "diagnostic-second": (json.loads((root / "evidence/diagnostic-second.json").read_text())["saved"], 120, "disputed"),
    }
    public_policy = json.loads((root / "public-policy.json").read_text())
    withheld_values = [expected[identity][0] for identity in public_policy["additional_withheld"]]
    for identity in public_policy["additional_withheld"]:
        expected[identity] = ("Withheld (complementary disclosure)", expected[identity][1], "withheld-complementary")
    parser = RenderedEvidence()
    content = Path(staged).read_text()
    parser.feed(content)
    parser.close()
    if parser.identity is not None or set(parser.rows) != set(expected):
        raise ValueError("Rendered charts silently omit or add evidence")
    for identity, (value, denominator, status) in expected.items():
        rendered = "Unavailable" if value is None else (
            json.dumps(value, sort_keys=True) if isinstance(value, dict) else str(value))
        if parser.rows[identity] != [identity, rendered, str(denominator), status]:
            raise ValueError("Rendered value, row denominator or status differs: " + identity)
    summary = "Cohort A is " + evidence["A"]["selection"] + " (" + str(evidence["A"]["numerator"]) + "/" + str(evidence["A"]["denominator"]) + "); cohort B is " + evidence["B"]["selection"] + " (" + str(evidence["B"]["numerator"]) + "/" + str(evidence["B"]["denominator"]) + "). Different selections do not establish improvement."
    if parser.cohort_summary != summary:
        raise ValueError("Rendered cohort meaning or counts differ from saved evidence")
    expected_bars = {}
    for cohort in ("A", "B"):
        record = evidence[cohort]
        percentage = format(record["numerator"] * 100 / record["denominator"], ".4f").rstrip("0").rstrip(".")
        expected_bars[cohort] = {"label": "Cohort " + cohort + " — " + record["selection"] + " — " + str(record["numerator"]) + "/" + str(record["denominator"]) + " (" + percentage + "%)", "width": percentage + "%"}
    if parser.bars != expected_bars:
        raise ValueError("Graphical cohort bar width, percentage, denominator or label differs")
    for value in withheld_values:
        forbidden = r"(?<![0-9.])" + re.escape(str(value)) + r"(?:[.]0+)?(?![0-9.])"
        if any(re.search(forbidden, text) for text in parser.public_strings):
            raise ValueError("Complementary withheld value leaked through public text, attributes or embedded data")
    graph = json.loads((root / "diagrams/workflow.json").read_text())
    labels = {node["id"]: node["label"] for node in graph["nodes"]}
    equivalent = [labels[edge["from"]] + " → " + labels[edge["to"]] + ": " +
                  edge["label"] + " (" + edge["kind"] + ")" for edge in graph["edges"]]
    if parser.diagram_text != equivalent:
        raise ValueError("Diagram text equivalent lost a connection")
    for marker in ("{{", "synthetic-private-", "synthetic record text"):
        if marker in content:
            raise ValueError("Unresolved template or record-level disclosure")
    return {"status": "completed", "rows": len(parser.rows), "bars": len(parser.bars),
            "evidence": "Parsed graphical bar widths and labels, table values/denominators/statuses and diagram text against saved sources"}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Check the existing fictional saved-evidence report")
    parser.add_argument("--output", default="report.html")
    parser.add_argument("--correction", action="store_true")
    arguments = parser.parse_args()
    project = Path(__file__).resolve().parents[1]
    destination = Path(arguments.output)
    if not destination.is_absolute():
        destination = project / destination
    if destination.is_symlink() or not destination.resolve().is_relative_to(project) or not destination.is_file():
        parser.error("--output must name a regular file inside this fixture")
    print(json.dumps(check(project, destination, arguments.correction), sort_keys=True))
'''

FIXTURE_README = '''# Fictional saved-evidence maintenance fixture

This fixture defines saved inputs, an existing builder and independent acceptance checks.
Python 3 and its standard library are the only dependencies. No notebooks, data retrieval,
model calls, source-project files, package installation or deployment are needed.

`evidence/cohorts.json` and the two independent diagnostic artifacts are authoritative.
`ledger.json` is the protected checkpoint, not the source of rendered-value expectations.
`evidence/correction.json` supports only A's numerator changing from 24 to 25; it does
not authorize changing selection, denominator, disputed evidence or suppressed values.

The existing graph and argument vectors are recorded in `build.json`. From this folder:

    python3 scripts/assemble_report.py --output .report-staged.html
    python3 scripts/check_report.py --output .report-staged.html

For diagram-source presentation edits, `build.json` maps the existing command:

    python3 scripts/render_diagram.py --source diagrams/workflow.json --asset diagrams/workflow.svg --manifest diagrams/manifest.json

Retain the independent decision/loop/optional-edge contract and verify regenerated hashes.

For the explicit supported correction, add `--correction` to both commands. To exercise
the failed-build scenario, add `--fail` to the assembler. The assembler writes only
the staged file; the seeded `report.html` is the prior checkpoint and must remain intact
until the maintained transactional helper authorizes an atomic replacement. Never run
the assembler against that live output. Templates and `presentation.json` are editable;
diagram source/asset hashes must stay paired. Runtime inputs and error messages are not
historical fixed prompt text and must not be embedded in output.

For report maintenance load the research skill's evidence, disclosure, archives, diagrams
and rebuilding references and use its bounded count/JSON-pointer helper around these
existing commands. This fixture does not implement arbitrary-format extraction. Missing
dependencies block the affected operation rather than silently omitting sections.

Counts, statuses and row-specific denominators are checked in the rendered chart table.
Two horizontal bars show within-cohort proportions, with exact count/denominator,
selection and percentage text equivalents; their actual width styles are checked.
No bars or percentages are used for suppressed or unavailable cells. Diagram connections
Saved total 20, disclosed 15 and suppressed '<11' remain in the internal evidence and
ledger, but public-policy.json additionally withholds the disclosed cell to prevent
recovering the suppressed remainder. Public text, tooltips and embedded data must not
reintroduce that internal value. Internal ledgers are not publication artifacts.
have a meaningful text equivalent. Static checks do not certify keyboard behavior,
narrow-layout rendering, readable print, browser console/offline behavior, independent
agent execution or scientific validity; report those separately as not run.
'''

TEMPLATE = '''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{{TITLE}}</title><style>{{STYLE}}
body{color:var(--ink);font-family:system-ui;margin:1rem;max-width:60rem}
.table-scroll,.diagram-viewport{overflow-x:auto}table{border-collapse:collapse}th,td{padding:.4rem;text-align:left}
.bar-track{width:100%;background:#eee}.bar{display:block;height:1rem;background:var(--accent)}
@media print{details>div{display:block}body{font-size:11pt}}
</style></head><body><h1>{{TITLE}}</h1>
<nav aria-label="Report contents"><a href="#chart">Chart table</a> · <a href="#workflow">Workflow</a> · <a href="#archive">Archive</a></nav>
<section id="chart"><h2>Saved aggregate chart: exact text labels</h2>
<p id="cohort-summary">{{COHORT_SUMMARY}}</p>
<figure id="cohort-bars" aria-labelledby="cohort-bars-heading"><h3 id="cohort-bars-heading">Within-cohort saved proportions</h3>{{BARS}}<figcaption>Each width is numerator divided by its own cohort denominator; differently selected cohorts are not evidence of improvement. Exact labels are the text equivalent.</figcaption></figure>
<div class="table-scroll" tabindex="0" role="region" aria-label="Saved chart table"><table><caption>Values and row-specific denominators; overlapping rows must not be summed</caption>
<thead><tr><th>Saved claim</th><th>Value</th><th>Denominator</th><th>Status</th></tr></thead><tbody>{{ROWS}}</tbody></table></div>
<p>Suppressed cells remain nonnumeric: do not infer remainders by subtraction. The intersection is unavailable, not zero.</p>
<p>Conflicting saved definitions are retained in separate rows; neither is silently reconciled.</p></section>
<section id="workflow"><h2>Saved decision workflow</h2><div class="diagram-viewport" tabindex="0" role="region" aria-label="Scrollable decision diagram">{{DIAGRAM}}</div>
<details><summary>Read diagram as text</summary><div><ul id="diagram-text">{{DIAGRAM_TEXT}}</ul></div></details></section>
<section id="archive"><h2>Historical archive: partial excerpt</h2><p>The original wrapper is unavailable. This is not an exact complete prompt.</p><pre id="archive-excerpt">{{ARCHIVE}}</pre>
<p>Fixed excerpt, runtime inputs and saved error messages have separate source artifacts.</p></section>
</body></html>
'''


RENDERER_MAIN = '''
if __name__ == "__main__":
    import argparse
    import hashlib
    import json
    from pathlib import Path
    parser = argparse.ArgumentParser(description="Regenerate the existing fictional decision diagram")
    parser.add_argument("--source", required=True)
    parser.add_argument("--asset", required=True)
    parser.add_argument("--manifest", required=True)
    arguments = parser.parse_args()
    project = Path(__file__).resolve().parents[1]
    paths = []
    for relative in (arguments.source, arguments.asset, arguments.manifest):
        path = project / relative
        if Path(relative).is_absolute() or ".." in Path(relative).parts or not path.resolve().is_relative_to(project):
            parser.error("Diagram paths must remain inside this fixture")
        if any(part.is_symlink() for part in (path, *path.parents) if part.is_relative_to(project)):
            parser.error("Diagram paths must not use symlinks")
        paths.append(path)
    source, asset, manifest = paths
    if len(set(paths)) != 3:
        parser.error("Source, asset and manifest must be distinct paths")
    original = source.read_bytes()
    output = _svg(json.loads(original)).encode("utf-8")
    if source.read_bytes() != original:
        raise RuntimeError("Concurrent diagram-source change")
    record = {"source": {"artifact": arguments.source, "sha256": hashlib.sha256(original).hexdigest()},
              "asset": {"artifact": arguments.asset, "sha256": hashlib.sha256(output).hexdigest()}}
    asset.write_bytes(output)
    manifest.write_text(json.dumps(record, indent=2, sort_keys=True) + "\\n", encoding="utf-8")
    print(json.dumps({"status": "completed", "manifest": record}, sort_keys=True))
'''


def _write_json(root, relative, value):
    target = root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _source(root, artifact, locator):
    return {"artifact": artifact, "version": "synthetic-saved-v1",
            "sha256": hashlib.sha256((root / artifact).read_bytes()).hexdigest(),
            "locator": locator}


def _svg(graph):
    nodes = "".join('<text id="node-' + node["id"] + '" x="10" y="' +
                    str(30 + index * 30) + '">' + html.escape(node["label"]) + '</text>'
                    for index, node in enumerate(graph["nodes"]))
    edges = "".join('<text x="250" y="' + str(30 + index * 30) + '">' +
                    html.escape(edge["from"] + " → " + edge["to"] + ": " +
                                edge["label"] + " (" + edge["kind"] + ")") + '</text>'
                    for index, edge in enumerate(graph["edges"]))
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 700 250">'
            '<title id="title">Saved decision workflow</title><desc id="description">'
            'Yes and No decision branches, a review loop and an optional proposed route.</desc>'
            '<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5">'
            '<path d="M0 0 L10 5 L0 10 Z"/></marker></defs>'
            '<path d="M10 200 L500 200" marker-end="url(#arrow)"/>' + nodes + edges + '</svg>')


def _load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    previous = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous
    return module


def create_fixture(root, profile="reliability-study"):
    """Materialize a bounded saved project without importing the candidate helper."""
    root = Path(root)
    if profile not in PROFILES:
        raise ValueError("Unknown fictional fixture profile")
    if root.is_symlink() or (root.exists() and any(root.iterdir())):
        raise ValueError("Fixture needs an empty nonsymlink directory")
    root.mkdir(parents=True, exist_ok=True)
    evidence = {
        "profile": profile, "title": PROFILES[profile],
        "A": {"cohort": "A", "selection": "random", "numerator": 24, "denominator": 120},
        "B": {"cohort": "B", "selection": "targeted", "numerator": 16, "denominator": 40},
        "partition": {"total": 20, "disclosed": 15, "suppressed": "<11"},
        "intersection": None, "established_zero": 0, "blank": None, "labeled_aggregate": 7,
        "overlap": [{"count": 8, "denominator": 24}, {"count": 9, "denominator": 16}],
    }
    _write_json(root, "evidence/cohorts.json", evidence)
    _write_json(root, "evidence/correction.json", {"A": {"numerator": 25, "denominator": 120}})
    _write_json(root, "evidence/diagnostic-first.json", {"saved": {"definition": "distinct selected service-days", "count": 17}})
    _write_json(root, "evidence/diagnostic-second.json", {"saved": {"definition": "saved dashboard events including repeats", "count": 19}})
    _write_json(root, "evidence/archive.json", {"kind": "partial-excerpt", "text": "Keep the saved selection labels.", "complete": False})
    (root / "evidence/archive.py").write_text('EXCERPT = "Keep the saved selection labels."\n', encoding="utf-8")
    _write_json(root, "evidence/runtime-inputs.json", {"subject": "synthetic-private-runtime", "text": "synthetic record text"})
    _write_json(root, "evidence/error-messages.json", {"saved": "Synthetic missing wrapper diagnostic"})
    _write_json(root, "evidence/spatial.json", [
        {"subject": "synthetic-private-" + str(index), "coordinates": [1.23456, 2.34567]}
        for index in range(24)])
    _write_json(root, "presentation.json", {"palette": ["#17324d", "#3d75a5"], "marker_encoding": "area=count", "mixed_group_encoding": "group-opacity-not-severity"})
    _write_json(root, "public-policy.json", {"complementary_disclosure": "withhold-partition", "protected": "partition-suppressed", "additional_withheld": ["partition-disclosed"]})
    graph = {"nodes": [{"id": "saved", "label": "Read saved evidence"},
                        {"id": "decision", "label": "Source supports change?"},
                        {"id": "review", "label": "Review staged output"},
                        {"id": "done", "label": "Keep prior report or replace safely"}],
             "edges": [{"from": "saved", "to": "decision", "label": "Inspect", "kind": "required"},
                       {"from": "decision", "to": "review", "label": "Yes", "kind": "decision"},
                       {"from": "decision", "to": "done", "label": "No", "kind": "decision"},
                       {"from": "review", "to": "decision", "label": "Revise", "kind": "loop"},
                       {"from": "review", "to": "done", "label": "Additional review", "kind": "optional"}]}
    _write_json(root, "diagrams/workflow.json", graph)
    (root / "diagrams/workflow.svg").write_text(_svg(graph), encoding="utf-8")
    _write_json(root, "diagrams/manifest.json", {
        "source": {"artifact": "diagrams/workflow.json", "sha256": hashlib.sha256((root / "diagrams/workflow.json").read_bytes()).hexdigest()},
        "asset": {"artifact": "diagrams/workflow.svg", "sha256": hashlib.sha256((root / "diagrams/workflow.svg").read_bytes()).hexdigest()},
    })
    definitions = [
        ("cohort-a", "/A/numerator", 24, 120, "A", "random", "exact"),
        ("cohort-b", "/B/numerator", 16, 40, "B", "targeted", "exact"),
        ("partition-total", "/partition/total", 20, 20, "partition", "saved-partition", "exact"),
        ("partition-disclosed", "/partition/disclosed", 15, 20, "partition", "saved-partition", "exact"),
        ("partition-suppressed", "/partition/suppressed", "<11", 20, "partition", "saved-partition", "suppressed"),
        ("unavailable-intersection", "/intersection", None, 120, "A", "random", "unavailable"),
        ("established-zero", "/established_zero", 0, 120, "A", "random", "exact"),
        ("blank-cell", "/blank", None, 120, "A", "random", "unavailable"),
        ("labeled-aggregate", "/labeled_aggregate", 7, 24, "A", "random", "reconstructed"),
        ("overlap-first", "/overlap/0/count", 8, 24, "overlapping-first", "overlapping-group", "exact"),
        ("overlap-second", "/overlap/1/count", 9, 16, "overlapping-second", "overlapping-group", "exact"),
    ]
    ledger = []
    for identity, locator, value, denominator, cohort, selection, status in definitions:
        ledger.append({"id": identity, "source": _source(root, "evidence/cohorts.json", locator),
                       "cohort": cohort, "selection": selection, "unit": "saved service-day observations",
                       "denominator": denominator,
                       "derivation": "legible saved label" if status == "reconstructed" else "printed saved aggregate; overlapping rows not additive",
                       "value": value, "status": status, "editable_source": "templates/report.html",
                       "output_location": "report.html#chart", "permitted_change": "layout; explicit saved-source correction of value/source only",
                       "verification": {"status": "not-run", "evidence": None}})
    for suffix in ("first", "second"):
        artifact = "evidence/diagnostic-" + suffix + ".json"
        record = deepcopy(ledger[0])
        record.update(id="diagnostic-" + suffix, source=_source(root, artifact, "/saved"),
                      value=json.loads((root / artifact).read_text())["saved"], status="disputed",
                      derivation="conflicting saved definition retained, not silently reconciled")
        ledger.append(record)
    _write_json(root, "ledger.json", ledger)
    _write_json(root, "corrections.json", [{"id": "cohort-a", "before_value": 24, "after_value": 25,
                                           "source": _source(root, "evidence/correction.json", "/A/numerator")}])
    for relative, content in (("scripts/assemble_report.py", ASSEMBLER_SOURCE),
                              ("scripts/check_report.py", CHECKER_SOURCE),
                              ("scripts/render_diagram.py", "import html\n\n" + inspect.getsource(_svg) + RENDERER_MAIN),
                              ("templates/report.html", TEMPLATE),
                              ("README.md", FIXTURE_README)):
        (root / relative).parent.mkdir(parents=True, exist_ok=True)
        (root / relative).write_text(content, encoding="utf-8")
    sources = sorted(str(path.relative_to(root)) for path in root.rglob("*") if path.is_file())
    _write_json(root, "build.json", {"sources": sources, "output": "report.html",
                                    "assembler": "scripts/assemble_report.py", "checker": "scripts/check_report.py",
                                    "assembly_argv": ["python3", "scripts/assemble_report.py", "--output", "{staged}"],
                                    "check_argv": ["python3", "scripts/check_report.py", "--output", "{staged}"],
                                    "regenerate_argv": ["python3", "scripts/render_diagram.py", "--source", "diagrams/workflow.json", "--asset", "diagrams/workflow.svg", "--manifest", "diagrams/manifest.json"]})
    assembler = _load_module(root / "scripts/assemble_report.py", "synthetic_assembler")
    assembler.assemble(root, root / "report.html")
    return root


def run_task(root, correction=False, fail=False):
    """Exercise the existing tiny fixture graph through the maintained checks."""
    root = Path(root)
    checks = _load_module(REPOSITORY / "research/scripts/report_checks.py", "fixture_report_checks")
    mapping = json.loads((root / "build.json").read_text())
    for relative in ["build.json", mapping["assembler"], mapping["checker"], *mapping["sources"]]:
        checks.bounded_path(root, relative)
    assembler = _load_module(root / mapping["assembler"], "synthetic_assembler")
    checker = _load_module(root / mapping["checker"], "synthetic_checker")
    before = json.loads((root / "ledger.json").read_text())
    after = deepcopy(before)
    corrections = json.loads((root / "corrections.json").read_text()) if correction else []
    if correction:
        after[0].update(value=corrections[0]["after_value"], source=corrections[0]["source"])
    checks.compare_ledger(before, after, root, corrections)
    manifest = json.loads((root / "diagrams/manifest.json").read_text())
    svg = checks.namespace_svg(checks.checked_asset(root, manifest), "maintained-workflow")
    archive = json.loads((root / "evidence/archive.json").read_text())
    checks.archive_record(archive["text"], archive["kind"], complete=archive["complete"])
    result = checks.transactional_build(root, [*mapping["sources"], "build.json"], mapping["output"],
        lambda staged: assembler.assemble(root, staged, correction=correction, fail=fail, svg=svg),
        [lambda staged: checker.check(root, staged, correction=correction),
         lambda staged: checks.inspect_html(staged.read_text())])
    for entry in after:
        entry["verification"] = {"status": "completed", "evidence": "Saved-source comparison and rendered table comparison"}
    _write_json(root, "ledger.after.json", after)
    result.update(profile=json.loads((root / "evidence/cohorts.json").read_text())["profile"],
                  ledger=after, archive=archive,
                  presentation=json.loads((root / "presentation.json").read_text()),
                  verification={"assembly": {"status": "completed", "evidence": result["output_sha256"]},
                                "rendered-evidence": result["checks"][0],
                                "static-html": result["checks"][1],
                                "visual-inspection": {"status": "not-run", "evidence": None},
                                "keyboard-browser": {"status": "not-run", "evidence": None},
                                "narrow-print-browser": {"status": "not-run", "evidence": None},
                                "independent-agent": {"status": "not-run", "evidence": None}})
    return result
