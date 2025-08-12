# Database Migrations (Alembic)

Run migrations locally:

1. Create virtualenv and install deps

```
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

2. Set database URL (defaults to SQLite dev DB if unset)

```
export LEANVIBE_DATABASE_URL="sqlite+aiosqlite:///./leanvibe.db"
```

3. Generate a new migration (if you change models)

```
alembic -c leanvibe-backend/alembic.ini revision -m "your message"
```

4. Upgrade to latest

```
alembic -c leanvibe-backend/alembic.ini upgrade head
```

5. Downgrade (optional)

```
alembic -c leanvibe-backend/alembic.ini downgrade -1
```

Notes:
- Migrations live in `leanvibe-backend/alembic/versions`
- The code uses async SQLAlchemy; migrations use sync URLs via `get_sync_database_url()` when needed.
