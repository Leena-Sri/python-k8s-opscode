"""Initial database schema

Revision ID: 001
Revises:
Create Date: 2026-09-15 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create workloads table
    op.create_table(
        'workloads',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('namespace', sa.String(255), nullable=False),
        sa.Column('kind', sa.String(50), nullable=False),
        sa.Column('desired_replicas', sa.Integer(), nullable=False),
        sa.Column('available_replicas', sa.Integer(), nullable=False),
        sa.Column('health', sa.String(20), nullable=False, server_default='UNKNOWN'),
        sa.Column('restart_count', sa.Integer(), server_default='0'),
        sa.Column('cpu_usage_percent', sa.Float(), server_default='0.0'),
        sa.Column('memory_usage_percent', sa.Float(), server_default='0.0'),
        sa.Column('error_rate', sa.Float(), server_default='0.0'),
        sa.Column('response_latency_ms', sa.Float(), server_default='0.0'),
        sa.Column('labels', postgresql.JSONB(), server_default='{}'),
        sa.Column('annotations', postgresql.JSONB(), server_default='{}'),
        sa.Column('metadata', postgresql.JSONB(), server_default='{}'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_workloads_name', 'workloads', ['name'])
    op.create_index('ix_workloads_namespace', 'workloads', ['namespace'])
    op.create_index('idx_workload_namespace_name', 'workloads', ['namespace', 'name'])

    # Create incidents table
    op.create_table(
        'incidents',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('workload', sa.String(255), nullable=False),
        sa.Column('namespace', sa.String(255), nullable=False),
        sa.Column('severity', sa.String(20), nullable=False),
        sa.Column('type', sa.String(50), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('detected_at', sa.DateTime(), nullable=False),
        sa.Column('acknowledged_at', sa.DateTime(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='OPEN'),
        sa.Column('metadata', postgresql.JSONB(), server_default='{}'),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.Column('workload_id', sa.String(36), sa.ForeignKey('workloads.id'), nullable=True),
    )
    op.create_index('ix_incidents_workload', 'incidents', ['workload'])
    op.create_index('ix_incidents_namespace', 'incidents', ['namespace'])
    op.create_index('ix_incidents_severity', 'incidents', ['severity'])
    op.create_index('ix_incidents_type', 'incidents', ['type'])
    op.create_index('ix_incidents_detected_at', 'incidents', ['detected_at'])
    op.create_index('ix_incidents_resolved_at', 'incidents', ['resolved_at'])
    op.create_index('ix_incidents_status', 'incidents', ['status'])
    op.create_index('idx_incident_status_severity', 'incidents', ['status', 'severity'])
    op.create_index('idx_incident_workload_namespace', 'incidents', ['workload', 'namespace'])

    # Create alerts table
    op.create_table(
        'alerts',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('workload', sa.String(255), nullable=False),
        sa.Column('namespace', sa.String(255), nullable=False),
        sa.Column('severity', sa.String(20), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('metric_name', sa.String(255), nullable=False),
        sa.Column('threshold', sa.Float(), nullable=False),
        sa.Column('current_value', sa.Float(), nullable=False),
        sa.Column('triggered_at', sa.DateTime(), nullable=False),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('is_resolved', sa.Boolean(), server_default='false'),
        sa.Column('metadata', postgresql.JSONB(), server_default='{}'),
        sa.Column('workload_id', sa.String(36), sa.ForeignKey('workloads.id'), nullable=True),
    )
    op.create_index('ix_alerts_workload', 'alerts', ['workload'])
    op.create_index('ix_alerts_namespace', 'alerts', ['namespace'])
    op.create_index('ix_alerts_severity', 'alerts', ['severity'])
    op.create_index('ix_alerts_triggered_at', 'alerts', ['triggered_at'])
    op.create_index('ix_alerts_is_resolved', 'alerts', ['is_resolved'])
    op.create_index('idx_alert_resolved_severity', 'alerts', ['is_resolved', 'severity'])

    # Create remediation_actions table
    op.create_table(
        'remediation_actions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('incident_id', sa.String(36), sa.ForeignKey('incidents.id'), nullable=True),
        sa.Column('workload', sa.String(255), nullable=False),
        sa.Column('namespace', sa.String(255), nullable=False),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='PENDING'),
        sa.Column('dry_run', sa.Boolean(), server_default='false'),
        sa.Column('initiated_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), server_default='0'),
        sa.Column('metadata', postgresql.JSONB(), server_default='{}'),
        sa.Column('workload_id', sa.String(36), sa.ForeignKey('workloads.id'), nullable=True),
    )
    op.create_index('ix_remediation_actions_workload', 'remediation_actions', ['workload'])
    op.create_index('ix_remediation_actions_namespace', 'remediation_actions', ['namespace'])
    op.create_index('ix_remediation_actions_status', 'remediation_actions', ['status'])
    op.create_index('ix_remediation_actions_incident_id', 'remediation_actions', ['incident_id'])
    op.create_index('ix_remediation_actions_initiated_at', 'remediation_actions', ['initiated_at'])
    op.create_index('idx_remediation_status_workload', 'remediation_actions', ['status', 'workload'])

    # Create health_checks table
    op.create_table(
        'health_checks',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('workload', sa.String(255), nullable=False),
        sa.Column('namespace', sa.String(255), nullable=False),
        sa.Column('check_type', sa.String(50), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('value', sa.Float(), nullable=True),
        sa.Column('threshold', sa.Float(), nullable=True),
        sa.Column('passed', sa.Boolean(), server_default='false'),
        sa.Column('checked_at', sa.DateTime(), nullable=False),
        sa.Column('metadata', postgresql.JSONB(), server_default='{}'),
    )
    op.create_index('ix_health_checks_workload', 'health_checks', ['workload'])
    op.create_index('ix_health_checks_namespace', 'health_checks', ['namespace'])
    op.create_index('ix_health_checks_checked_at', 'health_checks', ['checked_at'])
    op.create_index('idx_health_check_workload_time', 'health_checks', ['workload', 'checked_at'])

    # Create audit_events table
    op.create_table(
        'audit_events',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('actor', sa.String(255), nullable=True),
        sa.Column('workload', sa.String(255), nullable=True),
        sa.Column('namespace', sa.String(255), nullable=True),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('details', postgresql.JSONB(), server_default='{}'),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_audit_events_event_type', 'audit_events', ['event_type'])
    op.create_index('ix_audit_events_workload', 'audit_events', ['workload'])
    op.create_index('ix_audit_events_namespace', 'audit_events', ['namespace'])
    op.create_index('ix_audit_events_timestamp', 'audit_events', ['timestamp'])
    op.create_index('idx_audit_event_type_time', 'audit_events', ['event_type', 'timestamp'])


def downgrade() -> None:
    op.drop_table('audit_events')
    op.drop_table('health_checks')
    op.drop_table('remediation_actions')
    op.drop_table('alerts')
    op.drop_table('incidents')
    op.drop_table('workloads')
