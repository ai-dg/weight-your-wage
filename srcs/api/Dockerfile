FROM debian:bookworm-slim

RUN apt-get update && apt-get upgrade -y
RUN apt-get install -y python3
RUN apt-get install -y python3-pip
RUN apt-get install -y python3-venv
RUN apt-get install -y curl procps util-linux

# ENV PATH=$PATH:/root/.local/bin
# ENV PYTHONUNBUFFERED=1

COPY pyproject.toml uv.lock /app/

WORKDIR /app/

# Compte système aligné sur UID/GID (sinon getpass.getpwuid → KeyError avec PyTorch / torch.compile)
ARG UID=1000
ARG GID=1000
RUN groupadd --gid "${GID}" appuser \
	&& useradd --uid "${UID}" --gid appuser --home-dir /app --no-create-home --shell /bin/sh appuser
RUN chown -R "${UID}:${GID}" /app
ENV APP_UID=${UID} APP_GID=${GID}
ENV HOME=/app
ENV USER=appuser
ENV LOGNAME=appuser
ENV UV_CACHE_DIR=/app/.cache/uv
# .venv est souvent un bind mount : éviter les symlinks invalides hors conteneur
ENV UV_LINK_MODE=copy
ENV PYTHONPATH=/app/srcs

# RUN uv python install 3.12 \
# 	&& mkdir -p /opt \
# 	&& cp -a /root/.local/share/uv/python /opt/uv-python \
# 	&& chmod -R a+rX /opt/uv-python

# ENV PYTHONPATH=/app/.venv/lib/python3.12/site-packages

# RUN chmod +x /app/api/entrypoint.sh

ENTRYPOINT ["/bin/sh", "/app/srcs/api/entrypoint.sh"]
