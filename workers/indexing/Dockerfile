# syntax=docker/dockerfile:1

FROM cgr.dev/chainguard/python:latest-dev AS builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM cgr.dev/chainguard/python:latest

WORKDIR /app

COPY --from=builder /install /usr/local
COPY worker.py .

ENV PATH="/usr/local/bin:${PATH}"

USER nonroot

CMD ["python", "worker.py"]
