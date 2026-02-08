"""init: sessions and agent_logs

Revision ID: 4b0760190cc6
Revises:
Create Date: 2026-02-08 14:36:56.969093

@TASK P0-T4 - SQLAlchemy ORM 모델 정의 + Alembic 마이그레이션
@SPEC docs/planning/04-database-design.md

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4b0760190cc6'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create sessions and agent_logs tables."""
    # Create sessions table
    op.create_table(
        'sessions',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('user_query', sa.Text, nullable=False, comment='User\'s query about NGT safety assessment'),
        sa.Column('final_report', sa.Text, nullable=True, comment='Generated safety assessment report'),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), nullable=False, comment='Timestamp when session was created'),
    )

    # Create agent_logs table with foreign key to sessions
    op.create_table(
        'agent_logs',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('session_id', sa.UUID(as_uuid=True), nullable=False, comment='Reference to parent session'),
        sa.Column('agent_name', sa.String(50), nullable=False, comment='Name of the agent (PI, Scientist, Critic, etc.)'),
        sa.Column('action', sa.String(100), nullable=False, comment='Type of action (search, analysis, review, validation, etc.)'),
        sa.Column('result', sa.Text, nullable=False, comment='Result or output from the action'),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), nullable=False, comment='Timestamp when the log entry was created'),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ondelete='CASCADE'),
    )

    # Create indexes
    op.create_index('idx_agent_logs_session_id', 'agent_logs', ['session_id'])
    op.create_index('idx_agent_logs_created_at', 'agent_logs', ['created_at'])
    op.create_index('idx_sessions_created_at', 'sessions', ['created_at'])


def downgrade() -> None:
    """Drop sessions and agent_logs tables."""
    # Drop indexes
    op.drop_index('idx_sessions_created_at', 'sessions')
    op.drop_index('idx_agent_logs_created_at', 'agent_logs')
    op.drop_index('idx_agent_logs_session_id', 'agent_logs')

    # Drop tables
    op.drop_table('agent_logs')
    op.drop_table('sessions')
