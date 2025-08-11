"""add hybrid multi-tenancy MVP factory support

Revision ID: 000fd3d14730
Revises: fad491620d96
Create Date: 2025-08-11 08:29:30.351930

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '000fd3d14730'
down_revision: Union[str, None] = 'fad491620d96'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add tenant_type enum and extend existing enums
    op.execute("ALTER TYPE tenantplan ADD VALUE 'MVP_SINGLE'")
    op.execute("ALTER TYPE tenantplan ADD VALUE 'MVP_BUNDLE'")
    
    # Create tenant type enum
    sa.Enum('ENTERPRISE', 'MVP_FACTORY', name='tenanttype').create(op.get_bind())
    
    # Add new columns to tenants table
    op.add_column('tenants', sa.Column('tenant_type', sa.Enum('ENTERPRISE', 'MVP_FACTORY', name='tenanttype'), nullable=True))
    
    # MVP Factory specific fields
    op.add_column('tenants', sa.Column('founder_name', sa.String(255), nullable=True))
    op.add_column('tenants', sa.Column('founder_phone', sa.String(50), nullable=True))
    op.add_column('tenants', sa.Column('business_description', sa.Text(), nullable=True))
    op.add_column('tenants', sa.Column('target_market', sa.String(500), nullable=True))
    op.add_column('tenants', sa.Column('mvp_count_used', sa.Integer(), nullable=False, default=0))
    
    # Update existing tenants to be ENTERPRISE type (backward compatibility)
    op.execute("UPDATE tenants SET tenant_type = 'ENTERPRISE' WHERE tenant_type IS NULL")
    
    # Make tenant_type NOT NULL after updating existing records
    op.alter_column('tenants', 'tenant_type', nullable=False)
    
    # Add index for tenant type
    op.create_index('idx_tenant_type', 'tenants', ['tenant_type'])
    
    # Create MVP projects table
    op.create_table('mvp_projects',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('project_name', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(50), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, default='blueprint_pending'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('deployed_at', sa.DateTime(), nullable=True),
        sa.Column('interview_data', sa.JSON(), nullable=True),
        sa.Column('blueprint_data', sa.JSON(), nullable=True),
        sa.Column('generation_progress', sa.JSON(), nullable=False, default='{}'),
        sa.Column('blueprint_approval', sa.JSON(), nullable=True),
        sa.Column('deployment_approval', sa.JSON(), nullable=True),
        sa.Column('deployment_url', sa.String(500), nullable=True),
        sa.Column('repository_url', sa.String(500), nullable=True),
        sa.Column('monitoring_dashboard_url', sa.String(500), nullable=True),
        sa.Column('admin_panel_url', sa.String(500), nullable=True),
        sa.Column('cpu_hours_used', sa.Float(), nullable=False, default=0.0),
        sa.Column('memory_gb_hours_used', sa.Float(), nullable=False, default=0.0),
        sa.Column('storage_mb_used', sa.Integer(), nullable=False, default=0),
        sa.Column('ai_tokens_used', sa.Integer(), nullable=False, default=0),
        sa.Column('generation_success_rate', sa.Float(), nullable=False, default=0.0),
        sa.Column('deployment_uptime', sa.Float(), nullable=False, default=0.0),
        sa.Column('founder_satisfaction_score', sa.Integer(), nullable=True),
        sa.Column('total_cost', sa.Float(), nullable=False, default=0.0),
        sa.Column('payment_status', sa.String(50), nullable=False, default='pending'),
        sa.Column('payment_method', sa.String(50), nullable=True),
        sa.CheckConstraint('created_at <= updated_at', name='chk_mvp_timestamps'),
        sa.CheckConstraint('cpu_hours_used >= 0', name='chk_cpu_hours_positive'),
        sa.CheckConstraint('memory_gb_hours_used >= 0', name='chk_memory_hours_positive'),
        sa.CheckConstraint('storage_mb_used >= 0', name='chk_storage_positive'),
        sa.CheckConstraint('founder_satisfaction_score >= 1 AND founder_satisfaction_score <= 10', name='chk_satisfaction_range'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for MVP projects table
    op.create_index('idx_mvp_tenant_status', 'mvp_projects', ['tenant_id', 'status'])
    op.create_index('idx_mvp_tenant_created', 'mvp_projects', ['tenant_id', 'created_at'])
    op.create_index('idx_mvp_slug_tenant', 'mvp_projects', ['slug', 'tenant_id'])
    op.create_index('idx_mvp_deployment_status', 'mvp_projects', ['status', 'deployed_at'])
    op.create_index('idx_mvp_project_name', 'mvp_projects', ['project_name'])
    
    # Create MVP metrics table
    op.create_table('mvp_metrics',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('mvp_project_id', sa.UUID(), nullable=False),
        sa.Column('response_time_ms', sa.Float(), nullable=False),
        sa.Column('uptime_percentage', sa.Float(), nullable=False),
        sa.Column('error_rate', sa.Float(), nullable=False),
        sa.Column('page_views', sa.Integer(), nullable=False, default=0),
        sa.Column('unique_visitors', sa.Integer(), nullable=False, default=0),
        sa.Column('conversion_rate', sa.Float(), nullable=False, default=0.0),
        sa.Column('user_signups', sa.Integer(), nullable=False, default=0),
        sa.Column('code_quality_score', sa.Float(), nullable=False),
        sa.Column('test_coverage', sa.Float(), nullable=False),
        sa.Column('security_score', sa.Float(), nullable=False),
        sa.Column('collected_at', sa.DateTime(), nullable=False),
        sa.CheckConstraint('response_time_ms >= 0', name='chk_response_time_positive'),
        sa.CheckConstraint('uptime_percentage >= 0 AND uptime_percentage <= 100', name='chk_uptime_range'),
        sa.CheckConstraint('error_rate >= 0 AND error_rate <= 100', name='chk_error_rate_range'),
        sa.CheckConstraint('code_quality_score >= 0 AND code_quality_score <= 100', name='chk_code_quality_range'),
        sa.CheckConstraint('test_coverage >= 0 AND test_coverage <= 100', name='chk_test_coverage_range'),
        sa.CheckConstraint('security_score >= 0 AND security_score <= 100', name='chk_security_score_range'),
        sa.ForeignKeyConstraint(['mvp_project_id'], ['mvp_projects.id']),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for MVP metrics table
    op.create_index('idx_metrics_project_time', 'mvp_metrics', ['mvp_project_id', 'collected_at'])
    op.create_index('idx_metrics_collection_time', 'mvp_metrics', ['collected_at'])
    
    # Enable row-level security for new tables
    op.execute('ALTER TABLE mvp_projects ENABLE ROW LEVEL SECURITY')
    op.execute('ALTER TABLE mvp_metrics ENABLE ROW LEVEL SECURITY')
    
    # Create RLS policies for MVP tables
    op.execute("""
        CREATE POLICY mvp_project_isolation_policy ON mvp_projects
        USING (tenant_id = current_setting('app.current_tenant_id')::uuid)
    """)
    
    op.execute("""
        CREATE POLICY mvp_metrics_isolation_policy ON mvp_metrics  
        USING (
            mvp_project_id IN (
                SELECT id FROM mvp_projects 
                WHERE tenant_id = current_setting('app.current_tenant_id')::uuid
            )
        )
    """)
    
    # Super admin bypass policies for new tables
    op.execute("""
        CREATE POLICY admin_bypass_mvp_projects ON mvp_projects
        USING (current_setting('app.user_role', true) = 'superadmin')
    """)
    
    op.execute("""
        CREATE POLICY admin_bypass_mvp_metrics ON mvp_metrics
        USING (current_setting('app.user_role', true) = 'superadmin')
    """)


def downgrade() -> None:
    # Drop RLS policies
    op.execute('DROP POLICY IF EXISTS admin_bypass_mvp_metrics ON mvp_metrics')
    op.execute('DROP POLICY IF EXISTS admin_bypass_mvp_projects ON mvp_projects')
    op.execute('DROP POLICY IF EXISTS mvp_metrics_isolation_policy ON mvp_metrics')
    op.execute('DROP POLICY IF EXISTS mvp_project_isolation_policy ON mvp_projects')
    
    # Drop tables
    op.drop_table('mvp_metrics')
    op.drop_table('mvp_projects')
    
    # Drop indexes
    op.drop_index('idx_tenant_type')
    
    # Remove MVP Factory fields from tenants
    op.drop_column('tenants', 'mvp_count_used')
    op.drop_column('tenants', 'target_market')
    op.drop_column('tenants', 'business_description')
    op.drop_column('tenants', 'founder_phone')
    op.drop_column('tenants', 'founder_name')
    op.drop_column('tenants', 'tenant_type')
    
    # Drop tenant type enum
    sa.Enum(name='tenanttype').drop(op.get_bind())
    
    # Remove MVP plan values (this is irreversible in PostgreSQL)
    # op.execute("ALTER TYPE tenantplan DROP VALUE 'MVP_SINGLE'")  # Not supported
    # op.execute("ALTER TYPE tenantplan DROP VALUE 'MVP_BUNDLE'")  # Not supported
