"""
Storage services package with provider selection.
"""

import os
from typing import Protocol
from uuid import UUID
from .local_storage_service import local_storage_service, StoredFile, LocalStorageService  # noqa: F401


class StorageService(Protocol):
    def list_files(self, project_id: UUID, *, path_filter: str | None = None) -> list[StoredFile]: ...
    # For downloads we expose presign to allow signed URLs in S3; local returns path
    def get_file(self, project_id: UUID, rel_path: str): ...
    # Cleanup API: delete all artifacts under a project prefix
    def delete_project_artifacts(self, project_id: UUID) -> None: ...


def get_storage_service() -> StorageService:
    provider = os.getenv("LEANVIBE_STORAGE_PROVIDER", "local").lower()
    # For now, default to local; S3 provider can be added when configured
    if provider == "s3":
        try:
            from .s3_storage_service import s3_storage_service
            return s3_storage_service
        except Exception:
            return local_storage_service
    return local_storage_service


def get_storage_capabilities() -> dict:
    """Return current storage provider and capabilities."""
    provider = os.getenv("LEANVIBE_STORAGE_PROVIDER", "local").lower()
    caps = {
        "provider": provider,
        "presign_download": provider == "s3",
        "range_supported": provider == "s3",
        "server_zip_archive": True,  # local native; s3 supported via server streaming
        "archive_formats": {"zip": True, "tar": False},
        "max_preview_size_bytes": 1_000_000,
    }
    return caps
