"""
AgentLog model for tracking agent actions and results.

@TASK P0-T4 - SQLAlchemy ORM 모델 정의
@SPEC docs/planning/04-database-design.md#agent-logs-table
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import UUID, Text, DateTime, String, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base


class AgentLog(Base):
    """
    Tracks actions and results from AI agents during safety assessment.

    Attributes:
        id: Unique log entry identifier (UUID)
        session_id: Reference to parent session (FK)
        agent_name: Name of the agent (PI, Scientist, Critic)
        action: Type of action performed (search, analysis, review, etc.)
        result: Result or output from the action
        created_at: Timestamp when the log was created
    """
    __tablename__ = "agent_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False,
        comment="Reference to parent session",
    )

    agent_name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Name of the agent (PI, Scientist, Critic, etc.)",
    )

    action: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Type of action (search, analysis, review, validation, etc.)",
    )

    result: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Result or output from the action",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
        comment="Timestamp when the log entry was created",
    )

    def __repr__(self) -> str:
        return f"<AgentLog(id={self.id}, agent={self.agent_name}, action={self.action}, created_at={self.created_at})>"
