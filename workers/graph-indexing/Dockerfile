# syntax=docker/dockerfile:1
# Build from repo root: docker build -f workers/graph-indexing/Dockerfile .

FROM cgr.dev/chainguard/python:latest-dev AS builder

WORKDIR /build
RUN pip install --no-cache-dir --prefix=/install httpx

FROM cgr.dev/chainguard/python:latest

WORKDIR /app

COPY --from=builder /install /usr/local
COPY backend/graph_service /graph_service
COPY workers/graph-indexing/worker.py ./worker.py

ENV PYTHONPATH=/app:/
ENV PATH="/usr/local/bin:${PATH}"

USER nonroot

CMD ["python", "worker.py"]
