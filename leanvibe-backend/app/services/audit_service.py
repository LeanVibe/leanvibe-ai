"""
Audit service to record critical actions for compliance.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy import select

from ..core.database import get_database_session
from ..models.orm_models import AuditLogORM

logger = logging.getLogger(__name__)


class AuditService:
    async def log(
        self,
        *,
        tenant_id: UUID,
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        user_id: Optional[UUID] = None,
        user_email: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> None:
        try:
            async for session in get_database_session():
                entry = AuditLogORM(
                    tenant_id=tenant_id,
                    action=action,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    user_id=user_id,
                    user_email=user_email,
                    details=details or {},
                    ip_address=ip_address,
                    user_agent=user_agent,
                    timestamp=datetime.utcnow(),
                )
                session.add(entry)
                await session.flush()
                try:
                    await session.commit()
                except Exception:
                    pass
                break
        except Exception as e:
            logger.warning(f"Failed to write audit log: {e}")


audit_service = AuditService()
