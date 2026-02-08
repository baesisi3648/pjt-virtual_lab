"""
Session model for storing user queries and final reports.

@TASK P0-T4 - SQLAlchemy ORM 모델 정의
@SPEC docs/planning/04-database-design.md#sessions-table
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import UUID, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class Session(Base):
    """
    Represents a user session with query and report data.

    Attributes:
        id: Unique session identifier (UUID)
        user_query: The user's initial query about NGT safety
        final_report: Generated safety assessment report (optional)
        created_at: Timestamp when the session was created
    """
    __tablename__ = "sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_query: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="User's query about NGT safety assessment",
    )

    final_report: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Generated safety assessment report",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
        comment="Timestamp when session was created",
    )

    def __repr__(self) -> str:
        return f"<Session(id={self.id}, created_at={self.created_at})>"
