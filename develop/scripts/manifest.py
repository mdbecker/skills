#!/usr/bin/env python3
"""Project-local feature state CLI for Develop's feedback-driven approach.

Run this terminal helper from the project being developed, using its installed
absolute path. Assistant slash requests have different instruction grammar.
Feature IDs such as csv-import are chosen names for .ai-state/<id>.json, not
built-in features. Status/list only read; phase/park/set change explicitly
selected state. Implicit status selects file modification time, not conversation.

Usage examples:
  manifest.py init csv-import --impact "Users upload a CSV and see rows in the dashboard"
  manifest.py status [csv-import]
  manifest.py phase csv-import TWEAKING
  manifest.py park csv-import edge "malformed CSV input"
  manifest.py park csv-import hardening "size limit on uploads"
  manifest.py resolve csv-import edge 1
  manifest.py testbed csv-import add --label "start services" --cmd "docker compose up -d"
  manifest.py testbed csv-import list
  manifest.py decision csv-import --title "Storage" --context "..." --option "Postgres" --option "Redis" --decision "Postgres" --rationale "..."
  manifest.py set csv-import data_flow "CSV -> parser -> rows table"
"""

import argparse
import json
import os
import re
import tempfile
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

STATE_DIR = Path(".ai-state")
# Committed alongside the tools so future feature iterations can discover them.
TOOLS_REGISTRY = Path("testbed/tools/registry.json")
PHASES = ["ARCHITECTURE", "HAPPY_PATH", "TEST_BED", "TWEAKING", "TESTING", "FINALIZATION"]
PHASE_LABELS = {
    "ARCHITECTURE": "Agree direction", "HAPPY_PATH": "Minimal working flow",
    "TEST_BED": "Manual demonstration", "TWEAKING": "Refine with feedback",
    "TESTING": "Regression protection", "FINALIZATION": "Agreed follow-ups",
}

EXIT_CRITERIA = {
    "ARCHITECTURE": "unsettled choices compared, adequate plans reused, and user agrees on direction",
    "HAPPY_PATH": "primary flow code-complete against the recorded data flow",
    "TEST_BED": "test bed runs and happy path exercised at least once (pass or reproducible failure)",
    "TWEAKING": "user says the behavior feels right",
    "TESTING": "happy-path tests pass green from a clean environment",
    "FINALIZATION": "backlog fully resolved-or-waived and hardening checklist addressed",
}

BACKLOG_KEYS = {"edge": "edge_cases", "hardening": "hardening_tasks"}

BACKLOG_ITEM = {"description": str, "is_resolved": bool, "?waive_reason": str}
MANIFEST_SCHEMA = {
    "project_metadata": {
        "feature_name": str, "last_updated": str, "current_phase": tuple(PHASES),
        "?next_step": str,
        "?phase_history": [{"from": tuple(PHASES), "to": tuple(PHASES), "at": str,
                            "?commit": (str, type(None))}],
    },
    "core_objective": {"impact_target": str, "strict_scope_exclusions": [str]},
    "implementation_state": {
        "data_flow_description": str, "test_bed_environment": str,
        "happy_path_entry_points": [str],
        "?test_bed_commands": [{"label": str, "command": str}],
    },
    "deferred_backlog": {"edge_cases": [BACKLOG_ITEM], "hardening_tasks": [BACKLOG_ITEM]},
    "testing_strategy": {"target_execution_path": str, "required_integration_assertions": [str]},
    "architecture_decisions": [{"id": "positive integer", "title": str, "context": str,
                               "options_considered": [str], "decision_made": str, "rationale": str}],
}


def _validate_shape(value, schema, field):
    if isinstance(schema, dict):
        if not isinstance(value, dict):
            raise ValueError(f"{field}: expected an object")
        for declared, child_schema in schema.items():
            key = declared.removeprefix("?")
            child = key if field == "root" else f"{field}.{key}"
            if key not in value:
                if declared.startswith("?"):
                    continue
                raise ValueError(f"{child}: missing required key")
            _validate_shape(value[key], child_schema, child)
    elif isinstance(schema, list):
        if not isinstance(value, list):
            raise ValueError(f"{field}: expected a list")
        for index, child in enumerate(value):
            _validate_shape(child, schema[0], f"{field}[{index}]")
    elif isinstance(schema, tuple):
        if all(isinstance(option, type) for option in schema):
            valid = type(value) in schema
        else:
            valid = isinstance(value, str) and value in schema
        if not valid:
            raise ValueError(f"{field}: invalid type or phase")
    elif schema == "positive integer":
        if type(value) is not int or value < 1:
            raise ValueError(f"{field}: expected a positive integer")
    elif type(value) is not schema:
        raise ValueError(f"{field}: expected {schema.__name__}")


def validate_manifest(value):
    _validate_shape(value, MANIFEST_SCHEMA, "root")
    try:
        json.dumps(value, allow_nan=False)
    except (ValueError, TypeError, RecursionError) as error:
        raise ValueError("root: expected JSON-compatible values") from error
    pending = [value]
    while pending:
        item = pending.pop()
        if isinstance(item, dict):
            if any(type(key) is not str for key in item):
                raise ValueError("root: JSON object keys must be strings")
            pending.extend(item.values())
        elif isinstance(item, list):
            pending.extend(item)
        elif item is not None and type(item) not in (str, bool, int, float):
            raise ValueError("root: expected JSON-compatible values without coercion")
    return value


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _invalid_constant(value):
    raise ValueError("non-JSON numeric constant")


def _corrupt_manifest(path, error):
    die(f"manifest {path}: {error} — stop and preserve this file; "
        "ask the user to restore a known-good local copy or authorize a separate recovery procedure")


def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def die(msg):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)


def check_state_dir():
    if STATE_DIR.is_symlink():
        die(".ai-state/ must be a local directory, not a symlink")


def registry_path():
    project = Path.cwd().resolve()
    destination = project / TOOLS_REGISTRY
    current = project
    try:
        for component in TOOLS_REGISTRY.parts:
            current = current / component
            if current.is_symlink():
                die(f"unsafe registry storage {current}: symlinks are not allowed")
            if not current.resolve().is_relative_to(project):
                die(f"unsafe registry storage {current}: path must remain inside the project")
            if current.exists():
                if current == destination and not current.is_file():
                    die(f"unsafe registry storage {current}: registry must be an ordinary file")
                if current != destination and not current.is_dir():
                    die(f"unsafe registry storage {current}: ancestor must be a directory")
    except (OSError, RuntimeError) as error:
        die(f"unsafe registry storage {current}: {error}")
    return destination


def path_for(feature):
    check_state_dir()
    if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_-]*", feature):
        die("feature must contain only letters, digits, underscores, or hyphens and start with a letter or digit")
    path = STATE_DIR / f"{feature}.json"
    if path.is_symlink():
        die("manifest files must be local files, not symlinks")
    if path.resolve().parent != STATE_DIR.resolve():
        die("manifest path must remain inside .ai-state/")
    return path


def load(feature):
    p = path_for(feature)
    if not p.exists():
        die(f"no manifest at {p} — run: manifest.py init {feature} --impact \"...\"")
    try:
        m = json.loads(p.read_text(), object_pairs_hook=_unique_object, parse_constant=_invalid_constant)
        validate_manifest(m)
    except ValueError as error:
        _corrupt_manifest(p, error)
    return m


def git_sha():
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                              capture_output=True, text=True, timeout=5).stdout.strip() or None
    except Exception:
        return None


def atomic_write(path, text):
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                         delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def save(feature, m):
    path = path_for(feature)
    try:
        validate_manifest(m)
    except ValueError as error:
        _corrupt_manifest(path, error)
    m["project_metadata"]["last_updated"] = now()
    atomic_write(path, json.dumps(m, indent=2, allow_nan=False) + "\n")


def latest_feature():
    check_state_dir()
    files = sorted(STATE_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        die("no manifests in .ai-state/ — run: manifest.py init <feature> --impact \"...\"")
    return files[0].stem


def new_manifest(feature, impact):
    return {
        "project_metadata": {
            "feature_name": feature,
            "last_updated": now(),
            "current_phase": "ARCHITECTURE",
            "next_step": "",
            "phase_history": [],
        },
        "core_objective": {
            "impact_target": impact,
            "strict_scope_exclusions": [],
        },
        "architecture_decisions": [],
        "implementation_state": {
            "data_flow_description": "",
            "test_bed_environment": "",
            "test_bed_commands": [],
            "happy_path_entry_points": [],
        },
        "deferred_backlog": {"edge_cases": [], "hardening_tasks": []},
        "testing_strategy": {
            "target_execution_path": "",
            "required_integration_assertions": [],
        },
    }


def cmd_init(args):
    check_state_dir()
    STATE_DIR.mkdir(exist_ok=True)
    p = path_for(args.feature)
    if p.exists():
        die(f"{p} already exists")
    save(args.feature, new_manifest(args.feature, args.impact))
    print(f"initialized {p} in phase ARCHITECTURE")


def cmd_status(args):
    feature = args.feature or latest_feature()
    m = load(feature)
    meta, impl, backlog = m["project_metadata"], m["implementation_state"], m["deferred_backlog"]
    phase = meta["current_phase"]
    edges = backlog["edge_cases"]
    hard = backlog["hardening_tasks"]
    open_e = sum(1 for x in edges if not x.get("is_resolved"))
    open_h = sum(1 for x in hard if not x.get("is_resolved"))

    print(f"feature:      {feature}")
    print(f"phase:        {phase}")
    print(f"stage:        {PHASE_LABELS[phase]}")
    selection = "explicit feature" if args.feature else "most recent manifest by file modification time"
    print(f"selection:    {selection}")
    print(f"updated:      {meta['last_updated']}")
    print(f"impact:       {m['core_objective']['impact_target']}")
    if meta.get("next_step"):
        print(f"next step:    {meta['next_step']}")
    print(f"backlog:      {open_e} open edge cases, {open_h} open hardening tasks "
          f"({len(edges) + len(hard)} total)")
    print(f"decisions:    {len(m['architecture_decisions'])} recorded")
    if impl.get("data_flow_description"):
        print(f"data flow:    {impl['data_flow_description']}")
    if impl.get("happy_path_entry_points"):
        print(f"entry points: {', '.join(impl['happy_path_entry_points'])}")
    cmds = impl.get("test_bed_commands", [])
    if cmds:
        print("test bed:")
        for c in cmds:
            print(f"  [{c['label']}] {c['command']}")
    if impl.get("test_bed_environment"):
        print(f"test bed:     {impl['test_bed_environment']}")
    print(f"exit when:    {EXIT_CRITERIA[phase]}")
    if args.verbose:
        for kind, items in (("edge", edges), ("hardening", hard)):
            for i, x in enumerate(items, 1):
                mark = "x" if x.get("is_resolved") else " "
                note = f" (waived: {x['waive_reason']})" if x.get("waive_reason") else ""
                print(f"  [{mark}] {kind} #{i}: {x['description']}{note}")


def cmd_phase(args):
    m = load(args.feature)
    old = m["project_metadata"]["current_phase"]
    m["project_metadata"]["current_phase"] = args.phase
    entry = {"from": old, "to": args.phase, "at": now()}
    sha = git_sha()
    if sha:
        entry["commit"] = sha
    m["project_metadata"].setdefault("phase_history", []).append(entry)
    save(args.feature, m)
    suffix = f" (at commit {sha})" if sha else ""
    print(f"{old} -> {args.phase}{suffix}. exit when: {EXIT_CRITERIA[args.phase]}")


def cmd_list(args):
    check_state_dir()
    if not STATE_DIR.is_dir():
        die("no .ai-state/ directory here")
    rows = []
    for p in sorted(STATE_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        m = load(p.stem)
        b = m["deferred_backlog"]
        open_items = sum(1 for k in BACKLOG_KEYS.values() for x in b[k] if not x.get("is_resolved"))
        rows.append((p.stem, m["project_metadata"]["current_phase"],
                     m["project_metadata"]["last_updated"], str(open_items)))
    if not rows:
        print("(no manifests in .ai-state/)")
        return
    header = ("FEATURE", "PHASE", "UPDATED", "OPEN BACKLOG")
    widths = [max(len(r[i]) for r in rows + [header]) for i in range(4)]
    for r in [header] + rows:
        print("  ".join(v.ljust(w) for v, w in zip(r, widths)))


def cmd_park(args):
    m = load(args.feature)
    key = BACKLOG_KEYS[args.kind]
    m["deferred_backlog"][key].append({"description": args.description, "is_resolved": False})
    save(args.feature, m)
    print(f"parked: {args.kind} #{len(m['deferred_backlog'][key])}: {args.description}")


def _backlog_item(m, kind, index):
    items = m["deferred_backlog"][BACKLOG_KEYS[kind]]
    if not 1 <= index <= len(items):
        die(f"no {kind} item #{index} (have {len(items)})")
    return items[index - 1]


def cmd_resolve(args):
    m = load(args.feature)
    item = _backlog_item(m, args.kind, args.index)
    item["is_resolved"] = True
    item.pop("waive_reason", None)
    if args.waive:
        item["waive_reason"] = args.waive
    save(args.feature, m)
    verb = f"waived ({args.waive})" if args.waive else "resolved"
    print(f"{verb}: {args.kind} #{args.index}: {item['description']}")


def cmd_testbed(args):
    m = load(args.feature)
    cmds = m["implementation_state"].setdefault("test_bed_commands", [])
    if args.action == "remove":
        if not args.label or not any(c["label"] == args.label for c in cmds):
            die("testbed remove requires an existing --label")
        cmds[:] = [c for c in cmds if c["label"] != args.label]
        save(args.feature, m)
        print(f"removed [{args.label}]")
    elif args.action == "add":
        if not (args.label and args.cmd):
            die("testbed add requires --label and --cmd")
        replacement = {"label": args.label, "command": args.cmd}
        for index, command in enumerate(cmds):
            if command["label"] == args.label:
                cmds[index] = replacement
                # Older manifests may have duplicate labels; keep the first position.
                cmds[index + 1:] = [c for c in cmds[index + 1:]
                                   if c["label"] != args.label]
                break
        else:
            cmds.append(replacement)
        save(args.feature, m)
        print(f"recorded [{args.label}] {args.cmd}")
    else:  # list
        if not cmds:
            print("(no test bed commands recorded)")
        for c in cmds:
            print(f"[{c['label']}] {c['command']}")


def cmd_render(args):
    m = load(args.feature)
    meta, obj, impl = m["project_metadata"], m["core_objective"], m["implementation_state"]
    out = [f"# {meta['feature_name']} — architecture", ""]
    out += [f"*Phase: {meta['current_phase']} · updated {meta['last_updated']}*", ""]
    out += ["## Objective", "", obj["impact_target"], ""]
    if obj["strict_scope_exclusions"]:
        out += ["Explicitly out of scope:", ""]
        out += [f"- {x}" for x in obj["strict_scope_exclusions"]] + [""]
    if impl.get("data_flow_description"):
        out += ["## Data flow", "", impl["data_flow_description"], ""]
    if m["architecture_decisions"]:
        out += ["## Decisions", ""]
        for d in m["architecture_decisions"]:
            out += [f"### {d['id']}. {d['title']}", "", d["context"], ""]
            out += [f"- {'**' + o + '** ← chosen' if o == d['decision_made'] else o}"
                    for o in d["options_considered"]]
            if d["decision_made"] not in d["options_considered"]:
                out += [f"- **{d['decision_made']}** ← chosen"]
            out += ["", d["rationale"], ""]
    if impl.get("test_bed_environment"):
        out += ["## Test bed plan", "", impl["test_bed_environment"], ""]
    text = "\n".join(out)
    if args.out:
        Path(args.out).write_text(text)
        print(f"wrote {args.out} — generated artifact, do not commit")
    else:
        print(text)


def cmd_tool(args):
    reg = []
    if registry_path().exists():
        try:
            reg = json.loads(registry_path().read_text())
        except json.JSONDecodeError as e:
            die(f"corrupt registry {TOOLS_REGISTRY}: {e}")
    if args.action == "list":
        if not reg:
            print("(no registered test bed tools)")
        for t in reg:
            print(f"{t['name']}: {t['description']}")
            print(f"  path: {t['path']}   usage: {t.get('usage', '-')}   added by: {t.get('added_by', '-')}")
        return
    if args.action == "update":
        entry = next((t for t in reg if t["name"] == args.name), None)
        if entry is None:
            die("tool update requires an existing --name")
        if args.path is not None and not Path(args.path).exists():
            die(f"{args.path} does not exist")
        for field, value in (("path", args.path), ("description", args.desc), ("usage", args.usage)):
            if value is not None:
                entry[field] = value
        atomic_write(registry_path(), json.dumps(reg, indent=2) + "\n")
        print(f"updated tool '{args.name}'")
        return
    # add
    if not (args.name and args.path and args.desc):
        die("tool add requires --name, --path, --desc")
    if not Path(args.path).exists():
        die(f"{args.path} does not exist — move the tool into place first")
    if any(t["name"] == args.name for t in reg):
        die(f"tool '{args.name}' already registered")
    entry = {"name": args.name, "path": args.path, "description": args.desc,
             "usage": args.usage or "", "added_by": args.feature or "", "added_at": now()}
    reg.append(entry)
    registry_path().parent.mkdir(parents=True, exist_ok=True)
    atomic_write(registry_path(), json.dumps(reg, indent=2) + "\n")
    print(f"registered tool '{args.name}' ({args.path}) — remember to commit {TOOLS_REGISTRY.parent}/")


def cmd_decision(args):
    m = load(args.feature)
    decisions = m["architecture_decisions"]
    decisions.append({
        "id": len(decisions) + 1,
        "title": args.title,
        "context": args.context,
        "options_considered": args.option,
        "decision_made": args.decision,
        "rationale": args.rationale,
    })
    save(args.feature, m)
    print(f"recorded decision #{len(decisions)}: {args.title} -> {args.decision}")


SET_FIELDS = {
    "next_step": ("project_metadata", "next_step"),
    "impact": ("core_objective", "impact_target"),
    "data_flow": ("implementation_state", "data_flow_description"),
    "test_bed_env": ("implementation_state", "test_bed_environment"),
    "target_path": ("testing_strategy", "target_execution_path"),
}
APPEND_FIELDS = {
    "exclusion": ("core_objective", "strict_scope_exclusions"),
    "entry_point": ("implementation_state", "happy_path_entry_points"),
    "assertion": ("testing_strategy", "required_integration_assertions"),
}


def cmd_set(args):
    m = load(args.feature)
    if args.field in SET_FIELDS:
        section, key = SET_FIELDS[args.field]
        m[section][key] = args.value
    else:
        section, key = APPEND_FIELDS[args.field]
        m[section][key].append(args.value)
    save(args.feature, m)
    print(f"{args.field} = {args.value}")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser("init", help="create established new feature state in ARCHITECTURE")
    s.add_argument("feature", help="chosen persistent feature ID, not a task description")
    s.add_argument("--impact", required=True, help="one-sentence impact target")
    s.set_defaults(fn=cmd_init)

    s = sub.add_parser("status", help="read-only status and disclosed feature selection")
    s.add_argument("feature", nargs="?", help="optional ID; defaults to most recent file modification time")
    s.add_argument("-v", "--verbose", action="store_true", help="include backlog items")
    s.set_defaults(fn=cmd_status)

    s = sub.add_parser("list", help="list all features in .ai-state/ (most recent first)")
    s.set_defaults(fn=cmd_list)

    s = sub.add_parser("phase", help="change an explicit feature's stage; records current Git SHA, never creates a commit")
    s.add_argument("feature")
    s.add_argument("phase", choices=PHASES, help="stored stage code; does not certify acceptance")
    s.set_defaults(fn=cmd_phase)

    s = sub.add_parser("park", help="record explicitly targeted deferred work; does not implement it")
    s.add_argument("feature")
    s.add_argument("kind", choices=["edge", "hardening"])
    s.add_argument("description")
    s.set_defaults(fn=cmd_park)

    s = sub.add_parser("resolve", help="mark a backlog item resolved (or waived)")
    s.add_argument("feature")
    s.add_argument("kind", choices=["edge", "hardening"])
    s.add_argument("index", type=int, help="1-based index as shown by status -v")
    s.add_argument("--waive", metavar="REASON", help="mark as consciously skipped instead of fixed")
    s.set_defaults(fn=cmd_resolve)

    s = sub.add_parser("testbed", help="record or list test bed commands")
    s.add_argument("feature")
    s.add_argument("action", choices=["add", "list", "remove"], help="add requires --label/--cmd; remove requires an existing --label")
    s.add_argument("--label")
    s.add_argument("--cmd")
    s.set_defaults(fn=cmd_testbed)

    s = sub.add_parser("render", help="render the manifest as a markdown architecture doc")
    s.add_argument("feature")
    s.add_argument("--out", metavar="PATH", help="write to file instead of stdout")
    s.set_defaults(fn=cmd_render)

    s = sub.add_parser("tool", help="register or list reusable test bed tools (project-wide, committed)")
    s.add_argument("action", choices=["add", "list", "update"])
    s.add_argument("--name")
    s.add_argument("--path", help="repo-relative path, conventionally under testbed/tools/")
    s.add_argument("--desc")
    s.add_argument("--usage", help="one-line invocation example")
    s.add_argument("--feature", help="creator annotation for a tool, not a state-operation selector")
    s.set_defaults(fn=cmd_tool)

    s = sub.add_parser("decision", help="record an architecture decision")
    s.add_argument("feature")
    s.add_argument("--title", required=True)
    s.add_argument("--context", required=True)
    s.add_argument("--option", action="append", required=True, help="repeat for each option considered")
    s.add_argument("--decision", required=True)
    s.add_argument("--rationale", required=True)
    s.set_defaults(fn=cmd_decision)

    s = sub.add_parser("set", help="set a scalar field or append to a list field")
    s.add_argument("feature")
    s.add_argument("field", choices=sorted(list(SET_FIELDS) + list(APPEND_FIELDS)))
    s.add_argument("value")
    s.set_defaults(fn=cmd_set)

    args = p.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
