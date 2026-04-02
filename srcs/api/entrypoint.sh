#!/bin/sh
set -e

APP_UID="${APP_UID:-1000}"
APP_GID="${APP_GID:-1000}"

# Bind mount model/ peut être root:root sur l'hôte : correction une fois au démarrage, puis exécution non-root.
if [ "$(id -u)" = 0 ]; then
	mkdir -p /app/srcs/model/datasets
	chown -R "${APP_UID}:${APP_GID}" /app/srcs/model
	# CSV/cache écrits par pandas : droits lecture/écriture sur tout le volume model (bind mount hôte)
	chmod -R u+rwX /app/srcs/model 2>/dev/null || true
	chown -R "${APP_UID}:${APP_GID}" /app/.uv-tool 2>/dev/null || true
	# --clear-groups évite --init-groups (qui exige une entrée /etc/passwd pour l’UID).
	exec setpriv --reuid="${APP_UID}" --regid="${APP_GID}" --clear-groups -- /bin/sh /app/srcs/api/entrypoint.sh
fi

# getpass.getuser() (PyTorch inductor) sans entrée passwd : forcer le nom logique
export USER="${USER:-appuser}"
export LOGNAME="${LOGNAME:-appuser}"
export PYTHONPATH="/app/srcs${PYTHONPATH:+:$PYTHONPATH}"
# srcs/.venv (hôte) monté ici : un seul venv pour uv + uv sync
export UV_PROJECT_ENVIRONMENT=/app/.uv-tool

cd /app
UV_ENV=/app/.uv-tool
# Montage srcs/.venv : peut être vide, ou cassé (pyvenv.cfg sans bin/python)
if [ ! -x "$UV_ENV/bin/python" ] && [ ! -x "$UV_ENV/bin/python3" ]; then
	# venv absent ou incomplet (ex. pyvenv.cfg sans binaires)
	rm -rf "${UV_ENV:?}"/* 2>/dev/null || true
	python3 -m venv "$UV_ENV"
fi
if [ -e "$UV_ENV/bin/python" ] && [ ! -e "$UV_ENV/bin/python3" ]; then
	ln -sf python "$UV_ENV/bin/python3"
fi
"$UV_ENV/bin/python" -m pip install --no-cache-dir --upgrade pip
"$UV_ENV/bin/python" -m pip install --no-cache-dir uv
export PATH="$UV_ENV/bin:$PATH"

uv python install 3.12
uv sync
exec uv run uvicorn api.app:app --host 0.0.0.0 --port 4243
