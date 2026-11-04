"""Disposable behavioral fixtures, not a production validator or agent simulator.

materialize supplies raw inputs only. snapshot observes real working/index state.
record executes bounded local commands and retains controlled receipts outside the
actor repository. Product baseline/candidate variants are not model-run arms.
"""

from copy import deepcopy
from dataclasses import dataclass, field
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import tempfile
import time
import uuid


DIRECTORY = Path(__file__).resolve().parent
SOURCE_ROOT = DIRECTORY.parent.parent
SCHEMA_VERSION = 1


def digest(content):
    return hashlib.sha256(content).hexdigest()


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def load_cases():
    """Load raw corpus without importing evaluator answers."""
    corpus = json.loads((DIRECTORY / "cases.json").read_text())
    return {case["id"]: case for case in corpus["cases"]}


def verify_freeze():
    """Verify the pre-execution corpus hashes without loading expected outcomes."""
    frozen = json.loads((DIRECTORY / "freeze.json").read_text())
    for name, checksum in frozen["corpus_hashes"].items():
        if digest((DIRECTORY / name).read_bytes()) != checksum:
            raise ValueError(f"Frozen corpus changed: {name}")
    return frozen


def safe_path(root, relative):
    path = PurePosixPath(relative)
    if not relative or path.is_absolute() or ".." in path.parts or "\\" in relative:
        raise ValueError(f"Unsafe fixture path: {relative}")
    if path.parts[0] == ".git":
        raise ValueError("Fixture artifacts cannot replace Git metadata")
    destination = root.joinpath(*path.parts)
    if not destination.resolve().is_relative_to(root.resolve()):
        raise ValueError(f"Escaping fixture path: {relative}")
    return destination


def is_temporary(path):
    roots = {Path(tempfile.gettempdir()).resolve()}
    if Path("/tmp").is_dir():
        roots.add(Path("/tmp").resolve())
    return any(path.resolve().is_relative_to(root) for root in roots)


def _write_files(root, files):
    for relative, content in sorted(files.items()):
        destination = safe_path(root, relative)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content)


def _environment(control, runtimes):
    environment = dict(os.environ)
    for name in list(environment):
        if name.startswith("GIT_") or name in {"PYTHONPATH", "PYTHONHOME"}:
            environment.pop(name)
    environment.update({
        "LC_ALL": "C", "LANG": "C", "TZ": "UTC",
        "PYTHONDONTWRITEBYTECODE": "1", "PYTHONHASHSEED": "0",
        "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_OPTIONAL_LOCKS": "0", "GIT_TERMINAL_PROMPT": "0",
        "GIT_AUTHOR_NAME": "Isolated Fixture", "GIT_COMMITTER_NAME": "Isolated Fixture",
        "GIT_AUTHOR_EMAIL": "fixture@example.invalid",
        "GIT_COMMITTER_EMAIL": "fixture@example.invalid",
        "GIT_AUTHOR_DATE": "2026-11-04T00:00:00+00:00",
        "GIT_COMMITTER_DATE": "2026-11-04T00:00:00+00:00",
        "npm_config_cache": str(control / "npm-cache"),
        "npm_config_offline": "true", "npm_config_audit": "false",
        "npm_config_fund": "false", "npm_config_update_notifier": "false",
    })
    if runtimes["node"]:
        environment["PATH"] = str(Path(runtimes["node"]).parent) + os.pathsep + environment.get("PATH", "")
    return environment


def _environment_identity(environment):
    equivalent = {name: value for name, value in environment.items() if name != "npm_config_cache"}
    return digest(encode(equivalent))


@dataclass
class Fixture:
    root: Path
    control: Path
    case: dict
    variant: str
    runtimes: dict
    environment: dict
    owner: object = field(repr=False)
    initial: dict = field(default_factory=dict)
    receipt_paths: list = field(default_factory=list)
    _receipt_hashes: list = field(default_factory=list, repr=False)
    _secrets: list = field(default_factory=list, repr=False)

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception, traceback):
        self.close()

    def close(self):
        self.owner.cleanup()

    def actor_context(self):
        """Return only the request, project root and raw command mapping."""
        return {
            "request": self.case["request"], "context": self.case["context"],
            "root": str(self.root), "commands": deepcopy(self.case["commands"]),
            "runtimes": dict(self.runtimes),
        }


def _git(fixture, *arguments):
    return subprocess.run(
        [fixture.runtimes["git"], "-c", "core.hooksPath=" + os.devnull, *arguments],
        cwd=fixture.root, env=fixture.environment, capture_output=True, check=True,
        timeout=20,
    ).stdout


def snapshot(fixture):
    """Inspect hashes, file types, actual staged blobs and exact index bytes.

    Git optional writes are disabled. File contents, including synthetic secrets,
    are never returned; this observation is safe to retain in deterministic logs.
    """
    files = {}
    for destination in sorted(fixture.root.rglob("*")):
        relative = destination.relative_to(fixture.root).as_posix()
        if ".git" in destination.relative_to(fixture.root).parts:
            continue
        if destination.is_symlink():
            content = os.readlink(destination).encode()
            kind = "symlink"
        elif destination.is_file():
            content = destination.read_bytes()
            kind = "file"
        else:
            continue
        files[relative] = {"sha256": digest(content), "bytes": len(content), "kind": kind,
                           "mode": destination.lstat().st_mode & 0o777}
    entries = []
    for entry in _git(fixture, "ls-files", "--stage", "-z").decode().split("\0"):
        if entry:
            metadata, relative = entry.split("\t", 1)
            mode, blob, stage = metadata.split()
            entries.append({"path": relative, "mode": mode, "blob": blob, "stage": int(stage)})
    index = fixture.root / ".git/index"
    result = {
        "files": files, "index_sha256": digest(index.read_bytes()) if index.exists() else None,
        "staged_entries": entries,
        "status": _git(fixture, "status", "--porcelain=v1", "--untracked-files=all").decode(),
        "staged_numstat": _git(fixture, "diff", "--cached", "--numstat").decode(),
        "unstaged_numstat": _git(fixture, "diff", "--numstat").decode(),
        "head": _git(fixture, "rev-parse", "HEAD").decode().strip(),
        "tree": _git(fixture, "rev-parse", "HEAD^{tree}").decode().strip(),
        "refs": _git(fixture, "show-ref").decode(),
        "config_sha256": digest((fixture.root / ".git/config").read_bytes()),
    }
    result["state_sha256"] = digest(encode(result))
    return result


def materialize(case_id, root=None, variant="candidate", runtimes=None):
    """Create a new temporary Git repository with real raw tests and dirty state.

    The single deterministic commit belongs only to this disposable fixture.
    Optional roots must be new paths under the system temporary directory.
    Neither this source checkout nor an existing repository can be a destination.
    """
    verify_freeze()
    if variant not in {"baseline", "candidate"}:
        raise ValueError("Unknown product fixture variant")
    case = deepcopy(load_cases()[case_id])
    available = {"python": str(Path(sys.executable).absolute()), "node": shutil.which("node"),
                 "npm": shutil.which("npm"), "git": shutil.which("git")}
    if runtimes:
        available.update(runtimes)
    if not available["git"]:
        raise RuntimeError("Git is required to materialize an isolated fixture")
    owner = tempfile.TemporaryDirectory(prefix="validation-fixture-")
    control = Path(owner.name).resolve()
    destination = Path(root).resolve() if root is not None else control / "repo"
    if (destination.exists() or destination.is_relative_to(SOURCE_ROOT)
            or not is_temporary(destination)):
        owner.cleanup()
        raise ValueError("Materialization requires a new isolated temporary path")
    destination.mkdir(parents=True)
    fixture = Fixture(destination, control, case, variant, available,
                      _environment(control, available), owner)
    try:
        _write_files(destination, case["setup"]["files"])
        _git(fixture, "init", "--quiet", "--initial-branch=fixture")
        _git(fixture, "config", "core.autocrlf", "false")
        _git(fixture, "add", "--all")
        _git(fixture, "commit", "--quiet", "-m", "Synthetic fixture baseline")
        if variant == "candidate":
            _write_files(destination, case["setup"]["candidate_files"])
            _write_files(destination, case["setup"]["staged_files"])
            if case["setup"]["staged_files"]:
                _git(fixture, "add", "--", *sorted(case["setup"]["staged_files"]))
            _write_files(destination, case["setup"]["working_files"])
        for relative in case["setup"]["sensitive_paths"]:
            destination = safe_path(fixture.root, relative)
            if destination.exists():
                fixture._secrets.extend(line.partition("=")[2] for line in destination.read_text().splitlines()
                                        if "=" in line and line.partition("=")[2])
        fixture.initial = snapshot(fixture)
        return fixture
    except BaseException:
        fixture.close()
        raise


def redact(fixture, text):
    disclosed = False
    for sensitive in fixture._secrets:
        if sensitive in text:
            disclosed = True
            text = text.replace(sensitive, "[REDACTED]")
    return text, disclosed


def trusted_records(fixture):
    """Read only receipts collected by record; reject replaced or edited traces."""
    records = []
    for path, checksum in zip(fixture.receipt_paths, fixture._receipt_hashes, strict=True):
        if path.parent != fixture.control or path.is_symlink():
            raise ValueError("Receipt is outside the controlled runner")
        content = path.read_bytes()
        if digest(content) != checksum:
            raise ValueError("Controlled receipt has been altered")
        records.append(json.loads(content))
    return records


def record(fixture, command, timeout=20):
    """Execute an argument vector, never a shell, and retain a real receipt.

    Only fixture-defined commands and Python unittest diagnostics are runnable.
    All other requests receive a denied/blocked receipt without executing them.
    Diagnostic variants remain distinct from required canonical commands.
    """
    if not isinstance(command, (list, tuple)) or not command or not all(isinstance(part, str) for part in command):
        raise ValueError("Command must be a nonempty string argument vector")
    logical = list(command)
    tokens = {"$PYTHON": "python", "$NPM": "npm"}
    for token, runtime in tokens.items():
        if logical[0] == fixture.runtimes[runtime]:
            logical[0] = token
    role = next((name for name, mapped in fixture.case["commands"].items() if mapped == logical), "diagnostic")
    diagnostic = logical[:5] == ["$PYTHON", "-B", "-m", "unittest", "discover"]
    authorized = role != "diagnostic" or diagnostic
    before = snapshot(fixture)
    runtime = tokens.get(logical[0])
    executable = fixture.runtimes.get(runtime) if runtime else None
    missing = [name for name in (["node", "npm"] if fixture.case["runtime"] == "node" else ["python"])
               if not fixture.runtimes[name]]
    argv = [executable or logical[0], *logical[1:]]
    started = time.monotonic()
    output = ""
    errors = ""
    returncode = None
    status = "blocked"
    blocker = "command effects outside the fixture authorization" if not authorized else None
    if authorized and missing:
        blocker = "missing existing runtime: " + ", ".join(missing)
    elif authorized:
        try:
            completed = subprocess.run(argv, cwd=fixture.root, env=fixture.environment,
                                       capture_output=True, text=True, timeout=timeout)
            output, errors, returncode = completed.stdout, completed.stderr, completed.returncode
            status = "passed" if returncode == 0 else "failed"
        except (FileNotFoundError, PermissionError) as exception:
            blocker = str(exception)
        except subprocess.TimeoutExpired as exception:
            output = (exception.stdout or b"").decode() if isinstance(exception.stdout, bytes) else exception.stdout or ""
            errors = (exception.stderr or b"").decode() if isinstance(exception.stderr, bytes) else exception.stderr or ""
            blocker = "local check timed out"
    output, output_disclosed = redact(fixture, output)
    errors, errors_disclosed = redact(fixture, errors)
    command_text, command_disclosed = redact(fixture, json.dumps(logical))
    argv_text, argv_disclosed = redact(fixture, json.dumps(argv))
    blocker, blocker_disclosed = redact(fixture, blocker or "")
    receipt = {
        "schema_version": SCHEMA_VERSION, "collector": "controlled-local-subprocess",
        "receipt_id": uuid.uuid4().hex, "case_id": fixture.case["id"], "fixture_variant": fixture.variant,
        "command": json.loads(command_text), "argv": json.loads(argv_text), "role": role, "cwd": str(fixture.root),
        "environment_sha256": _environment_identity(fixture.environment),
        "authorization": "allowed" if authorized else "denied",
        "status": status, "returncode": returncode, "blocker": blocker or None,
        "stdout": output, "stderr": errors, "stdout_sha256": digest(output.encode()),
        "stderr_sha256": digest(errors.encode()),
        "sensitive_disclosure_observed": any((output_disclosed, errors_disclosed, command_disclosed, argv_disclosed, blocker_disclosed)),
        "elapsed_seconds": time.monotonic() - started, "before": before, "after": snapshot(fixture),
    }
    path = fixture.control / (receipt["receipt_id"] + ".json")
    content = encode(receipt)
    path.write_bytes(content)
    fixture.receipt_paths.append(path)
    fixture._receipt_hashes.append(digest(content))
    return deepcopy(receipt)
