"""
AgileAI SQLAlchemy models — 85 tables across 14 concern groups.

Import this module to register all models with the metadata
before calling Base.metadata.create_all() or running Alembic migrations.

Note: Some model modules are stubbed for development/testing until
all models are fully implemented.
"""

# Support both relative and absolute imports
try:
    from .base import Base, TimestampMixin, ActionTimestampMixin, generate_uuid
    from .identity import AIModel, Agent, User, APIKey
    from .issues import (
        Issue, IssueLabel, IssueLink, IssueAssignment, IssueWatcher,
        IssueInstruction, InstructionCompletion, IssueTemplate,
    )
except ImportError:
    from base import Base, TimestampMixin, ActionTimestampMixin, generate_uuid
    from identity import AIModel, Agent, User, APIKey
    from issues import (
        Issue, IssueLabel, IssueLink, IssueAssignment, IssueWatcher,
        IssueInstruction, InstructionCompletion, IssueTemplate,
    )

# Create inline stubs for missing modules (will be replaced with real imports later)
from sqlalchemy import String, ForeignKey, Integer, Boolean, Text, DateTime, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import Optional

# RBAC
class Role(Base, TimestampMixin):
    __tablename__ = "roles"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String(100), nullable=False)

class Permission(Base, TimestampMixin):
    __tablename__ = "permissions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String(100), nullable=False)

class RolePermission(Base):
    __tablename__ = "role_permissions"
    role_id: Mapped[str] = mapped_column(String(36), ForeignKey("roles.id"), primary_key=True)
    permission_id: Mapped[str] = mapped_column(String(36), ForeignKey("permissions.id"), primary_key=True)

class ActorRoleAssignment(Base, TimestampMixin):
    __tablename__ = "actor_role_assignments"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    actor_id: Mapped[str] = mapped_column(String(36), nullable=False)
    role_id: Mapped[str] = mapped_column(String(36), ForeignKey("roles.id"), nullable=False)

BUILT_IN_ROLES = {}

# Skills
class SkillDefinition(Base, TimestampMixin):
    __tablename__ = "skill_definitions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String(100), nullable=False)

class AgentSkill(Base, TimestampMixin):
    __tablename__ = "agent_skills"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    agent_id: Mapped[str] = mapped_column(String(36), ForeignKey("agents.id"), nullable=False, index=True)
    skill_id: Mapped[str] = mapped_column(String(36), ForeignKey("skill_definitions.id"), nullable=False)

class IssueSkillRequirement(Base):
    __tablename__ = "issue_skill_requirements"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    issue_id: Mapped[str] = mapped_column(String(36), ForeignKey("issues.id"), nullable=False)

# Teams
class AssigneeTeam(Base, TimestampMixin):
    __tablename__ = "assignee_teams"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String(100), nullable=False)

class AssigneeTeamMember(Base, TimestampMixin):
    __tablename__ = "assignee_team_members"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    team_id: Mapped[str] = mapped_column(String(36), ForeignKey("assignee_teams.id"), nullable=False)

class AgentTeam(Base, TimestampMixin):
    __tablename__ = "agent_teams"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)

class AgentTeamMember(Base, TimestampMixin):
    __tablename__ = "agent_team_members"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)

# Projects
class Project(Base, TimestampMixin):
    __tablename__ = "projects"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    issues: Mapped[list["Issue"]] = relationship("Issue")

class Label(Base, TimestampMixin):
    __tablename__ = "labels"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String(100), nullable=False)

class ProjectMetadata(Base, TimestampMixin):
    __tablename__ = "project_metadata"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)

class DataClassification(Base, TimestampMixin):
    __tablename__ = "data_classifications"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)

# Sprints
class Sprint(Base, TimestampMixin):
    __tablename__ = "sprints"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    project_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("projects.id"), nullable=True, index=True)
    status: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, default="planned")
    # planned | active | completed | cancelled
    goal: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    start_date: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    end_date: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    velocity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

class SprintIssue(Base):
    __tablename__ = "sprint_issues"
    sprint_id: Mapped[str] = mapped_column(String(36), ForeignKey("sprints.id"), primary_key=True)
    issue_id: Mapped[str] = mapped_column(String(36), ForeignKey("issues.id"), primary_key=True)
    added_at: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)

class SprintGoal(Base, TimestampMixin):
    __tablename__ = "sprint_goals"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    sprint_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("sprints.id"), nullable=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, default="not_started")
    # not_started | in_progress | achieved | missed
    order_index: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=0)

class SprintCapacity(Base, TimestampMixin):
    __tablename__ = "sprint_capacity"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    sprint_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("sprints.id"), nullable=True, index=True)
    member_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    member_type: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    # user | agent
    available_hours: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    story_points_capacity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

class BurndownSnapshot(Base, TimestampMixin):
    __tablename__ = "burndown_snapshots"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    sprint_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("sprints.id"), nullable=True, index=True)
    snapshot_date: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    remaining_points: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    completed_points: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    total_points: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

class Ceremony(Base, TimestampMixin):
    __tablename__ = "ceremonies"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    sprint_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("sprints.id"), nullable=True, index=True)
    ceremony_type: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    # planning | review | retro | standup
    scheduled_at: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    duration_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

class StandupRecord(Base, TimestampMixin):
    __tablename__ = "standup_records"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    sprint_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("sprints.id"), nullable=True, index=True)
    participant_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    participant_type: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    # user | agent
    recorded_date: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

class StandupItem(Base, TimestampMixin):
    __tablename__ = "standup_items"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    record_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("standup_records.id"), nullable=True, index=True)
    category: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    # did | doing | blocker
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

# Quality gates
class DefinitionOfReady(Base, TimestampMixin):
    __tablename__ = "definition_of_ready"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id"), nullable=False, index=True)
    issue_type: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, index=True)
    criterion: Mapped[str] = mapped_column(String(100), nullable=False)
    order_index: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

class DefinitionOfDone(Base, TimestampMixin):
    __tablename__ = "definition_of_done"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)

class DORCheck(Base, TimestampMixin):
    __tablename__ = "dor_checks"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    issue_id: Mapped[str] = mapped_column(String(36), ForeignKey("issues.id"), nullable=False, index=True)
    criterion_id: Mapped[str] = mapped_column(String(36), ForeignKey("definition_of_ready.id"), nullable=False, index=True)
    passed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    checked_by_id: Mapped[str] = mapped_column(String(36), nullable=False)
    checked_by_type: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    issue_id: Mapped[str] = mapped_column(String(36), ForeignKey("issues.id"), nullable=False)

class DODCheck(Base, TimestampMixin):
    __tablename__ = "dod_checks"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)

class Review(Base, TimestampMixin):
    __tablename__ = "reviews"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)

class ReviewCriterion(Base, TimestampMixin):
    __tablename__ = "review_criteria"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)

# Workflow
class StatusTransition(Base, TimestampMixin):
    __tablename__ = "status_transitions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    issue_id: Mapped[str] = mapped_column(String(36), ForeignKey("issues.id"), nullable=False, index=True)
    from_status: Mapped[str] = mapped_column(String(30), nullable=False)
    to_status: Mapped[str] = mapped_column(String(30), nullable=False)
    actor_id: Mapped[str] = mapped_column(String(36), nullable=False)
    actor_type: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    trigger_source: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    issue: Mapped["Issue"] = relationship("Issue", back_populates="status_transitions")

class Handover(Base, TimestampMixin):
    __tablename__ = "handovers"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)

class Impediment(Base, TimestampMixin):
    __tablename__ = "impediments"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)

class Workflow(Base, TimestampMixin):
    __tablename__ = "workflows"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)

class WorkflowStep(Base, TimestampMixin):
    __tablename__ = "workflow_steps"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)

class WorkflowRun(Base, TimestampMixin):
    __tablename__ = "workflow_runs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)

# Regulatory
class ComplianceCheck(Base, TimestampMixin):
    __tablename__ = "compliance_checks"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)

class ApprovalWorkflow(Base, TimestampMixin):
    __tablename__ = "approval_workflows"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)

class ApprovalRequest(Base, TimestampMixin):
    __tablename__ = "approval_requests"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)

class AccessLog(Base, TimestampMixin):
    __tablename__ = "access_log"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)

# Agent ops
class AgentAvailability(Base, TimestampMixin):
    __tablename__ = "agent_availability"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)

class TaskQueue(Base, TimestampMixin):
    __tablename__ = "task_queue"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)

class ExecutionLog(Base, TimestampMixin):
    __tablename__ = "execution_logs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    issue_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("issues.id"), nullable=True)

class AgentFeedback(Base, TimestampMixin):
    __tablename__ = "agent_feedback"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)

class AgentLog(Base, TimestampMixin):
    __tablename__ = "agent_logs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)

class AgentMessage(Base, TimestampMixin):
    __tablename__ = "agent_messages"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)

class AgentTokenUsage(Base, TimestampMixin):
    __tablename__ = "agent_token_usage"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    model_id: Mapped[str] = mapped_column(String(36), ForeignKey("ai_models.id"), nullable=False, index=True)
    agent_id: Mapped[str] = mapped_column(String(36), ForeignKey("agents.id"), nullable=False, index=True)
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)

class AgentTokenBudget(Base, TimestampMixin):
    __tablename__ = "agent_token_budget"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    agent_id: Mapped[str] = mapped_column(String(36), ForeignKey("agents.id"), nullable=False, index=True)
    model_id: Mapped[str] = mapped_column(String(36), ForeignKey("ai_models.id"), nullable=False, index=True)
    monthly_limit: Mapped[int] = mapped_column(Integer, nullable=False)
    used: Mapped[int] = mapped_column(Integer, default=0)

class TokenBudgetAlert(Base, TimestampMixin):
    __tablename__ = "token_budget_alerts"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)

# Memory
class ProjectMemory(Base, TimestampMixin):
    __tablename__ = "project_memory"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)

class ContextCompressionRule(Base, TimestampMixin):
    __tablename__ = "context_compression_rules"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)

class ContextSnapshot(Base, TimestampMixin):
    __tablename__ = "context_snapshots"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)

class ContentEmbedding(Base, TimestampMixin):
    __tablename__ = "content_embeddings"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)

# History
class IssueChangeLog(Base, TimestampMixin):
    __tablename__ = "issue_change_log"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    issue_id: Mapped[str] = mapped_column(String(36), ForeignKey("issues.id"), nullable=False, index=True)
    field_name: Mapped[str] = mapped_column(String(100), nullable=False)
    old_value: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    new_value: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    source: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    is_diff: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    issue: Mapped["Issue"] = relationship("Issue", back_populates="change_log")

class Note(Base, TimestampMixin):
    __tablename__ = "notes"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)

class VelocityRecord(Base, TimestampMixin):
    __tablename__ = "velocity_records"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)

class TimeEntry(Base, TimestampMixin):
    __tablename__ = "time_entries"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)

# Deliverables
class Deliverable(Base, TimestampMixin):
    __tablename__ = "deliverables"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    issue_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("issues.id"), nullable=True)

class DeliverableStatusHistory(Base, TimestampMixin):
    __tablename__ = "deliverable_status_history"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)

class DeliverableDistribution(Base, TimestampMixin):
    __tablename__ = "deliverable_distributions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)

class DeliverableDependency(Base, TimestampMixin):
    __tablename__ = "deliverable_dependencies"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)

class ExpectedDeliverable(Base, TimestampMixin):
    __tablename__ = "expected_deliverables"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)

# Reports
class ReportDefinition(Base, TimestampMixin):
    __tablename__ = "report_definitions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)

class ReportInstance(Base, TimestampMixin):
    __tablename__ = "report_instances"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)

class ReportSchedule(Base, TimestampMixin):
    __tablename__ = "report_schedules"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)

# Notifications
class NotificationRule(Base, TimestampMixin):
    __tablename__ = "notification_rules"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)

class NotificationTemplate(Base, TimestampMixin):
    __tablename__ = "notification_templates"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)

class Notification(Base, TimestampMixin):
    __tablename__ = "notifications"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)

# Knowledge base
class WikiPage(Base, TimestampMixin):
    __tablename__ = "wiki_pages"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)

class WikiPageVersion(Base, TimestampMixin):
    __tablename__ = "wiki_page_versions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)

class Attachment(Base, TimestampMixin):
    __tablename__ = "attachments"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)

# Contacts
class UserContact(Base, TimestampMixin):
    __tablename__ = "user_contacts"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)

class TelegramCommand(Base, TimestampMixin):
    __tablename__ = "telegram_commands"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)

# Jobs
class BackgroundJob(Base, TimestampMixin):
    __tablename__ = "background_jobs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    job_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    entity_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    priority: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

# Prompts
class PromptTemplate(Base, TimestampMixin):
    __tablename__ = "prompt_templates"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)

class PromptVersion(Base, TimestampMixin):
    __tablename__ = "prompt_versions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)

class PromptFragment(Base, TimestampMixin):
    __tablename__ = "prompt_fragments"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)

# Analytics
class ModelPerformance(Base, TimestampMixin):
    __tablename__ = "model_performance"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)

__all__ = [
    "Base",
    "TimestampMixin",
    "ActionTimestampMixin",
    "generate_uuid",
    "AIModel",
    "Agent",
    "User",
    "APIKey",
    "Role",
    "Permission",
    "RolePermission",
    "ActorRoleAssignment",
    "BUILT_IN_ROLES",
    "SkillDefinition",
    "AgentSkill",
    "IssueSkillRequirement",
    "AssigneeTeam",
    "AssigneeTeamMember",
    "AgentTeam",
    "AgentTeamMember",
    "Project",
    "Label",
    "ProjectMetadata",
    "DataClassification",
    "Issue",
    "IssueLabel",
    "IssueLink",
    "IssueAssignment",
    "IssueWatcher",
    "IssueInstruction",
    "InstructionCompletion",
    "IssueTemplate",
    "Sprint",
    "SprintIssue",
    "SprintGoal",
    "SprintCapacity",
    "BurndownSnapshot",
    "Ceremony",
    "StandupRecord",
    "StandupItem",
    "DefinitionOfReady",
    "DefinitionOfDone",
    "DORCheck",
    "DODCheck",
    "Review",
    "ReviewCriterion",
    "StatusTransition",
    "Handover",
    "Impediment",
    "Workflow",
    "WorkflowStep",
    "WorkflowRun",
    "ComplianceCheck",
    "ApprovalWorkflow",
    "ApprovalRequest",
    "AccessLog",
    "AgentAvailability",
    "TaskQueue",
    "ExecutionLog",
    "AgentFeedback",
    "AgentLog",
    "AgentMessage",
    "AgentTokenUsage",
    "AgentTokenBudget",
    "TokenBudgetAlert",
    "ProjectMemory",
    "ContextCompressionRule",
    "ContextSnapshot",
    "ContentEmbedding",
    "IssueChangeLog",
    "Note",
    "VelocityRecord",
    "TimeEntry",
    "Deliverable",
    "DeliverableStatusHistory",
    "DeliverableDistribution",
    "DeliverableDependency",
    "ExpectedDeliverable",
    "ReportDefinition",
    "ReportInstance",
    "ReportSchedule",
    "NotificationRule",
    "NotificationTemplate",
    "Notification",
    "WikiPage",
    "WikiPageVersion",
    "Attachment",
    "UserContact",
    "TelegramCommand",
    "BackgroundJob",
    "PromptTemplate",
    "PromptVersion",
    "PromptFragment",
    "ModelPerformance",
]
