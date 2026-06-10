# syntax=docker/dockerfile:1
# Sandbox needs docker CLI + Python; Chainguard wolfi base keeps CVE count low.

FROM cgr.dev/chainguard/wolfi-base:latest AS base

USER root
RUN apk add --no-cache python-3.12 py3-pip docker-cli

FROM base AS builder
WORKDIR /app
RUN pip install --no-cache-dir --prefix=/install fastapi "uvicorn[standard]"

FROM base

WORKDIR /app
COPY --from=builder /install /usr/local
COPY main.py .

ENV PYTHONUNBUFFERED=1
ENV PATH="/usr/local/bin:${PATH}"
EXPOSE 8010

# Root required for /var/run/docker.sock access in dev compose.
USER root

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8010"]
