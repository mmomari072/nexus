"""Base SQLAlchemy models and mixins for AgileAI."""

import uuid
from datetime import datetime
from sqlalchemy import DateTime, func
from sqlalchemy.orm import declarative_base, Mapped, mapped_column


def generate_uuid() -> str:
    """Generate a UUID string."""
    return str(uuid.uuid4())


Base = declarative_base()


class TimestampMixin:
    """Adds created_at and updated_at timestamps to models."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class ActionTimestampMixin:
    """Adds action-specific timestamps."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
