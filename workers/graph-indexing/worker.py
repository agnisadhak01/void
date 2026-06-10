"""Graph indexing worker — extracts imports and upserts to gateway graph API."""

import os
import time
from pathlib import Path

import httpx

from graph_service.extractor import extract_from_file

GATEWAY_URL = os.environ.get("GATEWAY_URL", "http://127.0.0.1:8000")
PROJECT_ID = os.environ.get("PROJECT_ID", "00000000-0000-0000-0000-000000000001")
WATCH_PATH = os.environ.get("WATCH_PATH", ".")
SCAN_INTERVAL = int(os.environ.get("SCAN_INTERVAL", "120"))
EXTENSIONS = {".ts", ".tsx", ".js", ".jsx", ".py"}
API_KEY = os.environ.get("AUSOME_API_KEY", "ausome-dev")


def upsert_graph(client: httpx.Client, path: Path) -> None:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return
    rel = str(path.relative_to(Path(WATCH_PATH).resolve())).replace("\\", "/")
    nodes, edges = extract_from_file(Path(rel), text)
    if not nodes:
        return
    resp = client.post(
        f"{GATEWAY_URL}/v1/graph/upsert",
        json={"project_id": PROJECT_ID, "nodes": nodes, "edges": edges},
        headers={"Authorization": f"Bearer {API_KEY}"},
        timeout=60.0,
    )
    resp.raise_for_status()
    print(f"Graph upsert {rel}: {resp.json()}")


def scan(root: Path) -> None:
    with httpx.Client() as client:
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in EXTENSIONS:
                continue
            if "node_modules" in path.parts or ".git" in path.parts:
                continue
            upsert_graph(client, path)


def main() -> None:
    root = Path(WATCH_PATH).resolve()
    print(f"Graph indexing worker watching {root}")
    while True:
        try:
            scan(root)
        except Exception as exc:
            print(f"Graph scan error: {exc}")
        time.sleep(SCAN_INTERVAL)


if __name__ == "__main__":
    main()
