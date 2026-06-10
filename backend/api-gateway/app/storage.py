"""MinIO object storage for workspace snapshots."""

import io
from typing import Any

from app.config import settings

_client: Any = None


def _get_client():
    global _client
    if _client is None:
        from minio import Minio

        endpoint = settings.minio_endpoint.replace("http://", "").replace("https://", "")
        secure = settings.minio_endpoint.startswith("https")
        _client = Minio(
            endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=secure,
        )
        bucket = settings.minio_bucket
        if not _client.bucket_exists(bucket):
            _client.make_bucket(bucket)
    return _client


def put_object(key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
    client = _get_client()
    client.put_object(settings.minio_bucket, key, io.BytesIO(data), len(data), content_type=content_type)
    return key


def get_object(key: str) -> bytes:
    client = _get_client()
    resp = client.get_object(settings.minio_bucket, key)
    try:
        return resp.read()
    finally:
        resp.close()
        resp.release_conn()
