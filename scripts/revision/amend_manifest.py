"""Amendment 1 to the main-experiment manifest (2026-11-07): exclude attempts lost to the exhausted
OpenAI credit balance from attempt counting (RUN_LOG 2026-11-06).

    python -B scripts/revision/amend_manifest.py

- Keeps every execution input of manifest v1 (code, prompts, snapshot, models, limits, order,
  environment). The only code difference allowed is utils/manifest.py, which gained the
  amendment-aware attempt counting.
- Lists each excluded attempt with its evidence: status failed, and every OpenAI call that failed
  ended with HTTP 429 and no successful OpenAI response after the first 429.
- v1 is kept as experiment_manifest.v1.json; the amended manifest becomes experiment_manifest.json.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from utils import manifest as mf  # noqa: E402

RUNS = ROOT / "experiments" / "runs_rev"
CUR = RUNS / "experiment_manifest.json"
V1 = RUNS / "experiment_manifest.v1.json"
V1_SHA = "ae922a5db1a34e8c3eaa95b218d7a4d79989a56fe93fee0228cec20c5d1bb66c"
MAIN = RUNS / "main"
KST = timezone(timedelta(hours=9))
ALLOWED_CODE_CHANGES = {"utils/manifest.py"}
# Outage window (KST): from the start of B_2 attempt_01 to the end of the last failed attempt.
WINDOW_KST = ("2026-11-06T20:19:00+09:00", "2026-11-06T22:09:00+09:00")
EXPECTED_EXCLUDED = 21
FINAL_ERRORS = ("OpenAI API rate limit exceeded after 5 retries",
                "Team composition did not reach 10 trials after 30 attempts (0 succeeded).")


def credit_evidence(att: Path) -> dict | None:
    """Evidence that an attempt failed because of the credit balance, or None."""
    meta = json.loads((att / "meta.json").read_text(encoding="utf-8"))
    if meta.get("status") != "failed":
        return None
    start = datetime.fromisoformat(meta["started"]["kst"])
    if not (datetime.fromisoformat(WINDOW_KST[0]) <= start <= datetime.fromisoformat(WINDOW_KST[1])):
        return None
    if (meta.get("error") or {}).get("message") not in FINAL_ERRORS:
        return None
    calls = [json.loads(line) for line in (att / "calls.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    if any(c.get("provider") != "openai" and c.get("status") != "ok" for c in calls):
        return None  # another failure (e.g. a Critic refusal) is present
    openai = [c for c in calls if c.get("provider") == "openai"]
    failed = [c for c in openai if c.get("status") != "ok"]
    if not failed:
        return None
    first_fail = calls.index(failed[0])
    ok_after = [c for c in calls[first_fail:] if c.get("provider") == "openai" and c.get("status") == "ok"]
    statuses = {a.get("http_status") for c in failed for a in c.get("attempts", [])}
    if ok_after or statuses != {429}:
        return None
    return {
        "attempt": f"{att.parent.name}/{att.name}",
        "started_kst": meta["started"]["kst"], "finished_kst": meta["finished"]["kst"],
        "status": meta["status"], "error": (meta.get("error") or {}).get("message", "")[:200],
        "openai_calls_ok_before_failure": sum(1 for c in openai[: openai.index(failed[0])] if c.get("status") == "ok"),
        "openai_calls_failed": len(failed), "http_statuses_of_failed_calls": sorted(statuses),
        "first_failure_utc": failed[0].get("started_utc"),
    }


def main() -> int:
    if V1.exists():
        raise SystemExit(f"{V1} already exists; the amendment has been made")
    v1, sha = mf.load(CUR)
    if sha != V1_SHA:
        raise SystemExit(f"current manifest is not v1 (sha256 {sha})")
    dirty = mf.uncommitted(list(mf.CODE_PATHS) + list(mf.PROMPT_DIRS.values()))
    if dirty:
        raise SystemExit("commit these files first:\n  " + "\n  ".join(dirty))

    cur_hashes = mf.file_hashes(mf.CODE_PATHS)
    old = v1["code"]["file_hashes"]
    changed = {f for f in set(cur_hashes) | set(old) if cur_hashes.get(f) != old.get(f)}
    if changed - ALLOWED_CODE_CHANGES:
        raise SystemExit(f"code differs from v1 beyond {ALLOWED_CODE_CHANGES}: {sorted(changed - ALLOWED_CODE_CHANGES)}")
    for c in "AB":
        if mf.prompt_hashes(c) != v1["prompts"][c]["file_hashes"]:
            raise SystemExit(f"prompt set {c} differs from v1")
    if mf.python_version() != v1["environment"]["python"] or mf.installed_packages() != v1["environment"]["packages"]:
        raise SystemExit("Python or installed packages differ from v1")

    excluded, kept_failed = [], []
    for run_dir in sorted(d for d in MAIN.iterdir() if d.is_dir()):
        for att in mf.attempt_folders(run_dir):
            ev = credit_evidence(att)
            if ev:
                excluded.append(ev)
            elif json.loads((att / "meta.json").read_text(encoding="utf-8")).get("status") != "ok":
                kept_failed.append(f"{run_dir.name}/{att.name}")
    if len(excluded) != EXPECTED_EXCLUDED:
        raise SystemExit(f"expected {EXPECTED_EXCLUDED} excluded attempts, found {len(excluded)}")
    if kept_failed:
        raise SystemExit(f"failed attempts without credit-exhaustion evidence (not excluded, review first): {kept_failed}")

    now = datetime.now(timezone.utc)
    amended = json.loads(json.dumps(v1))
    amended["code"]["file_hashes"] = cur_hashes
    amended["code"]["commit_at_amendment"] = mf._git("rev-parse", "HEAD")
    amended["amendment"] = {
        "number": 1,
        "created": {"utc": now.isoformat(), "kst": now.astimezone(KST).isoformat()},
        "supersedes": {"file": "experiment_manifest.v1.json", "sha256": V1_SHA},
        "reason": ("The OpenAI credit balance was exhausted during B_2 attempt_01 (2026-11-06, about 20:40 KST). "
                   "All later attempts failed within minutes with HTTP 429 and consumed the three attempts of "
                   "every remaining run. A test call at about 22:30 KST returned HTTP 429, error type "
                   "insufficient_quota, code credit_balance_exhausted. This is an account billing failure, a "
                   "technical failure under the retry policy, that occurred before any report was opened. The 429 response "
                   "bodies of the failed attempts were not recorded, so their cause is inferred from the timing, the "
                   "identical failure pattern and the diagnostic calls (22:30 KST on 2026-11-06, and again after the "
                   "top-up on 2026-11-07 before the credit became available). This is a one-off decision for the "
                   "fixed list below, made after the failures and before any report was opened."),
        "rule": ("Attempts listed in excluded_attempts are not counted toward max_attempts_per_run and do not "
                 "count as a started or finished run in the order check. They are kept on disk and reported. New "
                 "attempts take the next folder number. Every other input of v1 is unchanged; the only code change "
                 "is utils/manifest.py (amendment-aware counting)."),
        "outage_window_kst": list(WINDOW_KST),
        "evidence_criteria": ("status failed; started within the outage window; final error is the OpenAI 429 "
                              "retry exhaustion or the team-composition failure caused by it; every failed OpenAI "
                              "call ended with HTTP 429; no successful OpenAI call after the first failure; no "
                              "failure of any other provider"),
        "use_of_excluded_attempts": ("kept on disk and reported (24 attempts in total: 3 successful, 21 excluded); "
                                     "their outputs and scores are not used in any analysis; a run is restarted "
                                     "from the beginning in a new process"),
        "unchanged_runs": ["A_1/attempt_01", "B_1/attempt_01", "A_2/attempt_01"],
        "excluded_attempts": excluded,
        "prevention": ("scripts/revision/run_main.sh makes one minimal OpenAI request before each attempt with "
                       "the same key resolution as the run (environment first, then .env), logs it to "
                       "main_logs/preflight.jsonl, and stops without starting the attempt on any non-200 "
                       "response or error. A successful preflight does not guarantee the balance for a whole run."),
    }
    CUR.rename(V1)
    CUR.write_text(json.dumps(amended, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"v1 kept as {V1.name}; amended manifest sha256={mf.sha256_file(CUR)}")
    print(f"excluded attempts: {len(excluded)}")
    for ev in excluded:
        print(f"  {ev['attempt']}  {ev['started_kst'][11:19]}  ok-before={ev['openai_calls_ok_before_failure']} "
              f"failed={ev['openai_calls_failed']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
