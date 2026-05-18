# AgileAI — Database Schema Reference

85 tables · SQLite · SQLAlchemy 2.0 ORM

## Design Principles

- Every persistent table has `created_at` + `updated_at` (via `TimestampMixin`)
- Event/log tables add `occurred_at` (when it happened vs when it was recorded)
- All PKs are UUID strings (TEXT, 36 chars)
- All FKs have explicit `ondelete` cascade or set-null behavior
- Status fields use CHECK constraints — no lookup tables for fixed vocabularies
- Configurable vocabularies (roles, permissions, skills) have their own tables
- `actor_id` + `actor_type` polymorphic pattern used throughout for human/agent disambiguation
- Compression agent writes `summary` fields asynchronously — never block on them

## Table Groups

### AI & Identity (4 tables)

| Table | Key fields | Notes |
|---|---|---|
| `ai_models` | provider, model_name, is_local, cost_input/output_per_1k | Local Ollama or external API |
| `agents` | name, model_id FK, role, system_prompt, temperature | role: actor/reviewer/assistant/compressor/scrum_master |
| `users` | username, email, password_hash, timezone | Human actors |
| `api_keys` | owner_id+owner_type, key_hash, scope_json, expires_at | Never store raw keys |

### Skills (3 tables)

| Table | Key fields |
|---|---|
| `skill_definitions` | name, category (technical/regulatory/domain/language/tool) |
| `agent_skills` | agent_id, skill_id, proficiency_level |
| `issue_skill_requirements` | issue_id, skill_id, required_level, is_mandatory |

### RBAC (4 tables)

| Table | Key fields | Notes |
|---|---|---|
| `roles` | name, scope (system/project), is_built_in | 11 built-in roles seeded on install |
| `permissions` | resource, action → composite `name` | e.g. 'issue:create' |
| `role_permissions` | role_id, permission_id | Bridge |
| `actor_role_assignments` | actor_id, actor_type, role_id, project_id (NULL=global), expires_at | Replaces project_members |

### Teams (4 tables)

| Table | Key fields |
|---|---|
| `assignee_teams` | name, project_id, team_lead_id/type, team_type (mixed/human_only/agent_only) |
| `assignee_team_members` | team_id, member_id, member_type, role_in_team |
| `agent_teams` | name, project_id, lead_agent_id — agent-only coordination groups |
| `agent_team_members` | team_id, agent_id, member_role |

### Projects (4 tables)

| Table | Key fields |
|---|---|
| `projects` | slug, status, classification_id, po_id/type, sm_id/type |
| `labels` | project_id (NULL=global), name, color |
| `project_metadata` | project_id + key → value (key-value config store) |
| `data_classifications` | name, allowed_roles_json, requires_approval_to_view |

### Issues (8 tables)

| Table | Key fields | Notes |
|---|---|---|
| `issues` | project_id, parent_issue_id (self-ref), issue_type, status, priority, importance, **difficulty**, story_points, progress_pct | Epics = issue_type='epic' — no separate table |
| `issue_labels` | issue_id, label_id | Bridge |
| `issue_links` | source_id, target_id, link_type (blocks/requires/relates_to/duplicates) | |
| `issue_assignments` | issue_id, actor_id, actor_type, role (primary/reviewer/observer) | |
| `issue_watchers` | issue_id, actor_id, actor_type | |
| `issue_instructions` | issue_id, instruction_type, priority (must/should/could), target_actor_type, order_index | Gateway enforces 'must' |
| `instruction_completions` | instruction_id, actor_id, status, completion_note | Audit: was it followed? |
| `issue_templates` | issue_type, default_priority/difficulty, checklist_json | |

**Issue status flow:**
```
backlog → ready → in_progress → in_review → done
                      ↓
                   blocked → (unblocked) → in_progress
```

**Issue difficulty levels:** trivial · easy · medium · hard · very_hard · research

### Sprints (6 tables)

| Table | Key fields |
|---|---|
| `sprints` | project_id, sprint_number, status (planned/active/completed), start_date, end_date |
| `sprint_issues` | sprint_id, issue_id |
| `sprint_goals` | sprint_id, goal_text, is_achieved |
| `sprint_capacity` | sprint_id, actor_id/type, planned_hours, actual_hours, availability_pct |
| `burndown_snapshots` | sprint_id, snapshot_date, total/completed/remaining_points, ideal_remaining |
| `ceremonies` | sprint_id, ceremony_type, scheduled_at, facilitator_id, summary |

**Ceremony types:** sprint_planning · daily_standup · sprint_review · sprint_retrospective · backlog_refinement

### Quality Gates (6 tables)

| Table | Key fields |
|---|---|
| `definition_of_ready` | project_id (NULL=global), issue_type (NULL=all), criterion, order_index |
| `definition_of_done` | project_id, issue_type, criterion, order_index |
| `dor_checks` | issue_id, criterion_id, passed, checked_by_id |
| `dod_checks` | issue_id, criterion_id, passed, checked_by_id |
| `reviews` | issue_id, reviewer_id/type, verdict (pass/fail/pass_with_notes), score, summary |
| `review_criteria` | project_id, issue_type, criterion, weight, is_blocking |

### Workflow & Automation (6 tables)

| Table | Key fields |
|---|---|
| `status_transitions` | issue_id, from_status, to_status, actor_id/type, trigger_source |
| `handovers` | issue_id, sender/receiver id+type, handover_type, status (pending/accepted/rejected) |
| `impediments` | issue_id (nullable), sprint_id, severity, status, raised_by_id |
| `workflows` | trigger_event, conditions_json, is_active |
| `workflow_steps` | workflow_id, step_order, action_type, config_json, on_failure |
| `workflow_runs` | workflow_id, trigger_payload_json, status, current_step |

### Regulatory & Compliance (4 tables)

| Table | Key fields | Notes |
|---|---|---|
| `compliance_checks` | issue_id, requirement_ref, standard, status (pending/passed/failed/waived) | IAEA-SSG-25, ISO-9001 |
| `approval_workflows` | name, issue_type, steps_json (ordered approver roles) | |
| `approval_requests` | issue_id, workflow_id, step_number, status (pending/approved/rejected) | |
| `access_log` | actor_id/type, resource_type/id, action, result, occurred_at | **Immutable — never updated or deleted** |

### Agent Operations (9 tables)

| Table | Key fields |
|---|---|
| `agent_availability` | agent_id (unique), status, current_task_count, last_heartbeat_at |
| `task_queue` | issue_id, agent_id, priority (1-10), status, attempts |
| `execution_logs` | agent_id, issue_id, model_id, tokens_input/output, cost_usd, **output_summary** |
| `agent_feedback` | agent_id, score (1-5), correction_text — human rating of agent output |
| `agent_logs` | agent_id, log_level, **log_type**, message, payload_json — behavioral audit |
| `agent_messages` | from_agent_id, to_actor_id/type, message_type, parent_message_id |
| `agent_token_usage` | agent_id, model_id, period_type, tokens_total, cost_usd — rolled-up metrics |
| `agent_token_budgets` | agent_id/model_id (nullable), budget_type, token_limit, action_on_exceed, fallback_model_id |
| `token_budget_alerts` | budget_id, alert_type, usage_pct, is_resolved |

### Memory & Compression (4 tables)

| Table | Key fields | Notes |
|---|---|---|
| `project_memory` | scope_type (system/project/issue/agent), scope_id, memory_type, importance, **superseded_by_id** (self-ref) | Living knowledge base |
| `context_compression_rules` | context_type, agent_role, total_token_budget, tier_config_json, compressor_agent_id | Configurable compression |
| `context_snapshots` | agent_id, issue_id, **context_hash**, token_count, compression_ratio | Differential context cache |
| `content_embeddings` | entity_type, entity_id, chunk_index, embedding_model, embedding_blob | 768-dim vectors |

**Memory types:** fact · decision · lesson · constraint · preference · context

**Supersession chain:** When a memory is updated, old record gets `superseded_by_id` pointing to new record. Query `WHERE is_active=TRUE AND superseded_by_id IS NULL` for current state.

### Deliverables (5 tables)

| Table | Key fields | Notes |
|---|---|---|
| `deliverables` | issue_id, version, status, storage_type, storage_path, **file_hash** (SHA-256), document_number, **valid_until** | Formal output with integrity |
| `deliverable_status_history` | deliverable_id, from/to_status, changed_by_id, triggered_by | |
| `deliverable_distributions` | deliverable_id, recipient_id/type, distribution_method, acknowledged_at | |
| `deliverable_dependencies` | deliverable_id, depends_on_id, dependency_type | |
| `expected_deliverables` | issue_type, project_id, is_mandatory — defines what must be produced | |

**Deliverable status flow:** draft → under_review → approved / rejected → superseded / archived / expired

**Storage types:** local · network_share · git · s3_compatible · url · dms

### Reports (3 tables)

| Table | Key fields |
|---|---|
| `report_definitions` | report_type, scope_type, query_config_json, template |
| `report_instances` | definition_id, content, **summary** (agent-generated), compression_method, token_count_full/compressed |
| `report_schedules` | definition_id, cron_expression, next_run_at |

### History & Audit (4 tables)

| Table | Key fields | Notes |
|---|---|---|
| `issue_change_log` | issue_id, field_name, old_value, new_value, **is_diff**, source, timestamp | Field-level change audit |
| `notes` | entity_type+entity_id (polymorphic), note_type, **summary** (auto-generated), visibility | Free-text annotation |
| `velocity_records` | sprint_id, planned/completed/carry_over_points | One per sprint |
| `time_entries` | issue_id, actor_id/type, duration_minutes, work_date | |

### Notifications (3 tables)

| Table | Key fields |
|---|---|
| `notification_rules` | event_type, conditions_json, recipient_type, channel |
| `notification_templates` | channel, body_template, variables_json |
| `notifications` | recipient_id, channel, status (pending/sent/read/failed) |

### Knowledge Base (3 tables)

| Table | Key fields |
|---|---|
| `wiki_pages` | project_id, parent_page_id (self-ref), slug, content, **page_summary** |
| `wiki_page_versions` | page_id, version_number, content, changed_by_id |
| `attachments` | entity_type+entity_id (polymorphic), file_path, file_hash, uploaded_by_id |

### Contacts & Remote Control (2 tables)

| Table | Key fields |
|---|---|
| `user_contacts` | user_id, contact_type, telegram_chat_id, **can_send_commands**, allowed_commands_json |
| `telegram_commands` | user_id, chat_id, command, subcommand, status, response_text |

### Jobs & Prompts & Analytics (6 tables)

| Table | Key fields |
|---|---|
| `background_jobs` | job_type, entity_type/id, assigned_agent_id, status, priority, attempts |
| `prompt_templates` | issue_type, agent_role, content, version |
| `prompt_versions` | template_id, version_number, content |
| `prompt_fragments` | fragment_type (system/few_shot/tool_desc/constraint), content |
| `model_performance` | model_id, task_type, avg_feedback_score, sample_count |

---

## Summary Fields (Compression Agent Targets)

Fields auto-populated by the Compressor agent via `background_jobs`:

| Table | Field | Max tokens | Model |
|---|---|---|---|
| `issues` | `description_summary` | 60 | phi3:mini |
| `notes` | `summary` | 30 | phi3:mini |
| `execution_logs` | `output_summary` | 80 | phi3:mini |
| `wiki_pages` | `page_summary` | 80 | mistral:7b |
| `report_instances` | `summary` | 100 | mistral:7b |
| `agent_messages` | `summary` | 30 | phi3:mini |
| `handovers` | `summary` | 50 | phi3:mini |
| `deliverables` | `description_summary` | 60 | phi3:mini |

---

## Key Indexes

Beyond FK indexes, these columns are indexed for query performance:

```sql
issues(status), issues(priority), issues(project_id), issues(assignee_id)
agent_logs(agent_id, occurred_at)
access_log(actor_id, occurred_at)
background_jobs(status, job_type)
content_embeddings(entity_type, entity_id)
context_snapshots(agent_id, issue_id)
project_memory(scope_type, scope_id)
```
