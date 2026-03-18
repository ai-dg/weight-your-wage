FROM debian:latest

RUN apt-get update && apt-get upgrade -y

RUN apt-get install -y curl procps && curl -LsSf https://astral.sh/uv/install.sh | sh

ENV PATH=$PATH:/root/.local/bin
ENV PYTHONUNBUFFERED=1 

COPY pyproject.toml /app/
COPY srcs/api/ /app/

WORKDIR /app/

RUN uv python install 3.12

ENV PYTHONPATH=/app/.venv/lib/python3.12/site-packages

RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
