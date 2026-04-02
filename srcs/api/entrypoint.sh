#!/bin/sh
set -e

APP_UID="${APP_UID:-1000}"
APP_GID="${APP_GID:-1000}"

# Bind mount model/ peut être root:root sur l'hôte : correction une fois au démarrage, puis exécution non-root.
if [ "$(id -u)" = 0 ]; then
	mkdir -p /app/model/datasets
	chown -R "${APP_UID}:${APP_GID}" /app/model
	# --clear-groups évite --init-groups (qui exige une entrée /etc/passwd pour l’UID).
	exec setpriv --reuid="${APP_UID}" --regid="${APP_GID}" --clear-groups -- /bin/sh /app/api/entrypoint.sh
fi

python3 -m venv .uv-tool
.uv-tool/bin/python -m pip install --no-cache-dir --upgrade pip
.uv-tool/bin/python -m pip install --no-cache-dir uv
export PATH="/app/.uv-tool/bin:$PATH"

uv python install 3.12
uv sync
exec uv run uvicorn api.app:app --host 0.0.0.0 --port 4243
