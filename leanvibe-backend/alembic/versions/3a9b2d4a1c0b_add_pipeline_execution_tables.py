"""Add pipeline executions and execution logs tables

Revision ID: 3a9b2d4a1c0b
Revises: e8860589ccae
Create Date: 2025-08-12 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3a9b2d4a1c0b'
down_revision: Union[str, None] = 'e8860589ccae'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create pipeline_executions table
    op.create_table(
        'pipeline_executions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('mvp_project_id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('current_stage', sa.String(length=64), nullable=False),
        sa.Column('status', sa.String(length=64), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('current_stage_started_at', sa.DateTime(), nullable=False),
        sa.Column('stages_completed', sa.JSON(), nullable=False),
        sa.Column('stage_durations', sa.JSON(), nullable=False),
        sa.Column('overall_progress', sa.Float(), nullable=False),
        sa.Column('current_stage_progress', sa.Float(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['mvp_project_id'], ['mvp_projects.id']),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    # Indexes for pipeline_executions
    op.create_index('idx_exec_project_time', 'pipeline_executions', ['mvp_project_id', 'started_at'], unique=False)
    op.create_index('idx_exec_tenant_status', 'pipeline_executions', ['tenant_id', 'status'], unique=False)
    op.create_index('ix_pipeline_executions_current_stage', 'pipeline_executions', ['current_stage'], unique=False)
    op.create_index('ix_pipeline_executions_started_at', 'pipeline_executions', ['started_at'], unique=False)

    # Create pipeline_execution_logs table
    op.create_table(
        'pipeline_execution_logs',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('execution_id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('mvp_project_id', sa.UUID(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('level', sa.String(length=16), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('stage', sa.String(length=64), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['execution_id'], ['pipeline_executions.id']),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.ForeignKeyConstraint(['mvp_project_id'], ['mvp_projects.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    # Indexes for pipeline_execution_logs
    op.create_index('idx_exec_logs_exec_time', 'pipeline_execution_logs', ['execution_id', 'timestamp'], unique=False)
    op.create_index('idx_exec_logs_tenant_time', 'pipeline_execution_logs', ['tenant_id', 'timestamp'], unique=False)
    op.create_index('ix_pipeline_execution_logs_level', 'pipeline_execution_logs', ['level'], unique=False)
    op.create_index('ix_pipeline_execution_logs_stage', 'pipeline_execution_logs', ['stage'], unique=False)
    op.create_index('ix_pipeline_execution_logs_timestamp', 'pipeline_execution_logs', ['timestamp'], unique=False)


def downgrade() -> None:
    # Drop indexes and tables in reverse order
    op.drop_index('ix_pipeline_execution_logs_timestamp', table_name='pipeline_execution_logs')
    op.drop_index('ix_pipeline_execution_logs_stage', table_name='pipeline_execution_logs')
    op.drop_index('ix_pipeline_execution_logs_level', table_name='pipeline_execution_logs')
    op.drop_index('idx_exec_logs_tenant_time', table_name='pipeline_execution_logs')
    op.drop_index('idx_exec_logs_exec_time', table_name='pipeline_execution_logs')
    op.drop_table('pipeline_execution_logs')

    op.drop_index('ix_pipeline_executions_started_at', table_name='pipeline_executions')
    op.drop_index('ix_pipeline_executions_current_stage', table_name='pipeline_executions')
    op.drop_index('idx_exec_tenant_status', table_name='pipeline_executions')
    op.drop_index('idx_exec_project_time', table_name='pipeline_executions')
    op.drop_table('pipeline_executions')
