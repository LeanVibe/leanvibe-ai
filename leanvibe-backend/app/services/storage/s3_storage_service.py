"""
S3 storage service implementing list and presigned-get operations with range support.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple
from uuid import UUID

try:
    import boto3
    from botocore.client import Config as BotoConfig
except Exception:  # boto3 may not be installed in dev
    boto3 = None
    BotoConfig = None

from .local_storage_service import StoredFile


@dataclass
class _S3Config:
    bucket: str
    region: str
    prefix: str
    expiry_seconds: int


class S3StorageService:
    def __init__(self):
        if not boto3:
            raise RuntimeError("boto3 not available")
        self.config = _S3Config(
            bucket=os.getenv("LEANVIBE_S3_BUCKET", ""),
            region=os.getenv("LEANVIBE_S3_REGION", "us-east-1"),
            prefix=os.getenv("LEANVIBE_S3_PREFIX", "artifacts/"),
            expiry_seconds=int(os.getenv("LEANVIBE_S3_URL_EXPIRY", "900")),  # 15 min
        )
        if not self.config.bucket:
            raise RuntimeError("LEANVIBE_S3_BUCKET must be set for S3 provider")
        self._s3 = boto3.client("s3", region_name=self.config.region, config=BotoConfig(s3={"addressing_style": "virtual"}))

    def _key_prefix(self, project_id: UUID) -> str:
        return f"{self.config.prefix}{project_id.hex}/"

    def list_files(self, project_id: UUID, *, path_filter: Optional[str] = None) -> List[StoredFile]:
        prefix = self._key_prefix(project_id)
        paginator = self._s3.get_paginator("list_objects_v2")
        results: List[StoredFile] = []
        for page in paginator.paginate(Bucket=self.config.bucket, Prefix=prefix):
            for obj in page.get("Contents", []):
                key = obj["Key"]
                rel_path = key[len(prefix):]
                if not rel_path or rel_path.endswith("/"):
                    continue
                if path_filter and path_filter not in rel_path:
                    continue
                results.append(StoredFile(
                    path=rel_path,
                    size=int(obj.get("Size", 0)),
                    content_type="application/octet-stream",  # unknown until HEAD
                    modified_at=obj.get("LastModified", datetime.now(timezone.utc)).replace(tzinfo=None),
                ))
        return results

    def presign_download(self, project_id: UUID, rel_path: str, *, range_header: Optional[str] = None) -> str:
        key = f"{self._key_prefix(project_id)}{rel_path.lstrip('/')}"
        params = {"Bucket": self.config.bucket, "Key": key}
        if range_header:
            params["ResponseContentRange"] = range_header
        url = self._s3.generate_presigned_url(
            ClientMethod="get_object",
            Params=params,
            ExpiresIn=self.config.expiry_seconds,
        )
        return url

    # For interface compatibility with local storage
    def get_file(self, project_id: UUID, rel_path: str):
        # Return a small HTTP redirect tuple-like structure could be handled at endpoint layer
        raise NotImplementedError("Use presign_download for S3")


# Singleton
s3_storage_service = S3StorageService() if boto3 else None
