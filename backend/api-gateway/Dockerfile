# syntax=docker/dockerfile:1

FROM cgr.dev/chainguard/python:latest-dev AS builder

WORKDIR /build
COPY api-gateway/requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM cgr.dev/chainguard/python:latest

WORKDIR /app

COPY --from=builder /install /usr/local
COPY api-gateway/app ./app
COPY api-gateway/db ./db
COPY agent_service /agent_service
COPY planner_service /planner_service
COPY evaluation_service /evaluation_service
COPY graph_service /graph_service
COPY memory_service /memory_service

ENV PYTHONPATH=/app:/
ENV PYTHONUNBUFFERED=1
EXPOSE 8000

USER nonroot

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
