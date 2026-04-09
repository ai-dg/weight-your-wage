FROM pytorch/pytorch:2.5.1-cuda12.4-cudnn9-runtime
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV UV_SYSTEM_PYTHON=1
ENV PYTHONPATH=/app/srcs

WORKDIR /app/

COPY pyproject.toml uv.lock /app/

RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --system --no-cache -e .

EXPOSE 4243

CMD ["uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "4243"]
