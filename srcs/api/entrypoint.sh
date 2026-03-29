#!/bin/sh
set -e
uv python install 3.12 2>/dev/null || true

# Host-mounted uv venv often points to /home/<user>/.local/share/uv/python.
# Mirror that path to the container uv install so /app/.venv/bin/python works.
if [ -d /root/.local/share/uv/python ]; then
	mkdir -p /home/steven/.local/share/uv
	ln -sfn /root/.local/share/uv/python /home/steven/.local/share/uv/python
fi

if [ -x /app/.venv/bin/python ]; then
	echo "Starting uvicorn with mounted venv /app/.venv/bin/python" 1>&2
	exec /app/.venv/bin/python -m uvicorn api.app:app --host 0.0.0.0 --port 4243
fi

CONTAINER_PYTHON=/root/.local/share/uv/python/cpython-3.12-linux-x86_64-gnu/bin/python3
[ -x "$CONTAINER_PYTHON" ] || CONTAINER_PYTHON=$(find /root/.local/share/uv/python -path '*/bin/python3' 2>/dev/null | head -1)
if [ -n "$CONTAINER_PYTHON" ]; then
	echo "Starting uvicorn with $CONTAINER_PYTHON" 1>&2
	exec "$CONTAINER_PYTHON" -m uvicorn api.app:app --host 0.0.0.0 --port 4243
fi
echo "Fallback: uv run uvicorn" 1>&2
exec uv run uvicorn api.app:app --host 0.0.0.0 --port 4243
