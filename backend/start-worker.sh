#!/usr/bin/env bash
set -euo pipefail

exec python -m app.workers.vision_worker
