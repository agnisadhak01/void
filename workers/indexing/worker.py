"""File indexing worker — uses index_jobs table and gateway embeddings."""

import os
import time
from pathlib import Path

import asyncpg
import httpx

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://ausome:ausome_dev@localhost:5432/ausome")
GATEWAY_URL = os.environ.get("GATEWAY_URL", "http://127.0.0.1:8000")
PROJECT_ID = os.environ.get("PROJECT_ID", "00000000-0000-0000-0000-000000000001")
WATCH_PATH = os.environ.get("WATCH_PATH", ".")
CHUNK_SIZE = 1500
SCAN_INTERVAL = int(os.environ.get("SCAN_INTERVAL", "60"))
EXTENSIONS = {".ts", ".tsx", ".js", ".jsx", ".py", ".go", ".rs", ".md", ".json", ".yaml", ".yml"}
API_KEY = os.environ.get("AUSOME_API_KEY", "ausome-dev")


def chunk_text(text: str, size: int = CHUNK_SIZE) -> list[str]:
    return [text[i : i + size] for i in range(0, len(text), size)] or [text]


async def create_job(conn: asyncpg.Connection) -> str:
    row = await conn.fetchrow(
        """
        INSERT INTO index_jobs (project_id, status)
        VALUES ($1::uuid, 'running')
        RETURNING id
        """,
        PROJECT_ID,
    )
    return str(row["id"])


async def complete_job(conn: asyncpg.Connection, job_id: str, files_processed: int, error: str | None = None) -> None:
    status = "failed" if error else "completed"
    await conn.execute(
        """
        UPDATE index_jobs
        SET status = $2, files_processed = $3, error = $4, completed_at = NOW()
        WHERE id = $1::uuid
        """,
        job_id,
        status,
        files_processed,
        error,
    )


def index_file(client: httpx.Client, path: Path) -> int:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return 0
    if len(text) > 500_000:
        text = text[:500_000]
    chunks = chunk_text(text)
    rel = str(path).replace("\\", "/")
    resp = client.post(
        f"{GATEWAY_URL}/v1/context/index",
        json={"project_id": PROJECT_ID, "path": rel, "chunks": chunks},
        headers={"Authorization": f"Bearer {API_KEY}"},
        timeout=120.0,
    )
    resp.raise_for_status()
    print(f"Indexed {rel}: {len(chunks)} chunks")
    return 1


async def scan(root: Path) -> None:
    conn = await asyncpg.connect(DATABASE_URL)
    job_id = await create_job(conn)
    files_processed = 0
    try:
        with httpx.Client() as client:
            for path in root.rglob("*"):
                if not path.is_file():
                    continue
                if path.suffix.lower() not in EXTENSIONS:
                    continue
                if "node_modules" in path.parts or ".git" in path.parts:
                    continue
                files_processed += index_file(client, path)
        await complete_job(conn, job_id, files_processed)
    except Exception as exc:
        await complete_job(conn, job_id, files_processed, str(exc))
        raise
    finally:
        await conn.close()


def main() -> None:
    import asyncio

    root = Path(WATCH_PATH).resolve()
    print(f"Indexing worker watching {root}")
    while True:
        try:
            asyncio.run(scan(root))
        except Exception as exc:
            print(f"Scan error: {exc}")
        time.sleep(SCAN_INTERVAL)


if __name__ == "__main__":
    main()
