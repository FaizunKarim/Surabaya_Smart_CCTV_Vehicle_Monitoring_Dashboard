#!/usr/bin/env bash
set -euo pipefail

export PORT="${PORT:-7860}"
export HF_SPACE_MODE="${HF_SPACE_MODE:-true}"
export RUN_EMBEDDED_VISION_WORKER="${RUN_EMBEDDED_VISION_WORKER:-false}"

./start-worker.sh &
WORKER_PID=$!

cleanup() {
  kill "${WORKER_PID}" >/dev/null 2>&1 || true
}

trap cleanup EXIT

./start-api.sh
