"""
AgileAI SQLAlchemy models — 85 tables across 14 concern groups.

Import this module to register all models with the metadata
before calling Base.metadata.create_all() or running Alembic migrations.
"""
from .base import Base, TimestampMixin, ActionTimestampMixin, generate_uuid

# Identity & AI
from .identity import AIModel, Agent, User, APIKey

# RBAC
from .rbac import Role, Permission, RolePermission, ActorRoleAssignment, BUILT_IN_ROLES

# Skills
from .skills import SkillDefinition, AgentSkill, IssueSkillRequirement

# Teams
from .teams import AssigneeTeam, AssigneeTeamMember, AgentTeam, AgentTeamMember

# Projects
from .projects import Project, Label, ProjectMetadata, DataClassification

# Issues
from .issues import (
    Issue, IssueLabel, IssueLink, IssueAssignment, IssueWatcher,
    IssueInstruction, InstructionCompletion, IssueTemplate,
)

# Sprints & ceremonies
from .sprints import (
    Sprint, SprintIssue, SprintGoal, SprintCapacity,
    BurndownSnapshot, Ceremony, StandupRecord, StandupItem,
)

# Quality gates
from .quality import (
    DefinitionOfReady, DefinitionOfDone, DORCheck, DODCheck,
    Review, ReviewCriterion,
)

# Workflow & automation
from .workflow import (
    StatusTransition, Handover, Impediment,
    Workflow, WorkflowStep, WorkflowRun,
)

# Regulatory & compliance
from .regulatory import (
    ComplianceCheck, ApprovalWorkflow, ApprovalRequest, AccessLog,
)

# Agent operations
from .agent_ops import (
    AgentAvailability, TaskQueue, ExecutionLog, AgentFeedback,
    AgentLog, AgentMessage,
    AgentTokenUsage, AgentTokenBudget, TokenBudgetAlert,
)

# Memory
from .memory import ProjectMemory

# History & audit
from .history import IssueChangeLog, Note, VelocityRecord, TimeEntry

# Compression & embeddings
from .compression import ContextCompressionRule, ContextSnapshot, ContentEmbedding

# Deliverables
from .deliverables import (
    Deliverable, DeliverableStatusHistory, DeliverableDistribution,
    DeliverableDependency, ExpectedDeliverable,
)

# Reports
from .misc import ReportDefinition, ReportInstance, ReportSchedule

# Notifications
from .misc import NotificationRule, NotificationTemplate, Notification

# Knowledge base
from .misc import WikiPage, WikiPageVersion, Attachment

# Contacts & Telegram
from .misc import UserContact, TelegramCommand

# Background jobs
from .misc import BackgroundJob

# Prompts
from .misc import PromptTemplate, PromptVersion, PromptFragment

# Analytics
from .misc import ModelPerformance

__all__ = [
    "Base",
    # Identity
    "AIModel", "Agent", "User", "APIKey",
    # RBAC
    "Role", "Permission", "RolePermission", "ActorRoleAssignment",
    # Skills
    "SkillDefinition", "AgentSkill", "IssueSkillRequirement",
    # Teams
    "AssigneeTeam", "AssigneeTeamMember", "AgentTeam", "AgentTeamMember",
    # Projects
    "Project", "Label", "ProjectMetadata", "DataClassification",
    # Issues
    "Issue", "IssueLabel", "IssueLink", "IssueAssignment", "IssueWatcher",
    "IssueInstruction", "InstructionCompletion", "IssueTemplate",
    # Sprints
    "Sprint", "SprintIssue", "SprintGoal", "SprintCapacity",
    "BurndownSnapshot", "Ceremony", "StandupRecord", "StandupItem",
    # Quality
    "DefinitionOfReady", "DefinitionOfDone", "DORCheck", "DODCheck",
    "Review", "ReviewCriterion",
    # Workflow
    "StatusTransition", "Handover", "Impediment",
    "Workflow", "WorkflowStep", "WorkflowRun",
    # Regulatory
    "ComplianceCheck", "ApprovalWorkflow", "ApprovalRequest", "AccessLog",
    # Agent ops
    "AgentAvailability", "TaskQueue", "ExecutionLog", "AgentFeedback",
    "AgentLog", "AgentMessage",
    "AgentTokenUsage", "AgentTokenBudget", "TokenBudgetAlert",
    # Memory & compression
    "ProjectMemory", "ContextCompressionRule", "ContextSnapshot", "ContentEmbedding",
    # History
    "IssueChangeLog", "Note", "VelocityRecord", "TimeEntry",
    # Deliverables
    "Deliverable", "DeliverableStatusHistory", "DeliverableDistribution",
    "DeliverableDependency", "ExpectedDeliverable",
    # Reports
    "ReportDefinition", "ReportInstance", "ReportSchedule",
    # Notifications
    "NotificationRule", "NotificationTemplate", "Notification",
    # Knowledge
    "WikiPage", "WikiPageVersion", "Attachment",
    # Contacts
    "UserContact", "TelegramCommand",
    # Jobs
    "BackgroundJob",
    # Prompts
    "PromptTemplate", "PromptVersion", "PromptFragment",
    # Analytics
    "ModelPerformance",
]
