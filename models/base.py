"""
SQLAlchemy declarative base for all ORM models.

@TASK P0-T4 - SQLAlchemy ORM 모델 정의
@SPEC docs/planning/04-database-design.md#base-class
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""
    pass
