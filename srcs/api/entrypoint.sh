#!/bin/sh
set -e

python3 -m venv .uv-tool
.uv-tool/bin/python -m pip install --no-cache-dir --upgrade pip
.uv-tool/bin/python -m pip install --no-cache-dir uv
export PATH="/app/.uv-tool/bin:$PATH"

uv python install 3.12
uv sync
exec uv run uvicorn api.app:app --host 0.0.0.0 --port 4243
