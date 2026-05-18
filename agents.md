# AgileAI — Agent System

## Overview

AgileAI treats AI agents as first-class team members. Every agent has an identity, a role, a skill set, and an activity history — exactly like a human user. Agents are assigned issues, report progress, produce deliverables, review work, and communicate with each other through the same platform infrastructure humans use.

The agent system has four components:

| Component | Responsibility |
|---|---|
| **Agent Registry** | Identity, roles, skills, availability |
| **Agent Gateway** | Task dispatch, protocol handling (REST + MCP) |
| **Compression Agent** | Local offline summarization and embedding |
| **Agent Protocol** | How agents receive, execute, and report tasks |

---

## Agent Roles

### Actor Agent
Executes assigned tasks. Receives a task, reads issue context (compressed), follows instructions, produces output (text, code, document), attaches artifact, updates issue status, creates handover if required.

**Typical assignments:** code generation, document drafting, data analysis, dispersion model runs, configuration generation.

**Database identity:** `agents.role = 'actor'`

### Reviewer Agent
Validates completed work against review criteria and Definition of Done. Does not produce primary deliverables — it evaluates them. Issues a `verdict` of `pass`, `fail`, or `pass_with_notes`. On `fail`, creates a rejection handover back to the actor.

**Typical assignments:** code review, document review, compliance verification, output validation.

**Database identity:** `agents.role = 'reviewer'`

### Assistant Agent
Advisory role. Does not hold assigned tasks autonomously. Responds to queries from humans and other agents, suggests priorities, auto-generates subtasks from issue descriptions, recommends skill requirements, retrieves relevant memories.

**Typical activations:** sprint planning support, backlog grooming, impediment suggestions, standup digest generation.

**Database identity:** `agents.role = 'assistant'`

### Compressor Agent
The most important agent for performance. Runs entirely locally via Ollama. Never assigned issues. Watches `background_jobs` continuously and processes summarization and embedding tasks. Writes `summary` fields back to notes, execution logs, wiki pages, and agent messages. Generates vector embeddings for semantic memory retrieval.

**Model recommendations:**
- Short summaries (notes, messages): `phi3:mini` or `llama3.2:3b`
- Rich summaries (reports, wiki pages): `mistral:7b`
- Context compression: `mistral:7b`
- Embeddings: `nomic-embed-text`
- Arabic content: `qwen2.5:7b`
- Code/technical issues: `qwen2.5-coder:7b`

**Database identity:** `agents.role = 'compressor'`

### Scrum Master Agent
Facilitates Scrum ceremonies. Monitors sprint progress, detects impediments from agent logs and issue blockers, generates standup digests, sends ceremony reminders, posts retrospective summaries. Can be paired with a human SM or operate independently on lower-stakes projects.

**Database identity:** `agents.role = 'scrum_master'`

---

## Agent Registration

Every agent must be registered in the `agents` table before it can receive tasks. Registration requires:

1. An `ai_models` record for the underlying model
2. An `agents` record with role, system prompt, and temperature
3. `actor_role_assignments` records for each project the agent works on
4. `agent_skills` records declaring what the agent can do
5. An `api_keys` record for the agent's authentication token
6. An `agent_availability` record (created automatically on first registration)

### CLI Registration

```bash
# Register a local compressor agent
agileai agent register \
  --name "Zephyr" \
  --model "phi3:mini" \
  --provider "ollama" \
  --role "compressor" \
  --local \
  --temperature 0.1 \
  --description "Local summarization and embedding agent"

# Register a Claude-powered actor agent
agileai agent register \
  --name "Atlas" \
  --model "claude-sonnet-4-6" \
  --provider "anthropic" \
  --role "actor" \
  --temperature 0.7 \
  --skills "python,fastapi,regulatory_compliance,technical_writing"

# Assign agent to a project with a role
agileai agent assign \
  --agent "Atlas" \
  --project "jrtr-safety" \
  --role "agent_actor"
```

### Programmatic Registration

```python
from agileai.services.agents import AgentService
from agileai.models import AIModel, Agent

async def register_agent(session):
    model = AIModel(
        provider="ollama",
        model_name="phi3:mini",
        model_type="llm",
        is_local=True,
        api_endpoint="http://localhost:11434",
        is_active=True,
    )
    session.add(model)
    await session.flush()

    agent = Agent(
        name="Zephyr",
        model_id=model.id,
        role="compressor",
        temperature=0.1,
        max_concurrent_tasks=20,
        system_prompt=COMPRESSOR_SYSTEM_PROMPT,
    )
    session.add(agent)
    await session.commit()
```

---

## Agent Lifecycle

```
┌─────────────────────────────────────────────────────────────────┐
│  1. TASK CREATED                                                │
│     Issue assigned → agent_id + issue_id written to task_queue │
└──────────────────────────────┬──────────────────────────────────┘
                               ↓
┌─────────────────────────────────────────────────────────────────┐
│  2. CONTEXT ASSEMBLY (Compression Pipeline)                     │
│     Tier 1: issue core (title, status, type, difficulty)        │
│     Tier 2: must-priority instructions                          │
│     Tier 3: top-5 semantic memories (nomic-embed-text)          │
│     Tier 4: last 3 note summaries                               │
│     Tier 5: recent change log entries                           │
│     Differential check → only send delta if context unchanged   │
│     Total: ~1,200–2,000 tokens (from potentially 12,000+ raw)   │
└──────────────────────────────┬──────────────────────────────────┘
                               ↓
┌─────────────────────────────────────────────────────────────────┐
│  3. INSTRUCTION ENFORCEMENT                                     │
│     Read issue_instructions WHERE priority = 'must'             │
│     Inject as hard constraints                                  │
│     Sequence instructions: enforce order_index                  │
│     Compliance instructions: flag for human gate if required    │
└──────────────────────────────┬──────────────────────────────────┘
                               ↓
┌─────────────────────────────────────────────────────────────────┐
│  4. EXECUTION                                                   │
│     Agent processes task using model API                        │
│     Writes AgentLog entries throughout                          │
│     Updates task_queue status = 'running'                       │
│     Writes ExecutionLog on completion (tokens, cost, output)    │
└──────────────────────────────┬──────────────────────────────────┘
                               ↓
┌─────────────────────────────────────────────────────────────────┐
│  5. REPORTING                                                   │
│     Post artifact (if produced)                                 │
│     Write instruction_completions for each instruction          │
│     Update issue.progress_pct                                   │
│     Write IssueChangeLog entries for field changes              │
│     Update context_snapshot (hash + compressed context)         │
└──────────────────────────────┬──────────────────────────────────┘
                               ↓
┌─────────────────────────────────────────────────────────────────┐
│  6. HANDOVER / REVIEW TRIGGER                                   │
│     If issue_type requires review → create Handover record      │
│     → Reviewer agent receives task                              │
│     On pass → issue status = 'done'                             │
│     On fail → rejection handover back to actor                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Agent Protocol

### REST Protocol (Polling)

Agents poll the Gateway API for available tasks:

```http
GET /api/v1/gateway/tasks/pending?agent_id={id}
Authorization: Bearer {agent_api_key}

Response 200:
{
  "task_id": "...",
  "issue_id": "...",
  "context": "...compressed context string...",
  "instructions": [...],
  "token_budget": 2000
}
```

Report progress:
```http
PATCH /api/v1/gateway/tasks/{task_id}
{
  "status": "running",
  "progress_pct": 45,
  "note": "Completed sections 1-3 of the analysis"
}
```

Submit completion:
```http
POST /api/v1/gateway/tasks/{task_id}/complete
{
  "status": "completed",
  "output_text": "...",
  "artifact": { "type": "document", "path": "/outputs/report.md" },
  "tokens_used": { "input": 1240, "output": 890 },
  "instruction_completions": [
    { "instruction_id": "...", "status": "completed" }
  ]
}
```

### MCP Protocol (Native)

For Claude and MCP-compatible agents, the Gateway exposes an MCP server. Agents can:

```
Tools available via MCP:
  agileai.get_assigned_tasks()
  agileai.get_issue_context(issue_id)
  agileai.get_project_memory(project_id, scope?, importance?)
  agileai.update_issue_status(issue_id, status, note?)
  agileai.post_note(entity_type, entity_id, content, note_type?)
  agileai.create_handover(issue_id, receiver_id, type, summary?)
  agileai.complete_task(task_id, output, artifact?)
  agileai.log_action(log_type, message, payload?)
  agileai.read_instructions(issue_id)
  agileai.complete_instruction(instruction_id, status, note?)
```

MCP connection:
```json
{
  "mcpServers": {
    "agileai": {
      "url": "http://localhost:8000/mcp/v1",
      "headers": { "Authorization": "Bearer {agent_api_key}" }
    }
  }
}
```

---

## Skill-Based Routing

When an issue enters the task queue, the Gateway automatically matches it to capable agents using the `issue_skill_requirements` and `agent_skills` tables:

```sql
-- Find agents capable of handling this issue
SELECT a.id, a.name, a.role,
       COUNT(CASE WHEN isr.is_mandatory THEN 1 END) AS mandatory_skills,
       COUNT(CASE WHEN isr.is_mandatory AND ags.agent_id IS NOT NULL THEN 1 END) AS matched_mandatory
FROM agents a
JOIN agent_availability av ON a.id = av.agent_id AND av.status = 'idle'
LEFT JOIN issue_skill_requirements isr ON isr.issue_id = :issue_id
LEFT JOIN agent_skills ags ON ags.agent_id = a.id AND ags.skill_id = isr.skill_id
WHERE a.role = 'actor' AND a.is_active = TRUE
GROUP BY a.id
HAVING matched_mandatory = mandatory_skills   -- All mandatory skills satisfied
ORDER BY matched_mandatory DESC, av.current_task_count ASC
LIMIT 1;
```

If no agent satisfies all mandatory skills, the issue is flagged `status = 'blocked'` and an impediment is created for the SM.

---

## Token Budget Enforcement

Before dispatching a task, the Gateway checks active `agent_token_budgets`:

```python
async def check_budget(agent_id: str, model_id: str, session) -> BudgetCheckResult:
    budgets = await get_active_budgets(agent_id, model_id, session)
    for budget in budgets:
        usage = await get_current_usage(agent_id, budget.budget_type, session)
        pct = (usage.tokens_total / budget.token_limit) * 100

        if pct >= 100:
            if budget.action_on_exceed == "switch_model":
                return BudgetCheckResult(allowed=True, use_model=budget.fallback_model_id)
            elif budget.action_on_exceed == "pause_agent":
                await pause_agent(agent_id, "Token budget exceeded", session)
                return BudgetCheckResult(allowed=False, reason="budget_exceeded")
            elif budget.action_on_exceed == "block_agent":
                return BudgetCheckResult(allowed=False, reason="budget_exceeded")

        if pct >= budget.alert_threshold_pct:
            await create_budget_alert(budget, agent_id, usage, pct, session)

    return BudgetCheckResult(allowed=True)
```

---

## Compression Agent Operation

The Compressor agent runs as a background service, continuously polling `background_jobs`:

```python
# Automatic jobs created when content is written:
# - note saved           → job_type='summarize', entity_type='note'
# - execution completed  → job_type='summarize', entity_type='execution_log'
# - issue description updated → job_type='embed', entity_type='issue'
# - wiki page saved      → job_type='summarize' + 'embed', entity_type='wiki_page'
# - memory created       → job_type='embed', entity_type='memory'

SUMMARIZE_PROMPT = """You are a context compression specialist.
Produce a {max_tokens}-token summary of the following content.
Preserve: decisions, blockers, status changes, compliance requirements.
Omit: greetings, verbose restatements, filler text.
Output only the summary — no preamble.

Content:
{content}"""

COMPRESS_CONTEXT_PROMPT = """You are compressing agent context.
Token budget: {budget} tokens.
Extract what an AI agent needs to act on this task:
- Current status and blockers
- Key decisions already made
- Hard constraints and compliance requirements
- Relevant recent activity

Context:
{raw_context}"""
```

---

## Inter-Agent Communication

Agents communicate via `agent_messages`. All messages are stored, threaded, and auditable:

```python
# Actor agent escalates to SM
msg = AgentMessage(
    from_agent_id=actor.id,
    to_actor_id=sm_agent.id,
    to_actor_type="agent",
    issue_id=issue.id,
    message_type="escalation",
    content="Cannot proceed: IAEA SSG-25 Factor 3 compliance check "
            "requires human approval before I can close this issue. "
            "Please assign an approval request.",
)

# Reviewer sends feedback to Actor
feedback_msg = AgentMessage(
    from_agent_id=reviewer.id,
    to_actor_id=actor.id,
    to_actor_type="agent",
    issue_id=issue.id,
    message_type="feedback",
    content="Review failed. Section 4.2 references outdated procedure. "
            "Please update to reference SOP-2025-014 Rev 3.",
    parent_message_id=original_task_msg.id,
)
```

---

## Telegram Remote Control

Users with `can_send_commands = True` on their `user_contacts` record can control the platform via Telegram:

| Command | Action |
|---|---|
| `/sprint status` | Returns current sprint board summary |
| `/sprint start [name]` | Starts a new sprint |
| `/issue create [title]` | Creates a backlog item |
| `/issue assign [id] [agent]` | Assigns issue to agent |
| `/agent status` | Lists all agent availability |
| `/agent pause [name]` | Pauses an agent |
| `/agent resume [name]` | Resumes a paused agent |
| `/budget report` | Shows token usage this week |
| `/standup` | Triggers SM agent standup digest |
| `/review [issue_id]` | Requests review of a completed issue |
| `/memory add [content]` | Adds a project memory |

All commands are validated against `allowed_commands_json` before execution. Denied commands are logged to `telegram_commands` with `status = 'denied'`.

---

## Built-in Agent Seed Data

On first install, the following agents are registered automatically:

| Name | Role | Model | Purpose |
|---|---|---|---|
| Zephyr | compressor | phi3:mini (local) | Summarization, short content |
| Zephyr-Embed | compressor | nomic-embed-text (local) | Vector embeddings |
| Hermes | scrum_master | mistral:7b (local) | Sprint facilitation, standups |
| Atlas | actor | claude-sonnet-4-6 | General task execution |
| Argus | reviewer | claude-sonnet-4-6 | Review and compliance |
| Minerva | assistant | claude-sonnet-4-6 | Advisory, backlog grooming |

Local agents (Zephyr, Hermes) require Ollama running at `http://localhost:11434`.
External agents (Atlas, Argus, Minerva) require `ANTHROPIC_API_KEY` in environment.

---

## Environment Variables

```bash
AGILEAI_DB_PATH=./agileai.db          # SQLite database path
AGILEAI_SECRET_KEY=...                 # JWT signing key
ANTHROPIC_API_KEY=sk-ant-...           # Claude API key
AGILEAI_OLLAMA_URL=http://localhost:11434  # Ollama endpoint
AGILEAI_TELEGRAM_TOKEN=...             # Telegram bot token
AGILEAI_SQL_ECHO=                      # Set to '1' for SQL logging
AGILEAI_HOST=127.0.0.1                 # API host
AGILEAI_PORT=8000                      # API port
```

---

## Adding a Custom Agent

1. Register the model in `ai_models`
2. Register the agent in `agents` with a detailed `system_prompt`
3. Add skills to `agent_skills`
4. Assign to projects via `actor_role_assignments`
5. Create an `api_keys` record with appropriate scopes
6. Set token budgets in `agent_token_budgets`
7. Configure compression rules for this agent's role in `context_compression_rules`

The agent will appear in the Web UI agent monitor and can immediately receive tasks via the Gateway.
