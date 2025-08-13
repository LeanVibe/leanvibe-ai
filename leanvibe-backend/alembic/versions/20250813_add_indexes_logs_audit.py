"""
Add indexes for pipeline_execution_logs and audit_logs

Revision ID: 20250813_add_indexes_logs_audit
Revises: 3a9b2d4a1c0b
Create Date: 2025-08-13
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20250813_add_indexes_logs_audit'
down_revision = '3a9b2d4a1c0b'
branch_labels = None
depends_on = None

def upgrade():
    try:
        op.create_index('idx_logs_ts_level_stage', 'pipeline_execution_logs', ['timestamp', 'level', 'stage'], unique=False)
    except Exception:
        pass
    try:
        op.create_index('idx_audit_tenant_action_ts', 'audit_logs', ['tenant_id', 'action', 'timestamp'], unique=False)
    except Exception:
        pass


def downgrade():
    try:
        op.drop_index('idx_logs_ts_level_stage', table_name='pipeline_execution_logs')
    except Exception:
        pass
    try:
        op.drop_index('idx_audit_tenant_action_ts', table_name='audit_logs')
    except Exception:
        pass
