"""Initial migration for callzo usage metering schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-11-08 19:15:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Accounts
    op.create_table(
        'accounts',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('company', sa.String(length=255), nullable=True),
        sa.Column('country', sa.String(length=8), server_default='US', nullable=False),
        sa.Column('plan', sa.String(length=32), server_default='pro', nullable=False),
        sa.Column('status', sa.String(length=32), server_default='active', nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_accounts_email'), 'accounts', ['email'], unique=False)
    op.create_index(op.f('ix_accounts_id'), 'accounts', ['id'], unique=False)

    # 2. Raw Webhook Events
    op.create_table(
        'raw_webhook_events',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('event_id', sa.String(length=128), nullable=False),
        sa.Column('event_type', sa.String(length=64), nullable=False),
        sa.Column('account_id', sa.String(length=64), nullable=False),
        sa.Column('call_id', sa.String(length=128), nullable=False),
        sa.Column('payload', sa.Text(), nullable=False),
        sa.Column('signature', sa.String(length=256), nullable=True),
        sa.Column('received_at', sa.DateTime(), nullable=False),
        sa.Column('processing_status', sa.String(length=32), server_default='processed', nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_raw_webhook_events_event_id'), 'raw_webhook_events', ['event_id'], unique=True)
    op.create_index(op.f('ix_raw_webhook_events_event_type'), 'raw_webhook_events', ['event_type'], unique=False)
    op.create_index(op.f('ix_raw_webhook_events_account_id'), 'raw_webhook_events', ['account_id'], unique=False)
    op.create_index(op.f('ix_raw_webhook_events_call_id'), 'raw_webhook_events', ['call_id'], unique=False)
    op.create_index(op.f('ix_raw_webhook_events_processing_status'), 'raw_webhook_events', ['processing_status'], unique=False)
    op.create_index('ix_raw_events_account_type', 'raw_webhook_events', ['account_id', 'event_type'], unique=False)

    # 3. Calls
    op.create_table(
        'calls',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('call_id', sa.String(length=128), nullable=False),
        sa.Column('account_id', sa.String(length=64), nullable=False),
        sa.Column('status', sa.String(length=32), server_default='started', nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('ended_at', sa.DateTime(), nullable=True),
        sa.Column('duration_seconds', sa.Integer(), server_default='0', nullable=False),
        sa.Column('cost_cents', sa.Integer(), server_default='0', nullable=False),
        sa.Column('destination_country', sa.String(length=8), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_calls_call_id'), 'calls', ['call_id'], unique=True)
    op.create_index(op.f('ix_calls_account_id'), 'calls', ['account_id'], unique=False)
    op.create_index(op.f('ix_calls_status'), 'calls', ['status'], unique=False)
    op.create_index('ix_calls_account_status', 'calls', ['account_id', 'status'], unique=False)
    op.create_index('ix_calls_account_started_at', 'calls', ['account_id', 'started_at'], unique=False)

    # 4. Monthly Usage
    op.create_table(
        'monthly_usage',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('account_id', sa.String(length=64), nullable=False),
        sa.Column('year_month', sa.String(length=7), nullable=False),
        sa.Column('total_calls', sa.Integer(), server_default='0', nullable=False),
        sa.Column('total_duration_seconds', sa.Integer(), server_default='0', nullable=False),
        sa.Column('total_cost_cents', sa.Integer(), server_default='0', nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('account_id', 'year_month', name='uq_account_year_month')
    )
    op.create_index(op.f('ix_monthly_usage_account_id'), 'monthly_usage', ['account_id'], unique=False)
    op.create_index(op.f('ix_monthly_usage_year_month'), 'monthly_usage', ['year_month'], unique=False)
    op.create_index('ix_monthly_usage_account_month', 'monthly_usage', ['account_id', 'year_month'], unique=False)

    # 5. Usage Caps
    op.create_table(
        'usage_caps',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('account_id', sa.String(length=64), nullable=False),
        sa.Column('monthly_minutes_cap', sa.Integer(), nullable=True),
        sa.Column('monthly_cost_cents_cap', sa.Integer(), nullable=True),
        sa.Column('is_hard_cap', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('cap_action', sa.String(length=32), server_default='flag_exceeded', nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('account_id')
    )
    op.create_index(op.f('ix_usage_caps_account_id'), 'usage_caps', ['account_id'], unique=True)

    # 6. Event Retry Records
    op.create_table(
        'event_retry_records',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('event_id', sa.String(length=128), nullable=False),
        sa.Column('payload', sa.Text(), nullable=False),
        sa.Column('attempts', sa.Integer(), server_default='0', nullable=False),
        sa.Column('max_attempts', sa.Integer(), server_default='5', nullable=False),
        sa.Column('status', sa.String(length=32), server_default='pending', nullable=False),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('next_retry_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_event_retry_records_event_id'), 'event_retry_records', ['event_id'], unique=False)
    op.create_index(op.f('ix_event_retry_records_status'), 'event_retry_records', ['status'], unique=False)
    op.create_index('ix_retries_status_next_retry', 'event_retry_records', ['status', 'next_retry_at'], unique=False)


def downgrade() -> None:
    op.drop_table('event_retry_records')
    op.drop_table('usage_caps')
    op.drop_table('monthly_usage')
    op.drop_table('calls')
    op.drop_table('raw_webhook_events')
    op.drop_table('accounts')
