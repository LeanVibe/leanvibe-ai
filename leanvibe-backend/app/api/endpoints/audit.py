"""
Audit listing endpoint for admins with filters and pagination.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID

from fastapi import APIRouter, Depends, Query, HTTPException, status

from ...auth.permissions import require_permission, Permission
from ...core.database import get_database_session
from ...models.orm_models import AuditLogORM
from sqlalchemy import select

router = APIRouter(prefix="/api/v1/audit", tags=["audit"])


@router.get("/")
async def list_audit_logs(
    tenant_id: Optional[UUID] = Query(None),
    action: Optional[str] = Query(None),
    resource: Optional[str] = Query(None, description="resource_type, e.g., pipeline, project_file"),
    user_id: Optional[UUID] = Query(None),
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    _admin = Depends(require_permission(Permission.ADMIN_ALL)),
) -> Dict[str, Any]:
    try:
        items: List[Dict[str, Any]] = []
        total: int = 0
        async for session in get_database_session():
            stmt = select(AuditLogORM)
            if tenant_id:
                stmt = stmt.where(AuditLogORM.tenant_id == tenant_id)
            if action:
                stmt = stmt.where(AuditLogORM.action == action)
            if resource:
                stmt = stmt.where(AuditLogORM.resource_type == resource)
            if user_id:
                stmt = stmt.where(AuditLogORM.user_id == user_id)
            if start_time:
                stmt = stmt.where(AuditLogORM.timestamp >= start_time)
            if end_time:
                stmt = stmt.where(AuditLogORM.timestamp <= end_time)
            # Total count (approx via list)
            count_stmt = stmt.with_only_columns(AuditLogORM.id).order_by(None)
            rows = (await session.execute(count_stmt)).scalars().all()
            total = len(rows)

            # Pagination
            stmt = stmt.order_by(AuditLogORM.timestamp.desc()).offset(offset).limit(limit)
            res = await session.execute(stmt)
            for row in res.scalars().all():
                items.append({
                    "id": str(row.id),
                    "tenant_id": str(row.tenant_id),
                    "action": row.action,
                    "resource_type": row.resource_type,
                    "resource_id": row.resource_id,
                    "user_id": str(row.user_id) if row.user_id else None,
                    "timestamp": row.timestamp.isoformat() if row.timestamp else None,
                    "details": row.details or {},
                    "ip_address": row.ip_address,
                    "user_agent": row.user_agent,
                })
            break
        return {"total": total, "items": items}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to list audit logs: {e}")
