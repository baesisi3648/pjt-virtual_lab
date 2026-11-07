#!/usr/bin/env bash
# Run the main experiment in manifest order (revision_plan 7.3, step 10).
# Each run is a new Python process; a failed attempt is retried immediately, up to the
# manifest's max attempts (attempts excluded by a manifest amendment are not counted).
# Before each attempt one minimal OpenAI request checks the credit balance; if the API
# reports insufficient_quota the driver stops without starting the attempt.
# If run_experiment.py refuses to start (no new attempt folder), the driver stops.
set -u
cd "$(dirname "$0")/../.."
MANIFEST=${1:-experiments/runs_rev/experiment_manifest.json}
PY=venv/Scripts/python.exe
MAIN=$("$PY" -c "import json;print(json.load(open('$MANIFEST',encoding='utf-8')).get('out_dir','experiments/runs_rev/main'))" | tr -d '\r')
LOGS="${MAIN}_logs"
SNAP=$("$PY" -c "import json;print(json.load(open('$MANIFEST',encoding='utf-8'))['retrieval']['snapshot_path'])" | tr -d '\r')
mkdir -p "$LOGS"
unset VIRTUAL_LAB_PROMPTS_DIR VIRTUAL_LAB_CRITIC_MODE VIRTUAL_LAB_CRITIC_PROVIDER \
      VIRTUAL_LAB_RETRIEVAL_MODE VIRTUAL_LAB_RETRIEVAL_SNAPSHOT VIRTUAL_LAB_TEMPERATURE \
      CRITIC_MODEL CRITIC_EFFORT
export PYTHONIOENCODING=utf-8

ORDER=$("$PY" -c "import json;[print(e['condition'],e['run_id']) for e in sorted(json.load(open('$MANIFEST',encoding='utf-8'))['order'],key=lambda e:e['seq'])]" | tr -d '\r')

next_attempt() {
  "$PY" -c "
import json, sys
from pathlib import Path
sys.path.insert(0, '.')
from utils import manifest as mf
m = json.load(open('$MANIFEST', encoding='utf-8'))
print(mf.next_attempt(m, '$1', '$2', Path('$MAIN')))" | tr -d '\r'
}

preflight() {
  # Same key resolution as run_experiment.py: environment first, then .env (load_dotenv without override).
  "$PY" -c "
import json, os, time, httpx
from dotenv import load_dotenv
load_dotenv('.env')
rec = {'time': time.strftime('%Y-%m-%dT%H:%M:%S%z'), 'run': '$1', 'attempt': '$2'}
try:
    r = httpx.post('https://api.openai.com/v1/chat/completions',
                   headers={'Authorization': 'Bearer ' + os.environ.get('OPENAI_API_KEY', '').strip()},
                   json={'model': os.environ.get('GPT_MODEL', 'gpt-4o'), 'messages': [{'role': 'user', 'content': 'OK'}],
                         'max_completion_tokens': 16}, timeout=60)
    rec.update(http_status=r.status_code, request_id=r.headers.get('x-request-id'))
    try:
        j = r.json()
    except Exception:
        j = {}
    err = j.get('error') or {}
    rec.update(type=err.get('type'), code=err.get('code'), model=j.get('model'), usage=j.get('usage'))
    result = 'ok' if r.status_code == 200 else (err.get('type') or 'http_' + str(r.status_code))
except Exception as e:
    result = 'error:' + type(e).__name__
rec['result'] = result
open('$LOGS/preflight.jsonl', 'a', encoding='utf-8').write(json.dumps(rec) + '\n')
print(result)" | tr -d '\r'
}

while read -r COND RUN; do
  while true; do
    ATT=$(next_attempt "$COND" "$RUN")
    case "$ATT" in
      done) break ;;
      exhausted) echo "$(date '+%F %T') ${COND}_${RUN} exhausted counted attempts; reported as missing"; break ;;
    esac
    PF=$(preflight "${COND}_${RUN}" "$ATT")
    if [ "$PF" != "ok" ]; then
      echo "$(date '+%F %T') STOP before ${COND}_${RUN} attempt $ATT: OpenAI preflight returned $PF (no attempt started)"
      exit 3
    fi
    echo "$(date '+%F %T') start ${COND}_${RUN} attempt $ATT (preflight: $PF)"
    DIR="$MAIN/${COND}_${RUN}/attempt_$(printf %02d "$ATT")"
    "$PY" -B run_experiment.py --condition "$COND" --run-id "$RUN" --attempt "$ATT" \
        --out-dir "$MAIN" --retrieval-snapshot "$SNAP" --manifest "$MANIFEST" > "$LOGS/${COND}_${RUN}_attempt_$(printf %02d "$ATT").log" 2>&1
    CODE=$?
    if [ ! -d "$DIR" ]; then
      echo "$(date '+%F %T') REFUSED ${COND}_${RUN} attempt $ATT (exit $CODE); see the log. Stopping."
      exit 2
    fi
    echo "$(date '+%F %T') end   ${COND}_${RUN} attempt $ATT exit=$CODE"
  done
done <<< "$ORDER"
echo "$(date '+%F %T') all runs processed"
