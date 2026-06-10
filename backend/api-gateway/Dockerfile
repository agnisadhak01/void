# syntax=docker/dockerfile:1

FROM cgr.dev/chainguard/python:latest-dev AS builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM cgr.dev/chainguard/python:latest

WORKDIR /app

COPY --from=builder /install /usr/local
COPY app ./app
COPY db ./db

ENV PYTHONUNBUFFERED=1
ENV PATH="/usr/local/bin:${PATH}"
EXPOSE 8000

USER nonroot

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
