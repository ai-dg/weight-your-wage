#!/bin/bash
set -e
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$ROOT"
echo "3.12" > .python-version
uv python install 3.12
[ -d .venv ] && rm -rf .venv
uv sync