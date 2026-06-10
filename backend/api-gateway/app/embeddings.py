"""Embedding generation via vLLM with deterministic fallback."""

import hashlib

import httpx

from app.config import settings
from app.model_router import resolve_model, vllm_headers

EMBED_DIM = 1024


def _stub_vec(text: str) -> list[float]:
    h = int(hashlib.sha256(text.encode()).hexdigest()[:8], 16)
    return [((h + i) % 997) / 997.0 for i in range(EMBED_DIM)]


async def embed_texts(texts: list[str]) -> list[list[float]]:
    model = resolve_model("embedding", settings.embedding_model)
    body = {"model": model, "input": texts}
    url = f"{settings.vllm_base_url.rstrip('/')}/embeddings"
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(url, json=body, headers=vllm_headers())
            if resp.status_code >= 400:
                return [_stub_vec(t) for t in texts]
            data = resp.json().get("data", [])
            out: list[list[float]] = []
            for item in sorted(data, key=lambda x: x.get("index", 0)):
                vec = item.get("embedding", [])
                if len(vec) != EMBED_DIM:
                    out.append(_stub_vec(texts[len(out)]))
                else:
                    out.append(vec)
            while len(out) < len(texts):
                out.append(_stub_vec(texts[len(out)]))
            return out
    except httpx.HTTPError:
        return [_stub_vec(t) for t in texts]
