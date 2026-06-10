"""File indexing worker — watches workspace and pushes chunks to gateway."""

import hashlib
import os
import time
from pathlib import Path

import httpx

GATEWAY_URL = os.environ.get("GATEWAY_URL", "http://127.0.0.1:8000")
PROJECT_ID = os.environ.get("PROJECT_ID", "00000000-0000-0000-0000-000000000001")
WATCH_PATH = os.environ.get("WATCH_PATH", ".")
CHUNK_SIZE = 1500
SCAN_INTERVAL = int(os.environ.get("SCAN_INTERVAL", "60"))
EXTENSIONS = {".ts", ".tsx", ".js", ".jsx", ".py", ".go", ".rs", ".md", ".json", ".yaml", ".yml"}


def chunk_text(text: str, size: int = CHUNK_SIZE) -> list[str]:
    return [text[i : i + size] for i in range(0, len(text), size)] or [text]


def stub_embedding(text: str) -> list[float]:
    h = int(hashlib.sha256(text.encode()).hexdigest()[:8], 16)
    return [((h + i) % 997) / 997.0 for i in range(1024)]


def index_file(client: httpx.Client, path: Path) -> None:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return
    if len(text) > 500_000:
        text = text[:500_000]
    chunks = chunk_text(text)
    embeddings = [stub_embedding(c) for c in chunks]
    rel = str(path).replace("\\", "/")
    resp = client.post(
        f"{GATEWAY_URL}/v1/context/index",
        json={
            "project_id": PROJECT_ID,
            "path": rel,
            "chunks": chunks,
            "embeddings": embeddings,
        },
        timeout=60.0,
    )
    resp.raise_for_status()
    print(f"Indexed {rel}: {len(chunks)} chunks")


def scan(root: Path) -> None:
    with httpx.Client() as client:
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix.lower() not in EXTENSIONS:
                continue
            if "node_modules" in path.parts or ".git" in path.parts:
                continue
            index_file(client, path)


def main() -> None:
    root = Path(WATCH_PATH).resolve()
    print(f"Indexing worker watching {root}")
    while True:
        try:
            scan(root)
        except Exception as exc:
            print(f"Scan error: {exc}")
        time.sleep(SCAN_INTERVAL)


if __name__ == "__main__":
    main()
