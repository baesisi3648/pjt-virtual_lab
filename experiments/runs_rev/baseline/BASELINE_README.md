# Baseline record (2026-11-05T08:37:06Z UTC)
cwd: /c/Users/user/OneDrive/바탕 화면/배성우/projects/pjt-virtual_lab
commit: ca4b833c8845f98db76213d40d5290d3acfd8684

## git status --short
 M .gitignore
 M requirements.txt
?? .codex/
?? AGENTS.md
?? docs/paper-methods-corrections.md
?? experiments/runs_rev/
?? virtual_lab.db

## git diff (tracked)
diff --git a/.gitignore b/.gitignore
index 9d257d5..cb7300e 100644
--- a/.gitignore
+++ b/.gitignore
@@ -11,6 +11,7 @@ build/
 # Virtual Environment
 .venv/
 venv/
+venv_broken_oldpc/
 env/
 
 # Environment Variables
diff --git a/requirements.txt b/requirements.txt
index 7187922..ed302de 100644
--- a/requirements.txt
+++ b/requirements.txt
@@ -7,6 +7,9 @@ langgraph>=0.2.0
 # ── OpenAI ─────────────────────────────────────────────────────────────────
 openai>=1.50.0
 
+# ── Anthropic (Scientific Critic, revision) ────────────────────────────────
+anthropic>=2.5.0
+
 # ── Vector DB ──────────────────────────────────────────────────────────────
 pinecone[grpc]>=5.0.0          # rag/pinecone_client.py (PineconeGRPC)
 # chromadb>=0.5.0              # Python 3.14 비호환 (Pydantic V1 충돌) — Pinecone 사용 시 불필요

## pytest command
venv/Scripts/python.exe -m pytest tests/ -q -p no:cacheprovider --continue-on-collection-errors  (exit code: non-zero; 66 failed, 61 passed, 3 skipped, 4 errors)
env: .env present with OPENAI/ANTHROPIC/PINECONE/TAVILY keys (values not recorded)

## legacy test status
Legacy tests are not fixed. Collection errors: hard-coded old worktree paths. Failures: outdated APIs (get_gpt4o, Chroma), deployment config, live-key order dependence. test_invalid_json_defaults_to_approve conflicts with the new fail-closed policy and must not be made to pass. Focused revision tests will be added under tests/revision/.

## old venv
venv_broken_oldpc/ pointed to Python 3.14.3 on another PC; not evidence of the original run environment.
