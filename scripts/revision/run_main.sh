#!/usr/bin/env bash
# Run the main experiment in manifest order (revision_plan 7.3, step 10).
# Each run is a new Python process; a failed attempt is retried immediately, up to the
# manifest's max attempts. If run_experiment.py refuses to start (no new attempt folder),
# the driver stops: that is a configuration problem, not a failed attempt.
set -u
cd "$(dirname "$0")/../.."
MANIFEST=experiments/runs_rev/experiment_manifest.json
MAIN=experiments/runs_rev/main
LOGS=experiments/runs_rev/main_logs
PY=venv/Scripts/python.exe
mkdir -p "$LOGS"
unset VIRTUAL_LAB_PROMPTS_DIR VIRTUAL_LAB_CRITIC_MODE VIRTUAL_LAB_CRITIC_PROVIDER \
      VIRTUAL_LAB_RETRIEVAL_MODE VIRTUAL_LAB_RETRIEVAL_SNAPSHOT VIRTUAL_LAB_TEMPERATURE \
      CRITIC_MODEL CRITIC_EFFORT
export PYTHONIOENCODING=utf-8

MAX=$("$PY" -c "import json;print(json.load(open('$MANIFEST',encoding='utf-8'))['retry_policy']['max_attempts_per_run'])" | tr -d '\r')
ORDER=$("$PY" -c "import json;[print(e['condition'],e['run_id']) for e in sorted(json.load(open('$MANIFEST',encoding='utf-8'))['order'],key=lambda e:e['seq'])]" | tr -d '\r')

while read -r COND RUN; do
  for ((ATT=1; ATT<=MAX; ATT++)); do
    DIR="$MAIN/${COND}_${RUN}/attempt_$(printf %02d "$ATT")"
    [ -d "$DIR" ] && grep -q '"status": "ok"' "$DIR/meta.json" 2>/dev/null && break   # already done
    [ -d "$DIR" ] && continue                                                         # earlier failed attempt
    echo "$(date '+%F %T') start ${COND}_${RUN} attempt $ATT"
    "$PY" -B run_experiment.py --condition "$COND" --run-id "$RUN" --attempt "$ATT" \
        --manifest "$MANIFEST" > "$LOGS/${COND}_${RUN}_attempt_$(printf %02d "$ATT").log" 2>&1
    CODE=$?
    if [ ! -d "$DIR" ]; then
      echo "$(date '+%F %T') REFUSED ${COND}_${RUN} attempt $ATT (exit $CODE); see the log. Stopping."
      exit 2
    fi
    echo "$(date '+%F %T') end   ${COND}_${RUN} attempt $ATT exit=$CODE"
    [ $CODE -eq 0 ] && break
    [ $ATT -eq $MAX ] && echo "$(date '+%F %T') ${COND}_${RUN} exhausted $MAX attempts; reported as missing"
  done
done <<< "$ORDER"
echo "$(date '+%F %T') all runs processed"
