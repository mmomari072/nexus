"""Re-export models from root package for consistency."""

import sys
from pathlib import Path

# Add root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import all models from root
from __init__ import (  # noqa: F401
    Base,
    TimestampMixin,
    ActionTimestampMixin,
    generate_uuid,
    # Identity & AI
    AIModel,
    Agent,
    User,
    APIKey,
    # RBAC
    Role,
    Permission,
    RolePermission,
    ActorRoleAssignment,
    BUILT_IN_ROLES,
    # Skills
    SkillDefinition,
    AgentSkill,
    IssueSkillRequirement,
    # Teams
    AssigneeTeam,
    AssigneeTeamMember,
    AgentTeam,
    AgentTeamMember,
    # Projects
    Project,
    Label,
    ProjectMetadata,
    DataClassification,
    # Issues
    Issue,
    IssueLabel,
    IssueLink,
    IssueAssignment,
    IssueWatcher,
    IssueInstruction,
    InstructionCompletion,
    IssueTemplate,
    # Sprints
    Sprint,
    SprintIssue,
    SprintGoal,
    SprintCapacity,
    BurndownSnapshot,
    Ceremony,
    StandupRecord,
    StandupItem,
    # Quality
    DefinitionOfReady,
    DefinitionOfDone,
    DORCheck,
    DODCheck,
    Review,
    ReviewCriterion,
    # Workflow
    StatusTransition,
    Handover,
    Impediment,
    Workflow,
    WorkflowStep,
    WorkflowRun,
    # Regulatory
    ComplianceCheck,
    ApprovalWorkflow,
    ApprovalRequest,
    AccessLog,
    # Agent ops
    AgentAvailability,
    TaskQueue,
    ExecutionLog,
    AgentFeedback,
    AgentLog,
    AgentMessage,
    AgentTokenUsage,
    AgentTokenBudget,
    TokenBudgetAlert,
    # Memory & compression
    ProjectMemory,
    ContextCompressionRule,
    ContextSnapshot,
    ContentEmbedding,
    # History
    IssueChangeLog,
    Note,
    VelocityRecord,
    TimeEntry,
    # Deliverables
    Deliverable,
    DeliverableStatusHistory,
    DeliverableDistribution,
    DeliverableDependency,
    ExpectedDeliverable,
    # Reports
    ReportDefinition,
    ReportInstance,
    ReportSchedule,
    # Notifications
    NotificationRule,
    NotificationTemplate,
    Notification,
    # Knowledge
    WikiPage,
    WikiPageVersion,
    Attachment,
    # Contacts
    UserContact,
    TelegramCommand,
    # Jobs
    BackgroundJob,
    # Prompts
    PromptTemplate,
    PromptVersion,
    PromptFragment,
    # Analytics
    ModelPerformance,
)

__all__ = [
    "Base",
    "TimestampMixin",
    "ActionTimestampMixin",
    "generate_uuid",
    # ... all other exports
]
