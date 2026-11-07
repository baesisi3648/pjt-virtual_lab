"""Experiment manifest: what is fixed before the main runs (revision_plan 7.3).

The manifest records the code, prompts, retrieval snapshot, run inputs, models, limits,
retry policy, Python environment and run order. `run_experiment.py --manifest` refuses
to start a run whose inputs differ from it or that is out of order. Code is compared by
file content (not by commit), so the commit that adds the manifest does not invalidate it.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from importlib import metadata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_VERSION = 1

# Everything a run can import or read as code. Prompt sets are hashed separately per condition.
# (rag/ is imported lazily only in live retrieval mode; it is covered anyway.)
CODE_PATHS = ("agents", "utils", "workflow", "tools", "data", "search", "rag", "config.py",
              "run_experiment.py", "requirements.txt", "experiments/reproducibility/analyze_revision.py")
PROMPT_DIRS = {"A": "prompts_A", "B": "prompts_B"}
FORBIDDEN_ENV = ("VIRTUAL_LAB_TEMPERATURE",)  # would change the generation parameters

# Constants recorded for readability; their files are also covered by the code hashes.
CONSTANTS = {
    "MAX_ROUNDS": "workflow/graph.py",
    "MAX_HTTP_RETRIES": "utils/llm.py",
    "MAX_INCOMPLETE_RETRIES": "utils/llm.py",
    "CRITIC_MAX_TOKENS": "utils/llm.py",
    "DEFAULT_CRITIC_MODEL": "utils/llm.py",
    "DEFAULT_CRITIC_EFFORT": "utils/llm.py",
    "CRITIC_VALIDATION_RETRIES": "agents/critic.py",
    "INTRO_MAX_TOKENS": "agents/pi.py",
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def _git(*args: str, root: Path = ROOT) -> str:
    return subprocess.check_output(["git", *args], cwd=root, text=True, encoding="utf-8",
                                   stderr=subprocess.DEVNULL).strip()


def _skip(rel: str) -> bool:
    return "__pycache__" in rel or rel.endswith(".pyc")


def tracked_files(paths, root: Path = ROOT) -> list[str]:
    out = _git("ls-files", "-z", "--", *paths, root=root)
    return sorted(f for f in out.split("\0") if f and not _skip(f))


def untracked_code(paths, root: Path = ROOT) -> list[str]:
    """Python files under `paths` that git does not track (untracked or ignored).

    Such a file could shadow or add to the tracked code, so it blocks the manifest and the runs.
    """
    tracked = set(tracked_files(paths, root))
    found = []
    for p in paths:
        base = root / p
        candidates = [base] if base.is_file() else (base.rglob("*.py") if base.is_dir() else [])
        for f in candidates:
            rel = f.relative_to(root).as_posix()
            if f.suffix == ".py" and not _skip(rel) and rel not in tracked:
                found.append(rel)
    # A module or package at the repository root that git does not track could shadow an import
    # (e.g. config/__init__.py next to config.py, or a folder named like a dependency).
    tracked_all = set(_git("ls-files", "-z", root=root).split("\0"))
    tracked_dirs = {f.split("/", 1)[0] for f in tracked_all if "/" in f}
    for child in root.iterdir():
        name = child.name
        if child.is_file() and child.suffix == ".py" and name not in tracked_all:
            found.append(name)
        elif child.is_dir() and name not in tracked_dirs and (child / "__init__.py").is_file():
            found.append(f"{name}/__init__.py")
    return sorted(set(found))


def file_hashes(paths, root: Path = ROOT) -> dict[str, str]:
    """Hashes of the tracked files under `paths`, read from the working tree."""
    return {f: sha256_file(root / f) for f in tracked_files(paths, root)}


def uncommitted(paths, root: Path = ROOT) -> list[str]:
    """Tracked files under `paths` that differ from HEAD (staged or not)."""
    out = _git("status", "--porcelain", "--untracked-files=no", "--", *paths, root=root)
    return [line for line in out.splitlines() if line.strip()]


def prompt_hashes(condition: str, root: Path = ROOT) -> dict[str, str]:
    d = root / PROMPT_DIRS[condition]
    return {p.relative_to(d).as_posix(): sha256_file(p) for p in sorted(d.rglob("*.md"))}


def _dist_name(d) -> str:
    return (d.metadata["Name"] or "").lower().replace("_", "-")


def installed_packages() -> dict[str, str]:
    """Every installed distribution and its version (the whole environment, not only requirements).

    The same name installed twice is recorded as all versions joined by "|", sorted, so the result
    does not depend on enumeration order; environment_problems() rejects it.
    """
    seen: dict[str, set] = {}
    for d in metadata.distributions():
        name = _dist_name(d)
        if name:
            seen.setdefault(name, set()).add(d.version)
    return {n: "|".join(sorted(v)) for n, v in sorted(seen.items())}


def environment_problems() -> list[str]:
    """Duplicate distributions and editable installs (whose source can change without a version change)."""
    problems = []
    counts: dict[str, int] = {}
    for d in metadata.distributions():  # count installs, so same-version duplicates are caught too
        name = _dist_name(d)
        if name:
            counts[name] = counts.get(name, 0) + 1
    dup = sorted(n for n, c in counts.items() if c > 1)
    if dup:
        problems.append("duplicate installed distributions: " + ", ".join(dup))
    editable = []
    for d in metadata.distributions():
        try:
            info = json.loads(d.read_text("direct_url.json") or "{}")
        except (json.JSONDecodeError, OSError):
            continue
        if info.get("dir_info", {}).get("editable"):
            editable.append(_dist_name(d))
    if editable:
        problems.append("editable installs are not allowed: " + ", ".join(sorted(editable)))
    return problems


def python_version() -> str:
    return sys.version.split()[0]


def read_constants(root: Path = ROOT) -> dict:
    out = {}
    for name, rel in CONSTANTS.items():
        text = (root / rel).read_text(encoding="utf-8")
        m = re.search(rf"(?m)^{name}\s*=\s*(.+?)\s*(?:#.*)?$", text)
        if not m:
            raise SystemExit(f"constant {name} not found in {rel}")
        raw = m.group(1)
        try:
            out[name] = json.loads(raw.replace("'", '"'))
        except json.JSONDecodeError:
            out[name] = raw
    return out


def load(path: Path) -> tuple[dict, str]:
    data = path.read_bytes()
    return json.loads(data.decode("utf-8")), sha256_bytes(data)


def excluded_attempts(manifest: dict) -> set[str]:
    """Attempt folders ("A_1/attempt_02") that a manifest amendment excludes from attempt counting."""
    return {x["attempt"] for x in manifest.get("amendment", {}).get("excluded_attempts", [])}


def attempt_folders(run_dir: Path) -> list[Path]:
    return sorted(d for d in run_dir.glob("attempt_*") if d.is_dir())


def attempt_statuses(run_dir: Path, excluded: set[str] | None = None) -> list[str]:
    """Status of each counted attempt folder in order; a folder without meta.json counts as 'incomplete'.

    Folders listed in `excluded` (as "<run>/<attempt>") are skipped.
    """
    out = []
    for a in attempt_folders(run_dir):
        if excluded and f"{run_dir.name}/{a.name}" in excluded:
            continue
        try:
            out.append(json.loads((a / "meta.json").read_text(encoding="utf-8")).get("status", "unknown"))
        except (OSError, json.JSONDecodeError):
            out.append("incomplete")
    return out


def check_order(manifest: dict, condition: str, run_id: str, attempt: int, runs_dir: Path) -> list[str]:
    """Runs go in manifest order; a failed attempt is retried before the next run starts.

    Attempts excluded by a manifest amendment are ignored for every check except folder numbering:
    a new attempt always takes the next folder number.
    """
    problems = []
    excl = excluded_attempts(manifest)
    order = sorted(manifest.get("order", []), key=lambda e: e["seq"])
    idx = next((i for i, e in enumerate(order) if e["condition"] == condition and str(e["run_id"]) == str(run_id)), None)
    max_attempts = manifest.get("retry_policy", {}).get("max_attempts_per_run")
    if idx is None:
        return [f"{condition}_{run_id} is not in the manifest run order"]
    for e in order[:idx]:
        st = attempt_statuses(runs_dir / f"{e['condition']}_{e['run_id']}", excl)
        if "ok" not in st and len(st) < (max_attempts or 0):
            problems.append(f"earlier run {e['condition']}_{e['run_id']} (seq {e['seq']}) is not finished")
    for e in order[idx + 1:]:
        if attempt_statuses(runs_dir / f"{e['condition']}_{e['run_id']}", excl):
            problems.append(f"later run {e['condition']}_{e['run_id']} (seq {e['seq']}) has already started")
    run_dir = runs_dir / f"{condition}_{run_id}"
    counted = attempt_statuses(run_dir, excl)
    folders = len(attempt_folders(run_dir))
    if "ok" in counted:
        problems.append(f"{condition}_{run_id} already has a successful attempt")
    if attempt != folders + 1:
        problems.append(f"attempt must be {folders + 1} (existing attempt folders: {folders}), got {attempt}")
    if not isinstance(max_attempts, int) or not 1 <= len(counted) + 1 <= max_attempts:
        problems.append(f"counted attempts would be {len(counted) + 1}, outside 1..{max_attempts}")
    return problems


def next_attempt(manifest: dict, condition: str, run_id: str, runs_dir: Path) -> str:
    """'done' (has an ok attempt), 'exhausted' (no counted attempts left) or the next attempt number."""
    run_dir = runs_dir / f"{condition}_{run_id}"
    counted = attempt_statuses(run_dir, excluded_attempts(manifest))
    if "ok" in counted:
        return "done"
    if len(counted) >= manifest.get("retry_policy", {}).get("max_attempts_per_run", 0):
        return "exhausted"
    return str(len(attempt_folders(run_dir)) + 1)


def verify(manifest: dict, *, condition: str, run_id: str, attempt: int, retrieval_mode: str,
           snapshot_path: Path, topic: str, constraints: str, runs_dir: Path | None,
           root: Path = ROOT) -> list[str]:
    """Return every mismatch between the current inputs and the manifest (empty = OK).

    `runs_dir` (the main output folder) enables the order and attempt checks.
    """
    problems: list[str] = []
    if manifest.get("manifest_version") != MANIFEST_VERSION:
        problems.append(f"manifest_version {manifest.get('manifest_version')!r} != {MANIFEST_VERSION}")

    if runs_dir is not None:
        problems += check_order(manifest, condition, run_id, attempt, runs_dir)
    else:
        if not any(e["condition"] == condition and str(e["run_id"]) == str(run_id) for e in manifest.get("order", [])):
            problems.append(f"{condition}_{run_id} is not in the manifest run order")
        max_attempts = manifest.get("retry_policy", {}).get("max_attempts_per_run")
        if not isinstance(max_attempts, int) or not 1 <= attempt <= max_attempts:
            problems.append(f"attempt {attempt} is outside 1..{max_attempts}")

    inputs = manifest.get("inputs", {})
    if topic != inputs.get("topic"):
        problems.append("--topic differs from the manifest")
    if constraints != inputs.get("constraints"):
        problems.append("--constraints differs from the manifest")

    if retrieval_mode != manifest["retrieval"]["mode"]:
        problems.append(f"retrieval mode {retrieval_mode!r} != {manifest['retrieval']['mode']!r}")
    if not snapshot_path.is_file():
        problems.append(f"retrieval snapshot missing: {snapshot_path}")
    elif sha256_file(snapshot_path) != manifest["retrieval"]["snapshot_sha256"]:
        problems.append("retrieval snapshot hash differs from the manifest")

    if prompt_hashes(condition, root) != manifest["prompts"][condition]["file_hashes"]:
        problems.append(f"prompt set {PROMPT_DIRS[condition]} differs from the manifest")

    current = file_hashes(CODE_PATHS, root)
    expected = manifest["code"]["file_hashes"]
    changed = sorted(f for f in set(current) | set(expected) if current.get(f) != expected.get(f))
    if changed:
        problems.append("code differs from the manifest: " + ", ".join(changed[:10])
                        + (" ..." if len(changed) > 10 else ""))
    extra = untracked_code(CODE_PATHS, root)
    if extra:
        problems.append("untracked Python files in code paths: " + ", ".join(extra[:10]))

    for f, h in (manifest.get("preparation") or {}).get("file_hashes", {}).items():
        if not (root / f).is_file() or sha256_file(root / f) != h:
            problems.append(f"preparation file differs from the manifest: {f}")
    corpus = manifest.get("corpus")
    if corpus:
        cpath = root / corpus["manifest_path"]
        if not cpath.is_file() or sha256_file(cpath) != corpus["manifest_sha256"]:
            problems.append("corpus manifest differs from the manifest")

    models = manifest["models"]
    gen = os.environ.get("GPT_MODEL", "gpt-4o")
    if gen != models["generation_model_requested"]:
        problems.append(f"GPT_MODEL {gen!r} != {models['generation_model_requested']!r}")
    for env, key in (("CRITIC_MODEL", "critic_model_requested"), ("CRITIC_EFFORT", "critic_effort")):
        val = os.environ.get(env)
        if val is not None and val != models[key]:
            problems.append(f"{env} {val!r} != {models[key]!r}")
    for env in FORBIDDEN_ENV:
        if os.environ.get(env) is not None:
            problems.append(f"{env} is set; unset it for the main runs")

    problems += environment_problems()
    envm = manifest.get("environment", {})
    if envm.get("python") != python_version():
        problems.append(f"Python {python_version()} != {envm.get('python')}")
    if "packages" in envm:
        cur = installed_packages()
        diff = sorted(n for n in set(cur) | set(envm["packages"]) if cur.get(n) != envm["packages"].get(n))
        if diff:
            problems.append("installed packages differ from the manifest: "
                            + ", ".join(f"{n} {envm['packages'].get(n)}->{cur.get(n)}" for n in diff[:10]))
    return problems
