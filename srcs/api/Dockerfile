FROM debian:latest

RUN apt-get update && apt-get upgrade -y
RUN apt-get install -y python3
RUN apt-get install -y python3-pip
RUN apt-get install -y python3-venv
RUN apt-get install -y curl procps

# RUN pip install uv

# RUN curl -LsSf https://astral.sh/uv/install.sh | sh


# ENV PATH=$PATH:/root/.local/bin
# ENV PYTHONUNBUFFERED=1

COPY pyproject.toml /app/

WORKDIR /app/

# Permet à l'utilisateur non-root (voir docker-compose user: UID:GID) d'écrire .venv dans /app
ARG UID=1000
ARG GID=1000
RUN chown -R "${UID}:${GID}" /app
USER ${UID}:${GID}
ENV HOME=/app
ENV UV_CACHE_DIR=/app/.cache/uv

# RUN uv python install 3.12 \
# 	&& mkdir -p /opt \
# 	&& cp -a /root/.local/share/uv/python /opt/uv-python \
# 	&& chmod -R a+rX /opt/uv-python

# ENV PYTHONPATH=/app/.venv/lib/python3.12/site-packages

# RUN chmod +x /app/api/entrypoint.sh

ENTRYPOINT ["/bin/sh", "/app/api/entrypoint.sh"]
