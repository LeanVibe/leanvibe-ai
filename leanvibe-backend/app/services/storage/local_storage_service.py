"""
Local storage service for MVP artifacts.
Provides a simple filesystem-backed implementation with path scoping per project.
"""

from __future__ import annotations

import mimetypes
import os
from dataclasses import dataclass
from datetime import datetime
from io import BytesIO
from typing import List, Optional, Tuple
from uuid import UUID


@dataclass
class StoredFile:
    path: str
    size: int
    content_type: str
    modified_at: datetime


class LocalStorageService:
    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = base_dir or os.path.abspath(os.path.join(os.getcwd(), "generated_artifacts"))
        os.makedirs(self.base_dir, exist_ok=True)

    def _project_root(self, project_id: UUID) -> str:
        root = os.path.join(self.base_dir, project_id.hex)
        os.makedirs(root, exist_ok=True)
        return root

    def list_files(self, project_id: UUID, *, path_filter: Optional[str] = None) -> List[StoredFile]:
        root = self._project_root(project_id)
        results: List[StoredFile] = []
        for dirpath, _, filenames in os.walk(root):
            for name in filenames:
                rel_path = os.path.relpath(os.path.join(dirpath, name), root)
                if path_filter and path_filter not in rel_path:
                    continue
                full = os.path.join(dirpath, name)
                stat = os.stat(full)
                content_type, _ = mimetypes.guess_type(name)
                results.append(
                    StoredFile(
                        path=rel_path.replace("\\", "/"),
                        size=stat.st_size,
                        content_type=content_type or "application/octet-stream",
                        modified_at=datetime.fromtimestamp(stat.st_mtime),
                    )
                )
        return results

    def get_file(self, project_id: UUID, rel_path: str) -> Tuple[BytesIO, str]:
        root = self._project_root(project_id)
        safe_rel = rel_path.lstrip("/\\").replace("..", "_")
        full = os.path.join(root, safe_rel)
        if not os.path.isfile(full):
            raise FileNotFoundError(rel_path)
        with open(full, "rb") as f:
            data = f.read()
        content_type, _ = mimetypes.guess_type(full)
        return BytesIO(data), (content_type or "application/octet-stream")

    def delete_project_artifacts(self, project_id: UUID) -> None:
        root = self._project_root(project_id)
        # Remove entire directory tree safely
        try:
            for dirpath, dirnames, filenames in os.walk(root, topdown=False):
                for filename in filenames:
                    try:
                        os.remove(os.path.join(dirpath, filename))
                    except FileNotFoundError:
                        pass
                for dirname in dirnames:
                    try:
                        os.rmdir(os.path.join(dirpath, dirname))
                    except OSError:
                        pass
            try:
                os.rmdir(root)
            except OSError:
                pass
        except Exception:
            # Best effort cleanup
            pass


# Singleton
local_storage_service = LocalStorageService()
