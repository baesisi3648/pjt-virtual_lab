# Virtual Lab for the Safety Assessment of Genome-Edited Foods

Code, prompts, and analysis for the manuscript "Agentic AI Orchestration for the Safety
Assessment of Genome-Edited Foods" (Ham, Bae and Kim).

The system is a multi-agent workflow in which a PI agent assembles a panel of specialist
agents, the specialists draft and revise a safety-assessment framework over several rounds,
and a Scientific Critic scores and comments on each specialist's contribution.

## System

| Role | Model | Task |
|---|---|---|
| PI agent | GPT-5 (`gpt-5-2025-08-07`) | Selects the specialist panel, summarizes each round, writes the final report |
| Specialist agents | GPT-5 (`gpt-5-2025-08-07`) | Analyse the research agenda with retrieval, revise in later rounds |
| Scientific Critic | Claude Opus 5 (`claude-opus-5`, effort high) | Scores each specialist on four dimensions and gives feedback |

- The Critic scores evidence, universality, proportionality and readability on a 1–5 scale.
  The rubric is in `prompts_A/data/critique_rubric.md`.
- Each round runs specialist analysis or revision, Critic review and a PI summary. The workflow
  stops when every specialist receives 5 on all four dimensions, or after round 7
  (`workflow/graph.py`).
- Retrieval uses a Pinecone index of regulatory documents, Tavily web search and a search
  scoped to the EFSA Journal. The study runs read these results from a fixed retrieval snapshot.
- GPT-5 requests send no temperature or reasoning-effort parameter, so provider defaults apply.
  Every call, its parameters and the model identifier returned by the provider are logged.

## Prompts

| Folder | Content |
|---|---|
| `prompts_A/` | Prompt set of the final protocol reported in the manuscript |
| `prompts_B/` | Comparison prompt set that differs from `prompts_A/` only in `system/critic.md` |
| `prompts.example/` | Short placeholders that let the code run without the study prompts |

`prompts_A/` and `prompts_B/` are built by `scripts/revision/build_prompt_sets.py`.
Select a set with the environment variable `VIRTUAL_LAB_PROMPTS_DIR`.

## Reproducing the study

```bash
git clone -c core.autocrlf=true https://github.com/baesisi3648/pjt-virtual_lab.git
cd pjt-virtual_lab
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # add OPENAI_API_KEY, ANTHROPIC_API_KEY, TAVILY_API_KEY, PINECONE_*
```

One run is one process. The study runs were started as follows:

```bash
python -B run_experiment.py --condition A --run-id 1 --attempt 1 \
    --manifest experiments/runs_rev/experiment_manifest_v2.json --out-dir experiments/runs_rev/main_v1 \
    --retrieval-snapshot experiments/runs_rev/retrieval_snapshot_v1.json
python -B -m experiments.reproducibility.analyze_revision \
    --runs-dir experiments/runs_rev/main_v1 --out-dir <new folder>
```

A run checked against the manifest starts only when the code, prompts, retrieval snapshot,
models, Python (3.12.10) and package versions match those recorded in the manifest. The file
hashes were taken from a checkout with Windows line endings, hence `core.autocrlf=true` above.
The original retrieval snapshot contains third-party text and is not redistributed (see Data),
so this check cannot be passed with the public files alone. For a new run, obtain the 19 source
documents listed in `experiments/runs_rev/corpus_v1/corpus_manifest.json` (file name, source
and SHA-256 of each) and place them in `reference/revision/corpus_v1/raw/`, rebuild the
Pinecone index (`scripts/revision/build_corpus_v1.py`), build a new snapshot
(`scripts/revision/build_retrieval_snapshot.py --out <file>`), and run without `--manifest`,
passing that snapshot and a new folder (`--retrieval-snapshot <file> --out-dir
experiments/runs_rev/new_runs`). The analysis runs without API calls when
`--skip-embeddings` is added (similarity is then not recomputed).
The full procedure, the manifest checks and the description of every output file are in
`experiments/README.md`. The run log is `experiments/runs_rev/RUN_LOG.md`.

## Data

- Analysis results used in the manuscript are in `experiments/runs_rev/results_v1/`, and the
  corpus manifest is in `experiments/runs_rev/corpus_v1/`.
- The complete per-round records of every run (call logs, conversations, Critic scores, final
  reports, metadata) are archived at [DOI]. The package is built by
  `scripts/revision/build_release.py`. Excerpts of third-party documents in the retrieval inputs
  are replaced by their source, length and SHA-256, and the documents can be retrieved from the
  listed sources. The published records therefore support reanalysis of the saved outputs but
  not an exact replay of the retrieval inputs.

## Web interface (optional)

A FastAPI backend and a Next.js frontend run the workflow interactively. They use the default
settings, not the study protocol. Use `run_experiment.py` to run the study protocol.

```bash
python -B -m uvicorn server:app --host 0.0.0.0 --port 8000
cd frontend && npm install && npm run dev      # http://localhost:3000
```

## Tests

```bash
pytest tests/revision -v
```

Tests outside `tests/revision/` belong to the pre-revision code and are not maintained
(`experiments/runs_rev/baseline/BASELINE_README.md`).

## License

MIT (see `LICENSE`).
