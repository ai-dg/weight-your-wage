FROM debian:bookworm-slim

RUN apt-get update && apt-get upgrade -y && \
	apt-get install -y curl procps && \
	curl -LsSf https://astral.sh/uv/install.sh | sh && \
	rm -rf /var/lib/apt/lists/*

ENV PATH=$PATH:/root/.local/bin
ENV PYTHONUNBUFFERED=1 

COPY pyproject.toml /app/
COPY srcs/api/ /app/api

WORKDIR /app/

RUN uv python install 3.12

ENV PYTHONPATH=/app/.venv/lib/python3.12/site-packages

RUN chmod +x /app/api/entrypoint.sh

ENTRYPOINT ["/app/api/entrypoint.sh"]
