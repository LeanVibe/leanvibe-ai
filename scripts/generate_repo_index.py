#!/usr/bin/env python3
"""
Generate a navigable repository index:
- docs/repo_index.json: Full JSON map (file list, categories, directory tree, counts)
- docs/INDEX.md: Human-readable navigation overview linking to JSON

Uses `git ls-files` to enumerate tracked files for stability.
"""
from __future__ import annotations
import json
import os
import subprocess
from collections import defaultdict
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = REPO_ROOT / "docs"
INDEX_JSON = DOCS_DIR / "repo_index.json"
INDEX_MD = DOCS_DIR / "INDEX.md"

CATEGORY_BY_EXT = {
    # Documentation
    ".md": "docs",
    # Code
    ".py": "code_python",
    ".ts": "code_typescript",
    ".tsx": "code_typescript",
    ".js": "code_javascript",
    ".jsx": "code_javascript",
    ".swift": "code_swift",
    # Web
    ".html": "html",
    ".css": "css",
    # Configurations
    ".json": "config",
    ".yaml": "config",
    ".yml": "config",
    ".toml": "config",
    ".ini": "config",
    ".cfg": "config",
    ".conf": "config",
    ".properties": "config",
    # Scripts
    ".sh": "scripts",
    ".ps1": "scripts",
    ".bat": "scripts",
    ".cmd": "scripts",
    ".zsh": "scripts",
    # Data/DB
    ".sql": "database",
    # Packaging/locks
    ".lock": "lock",
    # iOS/Services
    ".plist": "plist",
    ".service": "service",
    # Env
    ".env": "env",
    # Images/Assets
    ".png": "image",
    ".jpg": "image",
    ".jpeg": "image",
    ".gif": "image",
    ".svg": "image",
    ".webp": "image",
}

SPECIAL_FILES = {
    "Dockerfile": "docker",
    "Makefile": "makefile",
}

DOCKER_COMPOSE_PREFIXES = ("docker-compose.",)

EXCLUDE_DIR_PREFIXES = {
    ".git/",
    "node_modules/",
    ".venv/",
    ".next/",
    "dist/",
    "build/",
    ".cache/",
    "coverage/",
}


def run_git_ls_files(repo_root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "ls-files"], cwd=str(repo_root), capture_output=True, text=True, check=True
    )
    raw_files = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    # Normalize any paths that may have been shell-quoted in history tools
    files: list[str] = []
    for path in raw_files:
        if path.startswith('"') and path.endswith('"') and len(path) > 1:
            path = path[1:-1]
        files.append(path)
    return files


def categorize(path: str) -> str:
    # Special file names
    name = os.path.basename(path)
    if name in SPECIAL_FILES:
        return SPECIAL_FILES[name]
    if name.startswith(DOCKER_COMPOSE_PREFIXES):
        return "docker"
    # Extension-based
    ext = os.path.splitext(name)[1].lower()
    if ext in CATEGORY_BY_EXT:
        return CATEGORY_BY_EXT[ext]
    # Fallbacks by path hints
    if "/docker-compose" in path:
        return "docker"
    if "/docs/" in path or path.startswith("docs/"):
        return "docs"
    return "other"


def should_exclude(path: str) -> bool:
    for prefix in EXCLUDE_DIR_PREFIXES:
        if path.startswith(prefix) or f"/{prefix}" in path:
            return True
    return False


def build_tree(file_paths: list[str]) -> dict:
    tree = {"name": "/", "type": "dir", "children": {}}

    for rel_path in file_paths:
        parts = rel_path.split("/")
        cursor = tree
        for i, part in enumerate(parts):
            is_last = i == len(parts) - 1
            if "children" not in cursor:
                cursor["children"] = {}
            if part not in cursor["children"]:
                cursor["children"][part] = {
                    "name": part,
                    "type": "file" if is_last else "dir",
                    "children": {} if not is_last else None,
                }
            cursor = cursor["children"][part]
    return tree


def tree_to_list(node: dict) -> dict:
    # Convert dict-of-dicts to list children for stable ordering
    def sort_key(item):
        name = item[0]
        node = item[1]
        # Directories before files, then name
        return (0 if node["type"] == "dir" else 1, name.lower())

    if node.get("children") is None:
        return node
    items = [tree_to_list(child) for _, child in sorted(node["children"].items(), key=sort_key)]
    node_list = {k: v for k, v in node.items() if k != "children"}
    node_list["children"] = items
    return node_list


def generate_index():
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    all_files = run_git_ls_files(REPO_ROOT)

    # Filter excluded
    files = [p for p in all_files if not should_exclude(p)]

    # Per-category buckets
    by_category: dict[str, list[str]] = defaultdict(list)
    for p in files:
        by_category[categorize(p)].append(p)

    # Counts
    counts = {k: len(sorted(v)) for k, v in by_category.items()}
    total = len(files)

    # Tree
    tree = tree_to_list(build_tree(files))

    # Top-level directories summary
    top_level: dict[str, int] = defaultdict(int)
    for p in files:
        head = p.split("/", 1)[0]
        top_level[head] += 1

    index = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "repo_root": str(REPO_ROOT),
        "total_files": total,
        "counts_by_category": dict(sorted(counts.items(), key=lambda kv: kv[0])),
        "top_level_counts": dict(sorted(top_level.items(), key=lambda kv: kv[0])),
        "files_by_category": {k: sorted(v) for k, v in sorted(by_category.items(), key=lambda kv: kv[0])},
        "tree": tree,
    }

    INDEX_JSON.write_text(json.dumps(index, indent=2))

    # Markdown summary
    lines = []
    lines.append("## Repository index")
    lines.append("")
    lines.append(f"Generated: {index['generated_at']}")
    lines.append("")
    lines.append(f"Total tracked files: {total}")
    lines.append("")
    lines.append("### Top-level directories")
    for name, cnt in sorted(top_level.items(), key=lambda kv: kv[0].lower()):
        lines.append(f"- {name}: {cnt}")
    lines.append("")
    lines.append("### Categories")
    for name, cnt in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])):
        lines.append(f"- {name}: {cnt}")
    lines.append("")
    lines.append("### Navigation")
    lines.append("- Full JSON: ./repo_index.json")
    lines.append("- Tips: Use your editor's file explorer or search on categories in JSON for quick navigation.")
    lines.append("")

    INDEX_MD.write_text("\n".join(lines))


if __name__ == "__main__":
    generate_index()
