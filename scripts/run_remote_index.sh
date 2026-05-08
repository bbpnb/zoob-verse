#!/usr/bin/env bash
set -euo pipefail

WORKDIR="${ZOOB_VERSE_WORKDIR:-/root/code/zoob-verse}"

if [ "$#" -lt 5 ]; then
  echo "usage: run_remote_index.sh <corpus> <model> <run_name> <novel_path> <log_dir>" >&2
  exit 2
fi

CORPUS="$1"
MODEL="$2"
RUN_NAME="$3"
NOVEL_PATH="$4"
LOG_DIR="$5"

mkdir -p "$LOG_DIR"
cd "$WORKDIR"
source "$WORKDIR/.venv/bin/activate"

python -m src jinyong index \
  --novel "$NOVEL_PATH" \
  --corpus "$CORPUS" \
  --model "$MODEL" \
  --run-name "$RUN_NAME" \
  > "$LOG_DIR/index.log" 2>&1

RUN_DIR="runs/jinyong/${CORPUS}/${MODEL}/lightrag/${RUN_NAME}"

python -m src jinyong normalize-graph --run-dir "$RUN_DIR" >> "$LOG_DIR/index.log" 2>&1
python -m src jinyong audit-graph --run-dir "$RUN_DIR" >> "$LOG_DIR/index.log" 2>&1
python -m src jinyong visualize \
  --input "$RUN_DIR/graph.normalized.json" \
  --output "$RUN_DIR/graph.html" \
  >> "$LOG_DIR/index.log" 2>&1
python -m src jinyong report --run-dir "$RUN_DIR" >> "$LOG_DIR/index.log" 2>&1
