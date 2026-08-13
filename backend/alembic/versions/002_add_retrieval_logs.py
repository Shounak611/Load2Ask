"""add retrieval logs table

Revision ID: 002_add_retrieval_logs
Revises: 001_initial_schema
Create Date: 2026-08-14 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '002_add_retrieval_logs'
down_revision: Union[str, None] = '001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'retrieval_logs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('session_id', sa.String(length=36), nullable=True),
        sa.Column('query', sa.Text(), nullable=False),
        sa.Column('retrieved_chunks_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('latency_ms', sa.Float(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_retrieval_logs_session_id'), 'retrieval_logs', ['session_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_retrieval_logs_session_id'), table_name='retrieval_logs')
    op.drop_table('retrieval_logs')
