"""
Identity layer: AI models, agents, users, and API keys.

An Agent is a configured persona powered by an AIModel.
Worker = Agent (identity) + AIModel (engine).
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean, DateTime, Float, ForeignKey,
    Integer, String, Text, UniqueConstraint, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, generate_uuid


class AIModel(Base, TimestampMixin):
    """
    Registered AI model — local (Ollama) or external (API-based).
    Multiple agents can share the same model with different configurations.
    """

    __tablename__ = "ai_models"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    # e.g. 'anthropic', 'openai', 'ollama', 'local'
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    # e.g. 'claude-sonnet-4-6', 'phi3:mini', 'nomic-embed-text'
    model_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="llm"
    )
    # 'llm' | 'embedding' | 'vision' | 'code' | 'compressor'
    context_window: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    capabilities_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # JSON array: ["code","reasoning","vision","arabic","summarization"]
    api_endpoint: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    # For Ollama: 'http://localhost:11434'
    api_key_ref: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("api_keys.id"), nullable=True
    )
    is_local: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    cost_input_per_1k: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    cost_output_per_1k: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    max_tokens_output: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    agents: Mapped[list["Agent"]] = relationship("Agent", back_populates="model")
    token_usages: Mapped[list["AgentTokenUsage"]] = relationship(
        "AgentTokenUsage", back_populates="model", foreign_keys="AgentTokenUsage.model_id"
    )
    token_budgets: Mapped[list["AgentTokenBudget"]] = relationship(
        "AgentTokenBudget", back_populates="model", foreign_keys="AgentTokenBudget.model_id"
    )

    def __repr__(self) -> str:
        return f"<AIModel {self.provider}/{self.model_name}>"


class Agent(Base, TimestampMixin):
    """
    An AI agent — a configured persona with a role, skills, and a model.
    Can be assigned issues just like a human user.

    Roles:
        actor      — executes assigned tasks, reports artifacts
        reviewer   — validates deliverables against criteria
        assistant  — advises, suggests priorities, generates subtasks
        compressor — summarizes and embeds content locally (offline model)
        scrum_master — facilitates ceremonies, monitors impediments
    """

    __tablename__ = "agents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    model_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("ai_models.id"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(30), nullable=False)
    # 'actor' | 'reviewer' | 'assistant' | 'compressor' | 'scrum_master'
    system_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    temperature: Mapped[float] = mapped_column(Float, default=0.7, nullable=False)
    max_tokens: Mapped[int] = mapped_column(Integer, default=4096, nullable=False)
    max_concurrent_tasks: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    availability_status: Mapped[str] = mapped_column(
        String(20), default="idle", nullable=False
    )
    # 'idle' | 'busy' | 'paused' | 'offline' | 'error'
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    avatar_emoji: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    # Relationships
    model: Mapped["AIModel"] = relationship("AIModel", back_populates="agents")
    skills: Mapped[list["AgentSkill"]] = relationship(
        "AgentSkill", back_populates="agent"
    )
    availability: Mapped[Optional["AgentAvailability"]] = relationship(
        "AgentAvailability", back_populates="agent", uselist=False
    )
    token_usages: Mapped[list["AgentTokenUsage"]] = relationship(
        "AgentTokenUsage", back_populates="agent"
    )
    token_budgets: Mapped[list["AgentTokenBudget"]] = relationship(
        "AgentTokenBudget", back_populates="agent",
        foreign_keys="AgentTokenBudget.agent_id"
    )
    execution_logs: Mapped[list["ExecutionLog"]] = relationship(
        "ExecutionLog", back_populates="agent"
    )
    agent_logs: Mapped[list["AgentLog"]] = relationship(
        "AgentLog", back_populates="agent"
    )
    feedback_received: Mapped[list["AgentFeedback"]] = relationship(
        "AgentFeedback", back_populates="agent"
    )
    sent_messages: Mapped[list["AgentMessage"]] = relationship(
        "AgentMessage", back_populates="from_agent",
        foreign_keys="AgentMessage.from_agent_id"
    )

    def __repr__(self) -> str:
        return f"<Agent {self.name} [{self.role}]>"


class User(Base, TimestampMixin):
    """
    Human user of the platform.
    Can hold any project role (PO, SM, Developer, Reviewer).
    """

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    username: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    timezone: Mapped[str] = mapped_column(String(50), default="UTC", nullable=False)
    locale: Mapped[str] = mapped_column(String(10), default="en", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Relationships
    api_keys: Mapped[list["APIKey"]] = relationship(
        "APIKey", back_populates="user",
        primaryjoin="and_(APIKey.owner_id == User.id, APIKey.owner_type == 'user')",
        foreign_keys="APIKey.owner_id",
        viewonly=True,
    )
    contacts: Mapped[list["UserContact"]] = relationship(
        "UserContact", back_populates="user"
    )
    telegram_commands: Mapped[list["TelegramCommand"]] = relationship(
        "TelegramCommand", back_populates="user"
    )

    def __repr__(self) -> str:
        return f"<User {self.username}>"


class APIKey(Base):
    """
    Auth tokens for agents, external integrations, and human CLI access.
    Keys are stored as hashes — never in plain text.
    """

    __tablename__ = "api_keys"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    owner_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    owner_type: Mapped[str] = mapped_column(String(10), nullable=False)
    # 'user' | 'agent' | 'integration'
    key_hash: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    key_prefix: Mapped[str] = mapped_column(String(8), nullable=False)
    # First 8 chars of raw key shown in UI: "sk-abc123..."
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    scope_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # JSON array of allowed scopes: ["issues:read","issues:write","agents:run"]
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )

    # Relationships
    user: Mapped[Optional["User"]] = relationship(
        "User", back_populates="api_keys",
        primaryjoin="and_(APIKey.owner_id == User.id, APIKey.owner_type == 'user')",
        foreign_keys=[owner_id],
        viewonly=True,
    )

    def __repr__(self) -> str:
        return f"<APIKey {self.key_prefix}... [{self.owner_type}:{self.owner_id[:8]}]>"


# Avoid circular import — import here at module bottom