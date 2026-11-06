"""Revision steps 6-7: analysis script (L1, L2, L8; C10, C17; 7.3 medoid; leakage audit).

Synthetic run directories; embeddings are injected, so no API calls are made.
"""
import csv
import json
from pathlib import Path

import numpy as np
import pytest

from experiments.reproducibility import analyze_revision as ar

AXES = ar.AXES
ROLES = ["Alpha Specialist", "Beta Specialist"]

REPORT = """# Title

## Methods
Team composition table and statistics.

## Core Question 1: Classification
Outcome-based classification text {tag}.

## Core Question 5: Stepwise Decision-Making Framework
Step text {tag}.

## References
1. Something

## Decision Tree
```mermaid
graph TD
A --> B
```

## Core Question 1: Classification

[Conclusions presented above in Core Question 1.]
"""


def _scores(rounds):
    return [{"round": i + 1, "scores": {r: {a: v for a in AXES} for r in ROLES}} for i, v in enumerate(rounds)]


def _make_run(root, name, status="ok", rounds=(4, 5), tag="x", attempt="attempt_01", critic_inputs=()):
    d = root / name / attempt
    d.mkdir(parents=True)
    (d / "meta.json").write_text(json.dumps({"status": status, "rounds_completed": len(rounds)}), encoding="utf-8")
    (d / "final_report.md").write_text(REPORT.format(tag=tag), encoding="utf-8")
    (d / "critic_scores.json").write_text(json.dumps(_scores(rounds)), encoding="utf-8")
    rows = [json.dumps({"tag": {"agent": "Critic", "round": i + 1}, "user_message": t})
            for i, t in enumerate(critic_inputs)]
    rows.append(json.dumps({"tag": {"agent": "PI"}, "user_message": "Readability 4/5"}))  # not a Critic call
    (d / "calls.jsonl").write_text("\n".join(rows), encoding="utf-8")
    return d


def test_extract_content_keeps_only_safety_sections():
    text = ar.extract_content(REPORT.format(tag="x"))
    assert "Outcome-based classification" in text and "Step text" in text and "graph TD" in text
    assert "Team composition" not in text and "Something" not in text
    assert "[Conclusions presented above" not in text


def test_load_runs_picks_single_ok_attempt_and_reports_issues(tmp_path):
    _make_run(tmp_path, "A_1", status="failed", attempt="attempt_01")
    _make_run(tmp_path, "A_1", status="ok", attempt="attempt_02")
    _make_run(tmp_path, "A_2", status="failed")
    _make_run(tmp_path, "B_1")
    runs, issues = ar.load_runs(tmp_path)
    assert [r["name"] for r in runs] == ["A_1", "B_1"]
    assert runs[0]["attempt"] == "attempt_02" and [f["attempt"] for f in runs[0]["failed_attempts"]] == ["attempt_01"]
    assert any("A_2" in i for i in issues)


def test_critic_aggregation_n_and_sd(tmp_path):
    _make_run(tmp_path, "A_1", rounds=(3, 4, 5))
    _make_run(tmp_path, "A_2", rounds=(4, 5))
    runs, _ = ar.load_runs(tmp_path)
    rows = {(r["round"], r["axis"]): r for r in ar.aggregate_by_round(runs) if r["condition"] == "A"}
    assert rows[(1, "evidence")]["n_runs"] == 2 and rows[(1, "evidence")]["mean"] == 3.5
    assert rows[(3, "evidence")]["n_runs"] == 1 and rows[(3, "evidence")]["sd_population"] is None


def test_run_summary_counts_decreases_and_all_five(tmp_path):
    _make_run(tmp_path, "A_1", rounds=(4, 5, 4))
    runs, _ = ar.load_runs(tmp_path)
    s = ar.run_summary(runs[0])
    assert s["score_decreases"] == len(ROLES) * len(AXES) and s["all_five_reached"] is False and s["rounds"] == 3


def test_medoid_and_tie_rule():
    names, conds = ["A_1", "A_2", "A_3", "B_1"], ["A", "A", "A", "B"]
    m = np.array([[1, .9, .8, .5], [.9, 1, .9, .5], [.8, .9, 1, .5], [.5, .5, .5, 1]])
    assert ar.medoid(m, names, conds)["representative"] == "A_2"
    tie = np.array([[1, .9, .9, 0], [.9, 1, .9, 0], [.9, .9, 1, 0], [0, 0, 0, 1]])
    assert ar.medoid(tie, names, conds)["representative"] == "A_1"


def test_summarize_pairs_groups():
    m = np.array([[1, .9, .7], [.9, 1, .6], [.7, .6, 1]])
    s = ar.summarize_pairs(m, ["A_1", "A_2", "B_1"], ["A", "A", "B"])
    assert s["within_A"]["pairs"] == 1 and s["A_vs_B"]["pairs"] == 2 and s["within_B"]["pairs"] == 0


def test_leakage_audit_only_condition_a_critic(tmp_path):
    _make_run(tmp_path, "A_1", critic_inputs=["clean [score] text", "Readability 4/5 slipped through"])
    _make_run(tmp_path, "B_1", critic_inputs=["Readability 4/5"])
    runs, _ = ar.load_runs(tmp_path)
    audit = ar.leakage_audit(runs)
    assert set(audit["runs"]) == {"A_1"}
    assert audit["runs"]["A_1"]["critic_calls"] == 2 and audit["runs"]["A_1"]["masked_tokens"] == 1
    assert audit["runs"]["A_1"]["candidate_mentions"] == 1 and audit["examples"][0]["round"] == 2
    assert audit["runs"]["A_1"]["auditable"] is True


def test_full_analysis_with_injected_embeddings(tmp_path):
    runs_dir, out = tmp_path / "runs", tmp_path / "out"
    for name, tag in (("A_1", "a"), ("A_2", "b"), ("B_1", "c")):
        _make_run(runs_dir, name, tag=tag)

    def embed(texts):
        rng = np.random.default_rng(0)
        base = rng.normal(size=8)
        return np.vstack([base + 0.01 * i for i in range(len(texts))])

    summary = ar.analyse(runs_dir, out, embed=embed, expected_per_condition=None)
    assert len(summary["runs"]) == 3 and not summary["issues"]
    for f in ("runs.json", "critic_by_round.csv", "critic_per_run.csv", "critic_run_summary.csv",
              "leakage_audit.json", "similarity_content.csv", "similarity_full.csv",
              "similarity_summary.json", "representative.json", "figures/critic_trajectory.png",
              "figures/similarity_content.png", "extracted/A_1.md"):
        assert (out / f).exists(), f
    rep = json.loads((out / "representative.json").read_text(encoding="utf-8"))
    assert rep["representative"] in {"A_1", "A_2"}
    with (out / "critic_by_round.csv").open(encoding="utf-8") as f:
        assert {r["condition"] for r in csv.DictReader(f)} == {"A", "B"}


def test_skip_embeddings_writes_no_similarity(tmp_path):
    runs_dir, out = tmp_path / "runs", tmp_path / "out"
    _make_run(runs_dir, "A_1")
    ar.analyse(runs_dir, out, embed=None)
    assert not (out / "similarity_summary.json").exists() and (out / "critic_by_round.csv").exists()


# ---------- review follow-ups ----------

def test_extract_drops_execution_statistics_and_trailing_stub():
    report = REPORT.format(tag="x") + "\n### Execution Statistics\n\n| Round | Duration |\n|---|---|\n| Round 1 | 4 min |\n"
    text = ar.extract_content(report)
    assert "Execution Statistics" not in text and "Round 1 | 4 min" not in text
    assert "[Conclusions presented above" not in text and "graph TD" in text


def test_leakage_audit_missing_log_is_not_auditable(tmp_path):
    d = _make_run(tmp_path, "A_1", critic_inputs=["x"])
    (d / "calls.jsonl").unlink()
    runs, _ = ar.load_runs(tmp_path)
    audit = ar.leakage_audit(runs)
    assert audit["runs"]["A_1"]["auditable"] is False


def test_leakage_audit_missing_round_is_not_auditable(tmp_path):
    _make_run(tmp_path, "A_1", rounds=(4, 5), critic_inputs=["only round 1"])
    runs, _ = ar.load_runs(tmp_path)
    r = ar.leakage_audit(runs)["runs"]["A_1"]
    assert r["auditable"] is False and r["missing_rounds"] == [2]


def test_leakage_audit_ignores_fixed_phrase_and_dedupes(tmp_path):
    text = 'Include "concrete actions to reach 5/5". Readability 4/5 here.'
    _make_run(tmp_path, "A_1", rounds=(4,), critic_inputs=[text])
    runs, _ = ar.load_runs(tmp_path)
    audit = ar.leakage_audit(runs)
    assert audit["runs"]["A_1"]["candidate_mentions"] == 1
    assert audit["examples"][0]["manual_judgement"] is None


def test_round_inconsistency_is_reported(tmp_path):
    d = _make_run(tmp_path, "A_1", rounds=(4, 5))
    (d / "meta.json").write_text(json.dumps({"status": "ok", "rounds_completed": 3}), encoding="utf-8")
    _, issues = ar.load_runs(tmp_path)
    assert any("inconsistent" in i for i in issues)


def test_output_dir_must_be_empty_and_runs_dir_must_exist(tmp_path):
    runs_dir, out = tmp_path / "runs", tmp_path / "out"
    _make_run(runs_dir, "A_1")
    out.mkdir()
    (out / "old.json").write_text("{}")
    with pytest.raises(SystemExit):
        ar.analyse(runs_dir, out)
    with pytest.raises(SystemExit):
        ar.analyse(tmp_path / "missing", tmp_path / "out2")


def test_incomplete_set_flagged_and_summaries_written(tmp_path):
    runs_dir, out = tmp_path / "runs", tmp_path / "out"
    d = _make_run(runs_dir, "A_1", rounds=(4, 5))
    meta = {"status": "ok", "rounds_completed": 2,
            "output_stats": {"definition": "chars of full outputs", "agents": {"PI": {"turns": 3, "chars": 900}}}}
    (d / "meta.json").write_text(json.dumps(meta), encoding="utf-8")
    _make_run(runs_dir, "B_1", rounds=(5,))
    summary = ar.analyse(runs_dir, out, expected_per_condition=5)
    assert summary["complete_main_set"] is False and any("incomplete" in i for i in summary["issues"])
    cs = json.loads((out / "condition_summary.json").read_text(encoding="utf-8"))
    assert cs["A"]["termination_round_distribution"] == {"2": 1} and cs["B"]["all_five_reached_runs"] == 1
    with (out / "output_stats.csv").open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert rows[0]["agent"] == "PI" and rows[0]["chars"] == "900"



def test_runs_without_success_keep_reasons(tmp_path):
    d = _make_run(tmp_path / "runs", "A_1", status="failed")
    (d / "meta.json").write_text(json.dumps({"status": "failed", "error": {"type": "SearchError", "message": "down"}}),
                                 encoding="utf-8")
    summary = ar.analyse(tmp_path / "runs", tmp_path / "out", expected_per_condition=None)
    ex = summary["excluded_runs"][0]
    assert ex["name"] == "A_1" and ex["failed_attempts"][0]["error_type"] == "SearchError"


def test_empty_extraction_makes_set_incomplete(tmp_path):
    runs_dir, out = tmp_path / "runs", tmp_path / "out"
    _make_run(runs_dir, "A_1", tag="a")
    d = _make_run(runs_dir, "A_2", tag="b")
    (d / "final_report.md").write_text("# Title\n\n## Methods\nonly methods\n", encoding="utf-8")

    def embed(texts):
        return np.vstack([np.ones(4) + 0.01 * i for i in range(len(texts))])

    summary = ar.analyse(runs_dir, out, embed=embed, expected_per_condition=None)
    rep = json.loads((out / "representative.json").read_text(encoding="utf-8")) if (out / "representative.json").exists() else None
    assert summary["complete_main_set"] is False
    assert any("no extractable content" in i for i in summary["issues"])
    assert rep is None or rep.get("complete_main_set") is False


def test_all_candidates_listed():
    runs = [{"name": "A_1", "condition": "A", "scores": [{"round": 1, "scores": {}}], "dir": None}]
    text = " ".join(f"Readability {i % 5 + 1}/5." for i in range(40))
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp)
        (p / "calls.jsonl").write_text(json.dumps({"tag": {"agent": "Critic", "round": 1}, "user_message": text}),
                                       encoding="utf-8")
        runs[0]["dir"] = p
        audit = ar.leakage_audit(runs)
    assert audit["runs"]["A_1"]["candidate_mentions"] == 40 and len(audit["examples"]) == 40


def test_extraction_keeps_extra_content_sections():
    report = REPORT.format(tag="x") + "\n## Explanatory Notes for the Decision Framework\n\nEdit classification notes.\n"
    text = ar.extract_content(report)
    assert "Edit classification notes" in text and "Team composition" not in text


def test_detector_ignores_list_markers_and_placeholder(tmp_path):
    _make_run(tmp_path, "A_1", rounds=(4,), critic_inputs=["Concrete actions to reach [score]: (1) Gloss. readability [score] from [score]. (2) Recast"])
    runs, _ = ar.load_runs(tmp_path)
    assert ar.leakage_audit(runs)["runs"]["A_1"]["candidate_mentions"] == 0


def test_extraction_excludes_template_subtrees_and_unicode_headings():
    report = ("# T\n\n## Team Composition\nrole table\n\n## Core Question 1: X\nKeep this.\n\n"
              "### Team Composition\nnested table\n#### Role-frequency Analysis\nfrequency rows\n"
              "### Notes\nkeep notes\n\n## Per\u2011agent Contribution Statistics\nstats\n")
    text = ar.extract_content(report)
    assert "Keep this." in text and "keep notes" in text
    for bad in ("role table", "nested table", "frequency rows", "stats"):
        assert bad not in text, bad



def test_audit_reports_candidates_by_channel(tmp_path):
    msg = ("[Team meeting Round 2 — critique stage]\n\n[Per-specialist analyses]\nmy readability was 4/5 before\n"
           "\n## [Web search results — verification context]\nweb text\n\n[Prior-round critique records]\n"
           "Readability: 4 overall\n\nReview each specialist's analysis individually")
    _make_run(tmp_path, "A_1", rounds=(4,), critic_inputs=[msg])
    runs, _ = ar.load_runs(tmp_path)
    r = ar.leakage_audit(runs)
    ch = r["runs"]["A_1"]["candidates_by_channel"]
    assert ch["specialist_outputs"] == 1 and ch["prior_feedback"] == 1 and ch["instructions"] == 0
    assert {e["channel"] for e in r["examples"]} == {"specialist_outputs", "prior_feedback"}
    assert "Pass: 0 confirmed" in r["pass_criteria"]


def test_detector_catches_parenthesised_score_but_not_list_marker(tmp_path):
    _make_run(tmp_path, "A_1", rounds=(4,), critic_inputs=["readability holds at (4). Next: (2) Recast the sentence"])
    runs, _ = ar.load_runs(tmp_path)
    assert ar.leakage_audit(runs)["runs"]["A_1"]["candidate_mentions"] == 1


def test_attempt_selection(tmp_path):
    _make_run(tmp_path, "A_1", attempt="attempt_02")
    _make_run(tmp_path, "A_1", attempt="attempt_03")
    runs, issues = ar.load_runs(tmp_path)
    assert runs == [] and issues                                  # two successful attempts -> excluded
    runs, issues = ar.load_runs(tmp_path, attempt="attempt_03")
    assert [r["attempt"] for r in runs] == ["attempt_03"] and not issues
