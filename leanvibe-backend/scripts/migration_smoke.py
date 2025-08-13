"""
Migration smoke test: initialize DB via Alembic and verify core tables exist.
Usage: python -m scripts.migration_smoke
"""
from __future__ import annotations

import asyncio
import os
import sys

os.environ.setdefault("LEANVIBE_DATABASE_URL", os.getenv("LEANVIBE_DATABASE_URL", "sqlite+aiosqlite:///./leanvibe_test.db"))

from app.core.database import init_database, close_database
from sqlalchemy import text
from app.core.database import get_database_session

REQUIRED_TABLES = [
    "tenants",
    "mvp_projects",
    "pipeline_executions",
    "pipeline_execution_logs",
    "audit_logs",
]

async def main() -> int:
    try:
        await init_database()
        missing: list[str] = []
        async for session in get_database_session():
            # Portable table listing
            try:
                res = await session.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
                names = {row[0] for row in res.fetchall()}
            except Exception:
                # Fallback for other engines
                res = await session.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema NOT IN ('pg_catalog','information_schema')"))
                names = {row[0] for row in res.fetchall()}
            for t in REQUIRED_TABLES:
                if t not in names:
                    missing.append(t)
            break
        if missing:
            print(f"Missing tables: {', '.join(missing)}")
            return 1
        print("Migration smoke OK")
        return 0
    except Exception as e:
        print(f"Migration smoke failed: {e}")
        return 2
    finally:
        try:
            await close_database()
        except Exception:
            pass

if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
