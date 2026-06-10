import re
from pathlib import Path
from typing import Any


def extract_from_file(path: Path, text: str) -> tuple[list[dict], list[dict]]:
    """MVP extractor: files, classes, functions, imports."""
    rel = str(path).replace("\\", "/")
    nodes: list[dict] = [{"node_type": "file", "name": path.name, "path": rel, "metadata": {}}]
    edges: list[dict] = []

    for m in re.finditer(r"^(?:export\s+)?class\s+(\w+)", text, re.MULTILINE):
        nodes.append({"node_type": "class", "name": m.group(1), "path": rel, "metadata": {}})
    for m in re.finditer(r"^(?:export\s+)?(?:async\s+)?function\s+(\w+)", text, re.MULTILINE):
        nodes.append({"node_type": "function", "name": m.group(1), "path": rel, "metadata": {}})
    for m in re.finditer(r"^def\s+(\w+)", text, re.MULTILINE):
        nodes.append({"node_type": "function", "name": m.group(1), "path": rel, "metadata": {}})
    for m in re.finditer(r'from\s+["\']([^"\']+)["\']', text):
        edges.append({"edge_type": "imports", "target_name": m.group(1), "source_path": rel})
    for m in re.finditer(r'import\s+["\']([^"\']+)["\']', text):
        edges.append({"edge_type": "imports", "target_name": m.group(1), "source_path": rel})

    return nodes, edges


EXTENSIONS = {".ts", ".tsx", ".js", ".jsx", ".py", ".go", ".rs"}


def scan_directory(root: Path) -> tuple[list[dict], list[dict]]:
    all_nodes: list[dict] = []
    all_edges: list[dict] = []
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix not in EXTENSIONS:
            continue
        if "node_modules" in path.parts or ".git" in path.parts:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")[:200_000]
        except OSError:
            continue
        nodes, edges = extract_from_file(path, text)
        all_nodes.extend(nodes)
        all_edges.extend(edges)
    return all_nodes, all_edges
