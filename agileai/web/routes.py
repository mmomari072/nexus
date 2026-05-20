"""Web routes for AgileAI backlog interface."""

from typing import Optional

from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

import sys
from pathlib import Path
_root = Path(__file__).parent.parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from agileai.api.dependencies import get_db, create_access_token
from agileai.api.routers.auth import hash_password, verify_password

try:
    from __init__ import (
        User, Issue, Sprint, SprintIssue, SprintGoal, SprintCapacity,
        Ceremony, StandupRecord, AIModel, Agent,
    )
except ImportError:
    from agileai.models import User, Issue  # type: ignore

router = APIRouter(tags=["web"])

# ---------------------------------------------------------------------------
# Auth page template (centered, no sidebar)
# ---------------------------------------------------------------------------
AUTH_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <style>
    *{{margin:0;padding:0;box-sizing:border-box}}
    body{{font-family:system-ui,-apple-system,sans-serif;background:linear-gradient(135deg,#1e293b 0%,#334155 100%);min-height:100vh;display:flex;align-items:center;justify-content:center}}
    .auth-card{{background:white;border-radius:1rem;padding:3rem;width:100%;max-width:420px;box-shadow:0 25px 50px rgba(0,0,0,0.3)}}
    .logo{{text-align:center;margin-bottom:2rem}}
    .logo h1{{font-size:1.75rem;font-weight:800;color:#1e293b}}
    .logo span{{color:#3b82f6}}
    .logo p{{color:#64748b;margin-top:0.25rem;font-size:0.9rem}}
    h2{{font-size:1.25rem;font-weight:700;color:#1e293b;margin-bottom:1.5rem}}
    .form-group{{margin-bottom:1.25rem}}
    label{{display:block;font-size:0.875rem;font-weight:600;color:#374151;margin-bottom:0.5rem}}
    input{{width:100%;padding:0.75rem 1rem;border:1.5px solid #e2e8f0;border-radius:0.5rem;font-size:0.95rem;transition:border-color .2s;outline:none;font-family:inherit}}
    input:focus{{border-color:#3b82f6;box-shadow:0 0 0 3px rgba(59,130,246,0.1)}}
    .btn-primary{{width:100%;padding:0.875rem;background:#3b82f6;color:white;border:none;border-radius:0.5rem;font-size:1rem;font-weight:600;cursor:pointer;transition:background .2s;margin-top:0.5rem}}
    .btn-primary:hover{{background:#2563eb}}
    .link-row{{text-align:center;margin-top:1.5rem;color:#64748b;font-size:0.9rem}}
    .link-row a{{color:#3b82f6;font-weight:600;text-decoration:none}}
    .link-row a:hover{{text-decoration:underline}}
    .error{{background:#fef2f2;border:1px solid #fecaca;color:#dc2626;padding:0.75rem 1rem;border-radius:0.5rem;font-size:0.875rem;margin-bottom:1rem}}
    .divider{{border:none;border-top:1px solid #e2e8f0;margin:1.5rem 0}}
  </style>
</head>
<body>
  <div class="auth-card">
    <div class="logo">
      <h1>Agile<span>AI</span></h1>
      <p>Local-first AI-native project management</p>
    </div>
    {content}
  </div>
</body>
</html>"""

# ---------------------------------------------------------------------------
# App shell template (sidebar + topbar)
# ---------------------------------------------------------------------------
APP_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <script src="https://unpkg.com/htmx.org@1.9.10"></script>
  <style>
    *{{margin:0;padding:0;box-sizing:border-box}}
    :root{{
      --sidebar-w:240px;
      --topbar-h:56px;
      --c-bg:#f1f5f9;
      --c-surface:white;
      --c-border:#e2e8f0;
      --c-text:#1e293b;
      --c-muted:#64748b;
      --c-primary:#3b82f6;
      --c-primary-d:#2563eb;
      --c-success:#10b981;
      --c-warn:#f59e0b;
      --c-danger:#ef4444;
      --c-sidebar:#0f172a;
      --c-sidebar-hover:#1e293b;
      --c-sidebar-text:#94a3b8;
      --c-sidebar-active:#3b82f6;
    }}
    body{{font-family:system-ui,-apple-system,sans-serif;background:var(--c-bg);color:var(--c-text);display:flex;min-height:100vh}}

    /* Sidebar */
    .sidebar{{width:var(--sidebar-w);background:var(--c-sidebar);display:flex;flex-direction:column;position:fixed;top:0;left:0;height:100vh;z-index:100}}
    .sidebar-logo{{padding:1.25rem 1.5rem;border-bottom:1px solid #1e293b}}
    .sidebar-logo h1{{font-size:1.25rem;font-weight:800;color:white}}
    .sidebar-logo span{{color:var(--c-primary)}}
    .sidebar-logo p{{font-size:0.7rem;color:var(--c-sidebar-text);margin-top:2px}}
    .sidebar-section{{padding:1rem 0.75rem 0.5rem;font-size:0.7rem;font-weight:700;letter-spacing:.08em;color:#475569;text-transform:uppercase}}
    .sidebar-nav{{flex:1;overflow-y:auto;padding:0.5rem 0.75rem}}
    .nav-item{{display:flex;align-items:center;gap:0.75rem;padding:0.6rem 0.75rem;border-radius:0.5rem;color:var(--c-sidebar-text);text-decoration:none;font-size:0.875rem;font-weight:500;transition:all .15s;cursor:pointer;margin-bottom:2px}}
    .nav-item:hover{{background:var(--c-sidebar-hover);color:white}}
    .nav-item.active{{background:var(--c-primary);color:white}}
    .nav-item .icon{{width:18px;text-align:center;font-size:1rem;flex-shrink:0}}
    .nav-project{{padding-left:2.25rem;font-size:0.8rem;padding-top:0.4rem;padding-bottom:0.4rem}}
    .sidebar-footer{{padding:1rem;border-top:1px solid #1e293b}}
    .user-pill{{display:flex;align-items:center;gap:0.75rem}}
    .avatar{{width:32px;height:32px;background:var(--c-primary);border-radius:50%;display:flex;align-items:center;justify-content:center;color:white;font-weight:700;font-size:0.8rem;flex-shrink:0}}
    .user-info{{flex:1;min-width:0}}
    .user-name{{font-size:0.8rem;font-weight:600;color:white;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
    .user-role{{font-size:0.7rem;color:var(--c-sidebar-text)}}
    .logout-btn{{color:var(--c-sidebar-text);text-decoration:none;font-size:0.8rem;padding:0.25rem 0.5rem;border-radius:0.25rem}}
    .logout-btn:hover{{color:white}}

    /* Main area */
    .main-wrap{{margin-left:var(--sidebar-w);flex:1;display:flex;flex-direction:column;min-height:100vh}}

    /* Topbar */
    .topbar{{height:var(--topbar-h);background:var(--c-surface);border-bottom:1px solid var(--c-border);display:flex;align-items:center;padding:0 1.5rem;gap:1rem;position:sticky;top:0;z-index:50}}
    .breadcrumb{{font-size:0.875rem;color:var(--c-muted);display:flex;align-items:center;gap:0.5rem}}
    .breadcrumb a{{color:var(--c-muted);text-decoration:none}}
    .breadcrumb a:hover{{color:var(--c-primary)}}
    .breadcrumb .sep{{color:#cbd5e1}}
    .breadcrumb .current{{color:var(--c-text);font-weight:600}}
    .topbar-search{{flex:1;max-width:400px;position:relative}}
    .topbar-search input{{width:100%;padding:0.5rem 1rem 0.5rem 2.25rem;border:1.5px solid var(--c-border);border-radius:0.5rem;font-size:0.875rem;background:#f8fafc;outline:none;transition:border-color .2s}}
    .topbar-search input:focus{{border-color:var(--c-primary);background:white}}
    .search-icon{{position:absolute;left:0.75rem;top:50%;transform:translateY(-50%);color:var(--c-muted);font-size:0.9rem}}
    .topbar-actions{{margin-left:auto;display:flex;align-items:center;gap:0.75rem}}
    .icon-btn{{background:none;border:1.5px solid var(--c-border);border-radius:0.5rem;padding:0.4rem 0.6rem;cursor:pointer;color:var(--c-muted);font-size:1rem;transition:all .15s}}
    .icon-btn:hover{{border-color:var(--c-primary);color:var(--c-primary)}}

    /* Page content */
    .page{{padding:1.5rem 2rem;flex:1}}

    /* Tabs */
    .tabs{{display:flex;gap:0;border-bottom:2px solid var(--c-border);margin-bottom:1.5rem}}
    .tab{{display:flex;align-items:center;gap:0.5rem;padding:0.75rem 1.25rem;font-size:0.875rem;font-weight:500;color:var(--c-muted);text-decoration:none;border-bottom:2px solid transparent;margin-bottom:-2px;transition:all .15s;white-space:nowrap}}
    .tab:hover{{color:var(--c-text)}}
    .tab.active{{color:var(--c-primary);border-bottom-color:var(--c-primary);font-weight:600}}

    /* Toolbar */
    .toolbar{{display:flex;align-items:center;gap:0.75rem;margin-bottom:1.25rem;flex-wrap:wrap}}
    .btn{{display:inline-flex;align-items:center;gap:0.4rem;padding:0.5rem 1rem;border-radius:0.5rem;font-size:0.875rem;font-weight:500;cursor:pointer;border:none;transition:all .15s;text-decoration:none;white-space:nowrap}}
    .btn-sm{{padding:0.35rem 0.75rem;font-size:0.8rem}}
    .btn-primary{{background:var(--c-primary);color:white}}
    .btn-primary:hover{{background:var(--c-primary-d)}}
    .btn-success{{background:var(--c-success);color:white}}
    .btn-success:hover{{background:#059669}}
    .btn-ghost{{background:white;color:var(--c-text);border:1.5px solid var(--c-border)}}
    .btn-ghost:hover{{border-color:var(--c-primary);color:var(--c-primary)}}
    .btn-danger{{background:var(--c-danger);color:white}}
    .btn-danger:hover{{background:#dc2626}}
    .filter-select{{padding:0.5rem 0.75rem;border:1.5px solid var(--c-border);border-radius:0.5rem;font-size:0.875rem;background:white;color:var(--c-text);cursor:pointer;outline:none}}
    .filter-select:focus{{border-color:var(--c-primary)}}
    .search-inline{{padding:0.5rem 0.75rem;border:1.5px solid var(--c-border);border-radius:0.5rem;font-size:0.875rem;background:white;outline:none;min-width:200px}}
    .search-inline:focus{{border-color:var(--c-primary)}}
    .spacer{{flex:1}}

    /* Stats row */
    .stats-row{{display:flex;gap:1rem;margin-bottom:1.25rem;flex-wrap:wrap}}
    .stat-chip{{display:flex;align-items:center;gap:0.4rem;padding:0.35rem 0.75rem;border-radius:2rem;font-size:0.8rem;font-weight:600;background:white;border:1.5px solid var(--c-border)}}
    .stat-chip .dot{{width:8px;height:8px;border-radius:50%}}

    /* Table */
    .data-table{{width:100%;border-collapse:collapse;background:white;border-radius:0.75rem;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,0.06)}}
    .data-table th{{padding:0.75rem 1rem;text-align:left;font-size:0.75rem;font-weight:700;color:var(--c-muted);text-transform:uppercase;letter-spacing:.05em;background:#f8fafc;border-bottom:1.5px solid var(--c-border)}}
    .data-table td{{padding:0.875rem 1rem;border-bottom:1px solid #f1f5f9;font-size:0.875rem;vertical-align:middle}}
    .data-table tr:last-child td{{border-bottom:none}}
    .data-table tr:hover td{{background:#f8fafc}}
    .drag-handle{{color:#cbd5e1;cursor:move;font-size:1.1rem;user-select:none;padding:0 0.25rem}}
    .drag-handle:hover{{color:var(--c-muted)}}
    tr.dragging{{opacity:0.4;background:#eff6ff!important}}
    tr.drag-over td{{border-top:2px solid var(--c-primary)}}

    /* Badges */
    .badge{{display:inline-flex;align-items:center;gap:0.3rem;padding:0.2rem 0.6rem;border-radius:2rem;font-size:0.75rem;font-weight:600;white-space:nowrap}}
    .badge-blue{{background:#dbeafe;color:#1d4ed8}}
    .badge-green{{background:#d1fae5;color:#065f46}}
    .badge-yellow{{background:#fef3c7;color:#92400e}}
    .badge-red{{background:#fee2e2;color:#991b1b}}
    .badge-purple{{background:#ede9fe;color:#5b21b6}}
    .badge-gray{{background:#f1f5f9;color:#475569}}

    /* Priority dots */
    .prio{{display:inline-flex;align-items:center;gap:0.35rem;font-size:0.8rem;font-weight:600}}
    .prio-dot{{width:8px;height:8px;border-radius:50%;flex-shrink:0}}
    .prio-critical .prio-dot{{background:#ef4444}}
    .prio-critical{{color:#dc2626}}
    .prio-high .prio-dot{{background:#f97316}}
    .prio-high{{color:#ea580c}}
    .prio-medium .prio-dot{{background:#3b82f6}}
    .prio-medium{{color:#2563eb}}
    .prio-low .prio-dot{{background:#94a3b8}}
    .prio-low{{color:#64748b}}

    /* Issue title link */
    .issue-link{{color:var(--c-text);text-decoration:none;font-weight:500}}
    .issue-link:hover{{color:var(--c-primary);text-decoration:underline}}
    .issue-id{{font-size:0.75rem;color:var(--c-muted);font-family:monospace}}

    /* Status select */
    .status-sel{{padding:0.3rem 0.5rem;border:1.5px solid transparent;border-radius:0.375rem;font-size:0.78rem;font-weight:600;cursor:pointer;background:transparent;outline:none;transition:border-color .15s}}
    .status-sel:hover{{border-color:var(--c-border)}}
    .status-sel:focus{{border-color:var(--c-primary)}}

    /* Empty state */
    .empty-state{{text-align:center;padding:5rem 2rem;color:var(--c-muted)}}
    .empty-state .empty-icon{{font-size:3rem;margin-bottom:1rem;opacity:0.4}}
    .empty-state h3{{font-size:1.1rem;font-weight:600;color:var(--c-text);margin-bottom:0.5rem}}
    .empty-state p{{font-size:0.9rem}}

    /* Modal */
    .modal{{display:none;position:fixed;inset:0;z-index:200;background:rgba(15,23,42,0.6);backdrop-filter:blur(4px);align-items:center;justify-content:center}}
    .modal.show{{display:flex}}
    .modal-box{{background:white;border-radius:0.75rem;width:90%;max-width:520px;max-height:90vh;overflow-y:auto;box-shadow:0 25px 50px rgba(0,0,0,0.25)}}
    .modal-head{{display:flex;justify-content:space-between;align-items:center;padding:1.25rem 1.5rem;border-bottom:1px solid var(--c-border)}}
    .modal-head h3{{font-size:1rem;font-weight:700;color:var(--c-text)}}
    .modal-close{{background:none;border:none;font-size:1.5rem;cursor:pointer;color:var(--c-muted);line-height:1;padding:0 0.25rem}}
    .modal-close:hover{{color:var(--c-text)}}
    .modal-body{{padding:1.5rem}}
    .form-group{{margin-bottom:1.25rem}}
    .form-group label{{display:block;font-size:0.8rem;font-weight:600;color:var(--c-text);margin-bottom:0.4rem;text-transform:uppercase;letter-spacing:.04em}}
    .form-control{{width:100%;padding:0.625rem 0.75rem;border:1.5px solid var(--c-border);border-radius:0.5rem;font-size:0.9rem;outline:none;transition:border-color .2s;font-family:inherit}}
    .form-control:focus{{border-color:var(--c-primary);box-shadow:0 0 0 3px rgba(59,130,246,0.1)}}
    .form-row{{display:grid;grid-template-columns:1fr 1fr;gap:1rem}}
    .modal-foot{{display:flex;justify-content:flex-end;gap:0.75rem;padding:1rem 1.5rem;border-top:1px solid var(--c-border);background:#f8fafc}}

    /* Alerts */
    .alert{{padding:0.75rem 1rem;border-radius:0.5rem;font-size:0.875rem;margin-bottom:1rem;display:flex;align-items:center;gap:0.5rem}}
    .alert-success{{background:#f0fdf4;border:1px solid #bbf7d0;color:#166534}}
    .alert-error{{background:#fef2f2;border:1px solid #fecaca;color:#dc2626}}

    /* Cards (for projects) */
    .card-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:1.25rem}}
    .project-card{{background:white;border-radius:0.75rem;padding:1.5rem;border:1.5px solid var(--c-border);cursor:pointer;transition:all .15s;text-decoration:none;display:block}}
    .project-card:hover{{border-color:var(--c-primary);box-shadow:0 4px 12px rgba(59,130,246,0.12);transform:translateY(-1px)}}
    .project-card h3{{font-size:1rem;font-weight:700;color:var(--c-text);margin-bottom:0.35rem}}
    .project-card p{{font-size:0.85rem;color:var(--c-muted)}}
    .project-card .proj-meta{{margin-top:1rem;display:flex;align-items:center;gap:0.5rem}}

    /* Detail page */
    .detail-grid{{display:grid;grid-template-columns:1fr 300px;gap:1.5rem;align-items:start}}
    .detail-card{{background:white;border-radius:0.75rem;border:1.5px solid var(--c-border);overflow:hidden}}
    .detail-card-head{{padding:1rem 1.25rem;border-bottom:1px solid var(--c-border);font-size:0.75rem;font-weight:700;text-transform:uppercase;letter-spacing:.05em;color:var(--c-muted)}}
    .detail-card-body{{padding:1.25rem}}
    .meta-row{{display:flex;justify-content:space-between;align-items:center;padding:0.625rem 0;border-bottom:1px solid #f1f5f9;font-size:0.875rem}}
    .meta-row:last-child{{border-bottom:none}}
    .meta-label{{color:var(--c-muted);font-weight:500}}

    /* Sprint cards */
    .sprint-card{{background:white;border-radius:0.75rem;border:1.5px solid var(--c-border);padding:1.25rem;margin-bottom:1rem}}
    .sprint-card-head{{display:flex;justify-content:space-between;align-items:center;margin-bottom:0.75rem}}
    .progress-bar{{height:6px;background:#e2e8f0;border-radius:3px;overflow:hidden}}
    .progress-fill{{height:100%;background:var(--c-primary);border-radius:3px;transition:width .3s}}

    /* Responsive */
    @media(max-width:768px){{
      .sidebar{{transform:translateX(-100%)}}
      .main-wrap{{margin-left:0}}
    }}
  </style>
</head>
<body>
  <!-- Sidebar -->
  <aside class="sidebar">
    <div class="sidebar-logo">
      <h1>Agile<span>AI</span></h1>
      <p>AI-native project management</p>
    </div>
    <nav class="sidebar-nav">
      <div class="sidebar-section">Workspace</div>
      <a href="/projects" class="nav-item {nav_projects}">
        <span class="icon">◫</span> Projects
      </a>
      {sidebar_projects}
      <div class="sidebar-section" style="margin-top:0.75rem">Views</div>
      <a href="#" class="nav-item">
        <span class="icon">◈</span> Dashboard
      </a>
      <a href="#" class="nav-item">
        <span class="icon">◉</span> My Issues
      </a>
      <a href="/agents" class="nav-item {nav_agents}">
        <span class="icon">🤖</span> Agents
      </a>
      <a href="/models" class="nav-item {nav_models}">
        <span class="icon">⚡</span> AI Models
      </a>
      <div class="sidebar-section" style="margin-top:0.75rem">System</div>
      <a href="/admin" class="nav-item {nav_admin}">
        <span class="icon">⚙</span> Admin · All Tables
      </a>
    </nav>
    <div class="sidebar-footer">
      <div class="user-pill">
        <div class="avatar">{user_initials}</div>
        <div class="user-info">
          <div class="user-name">{user_name}</div>
          <div class="user-role">Project Member</div>
        </div>
        <a href="/logout" class="logout-btn" title="Logout">⇥</a>
      </div>
    </div>
  </aside>

  <!-- Main -->
  <div class="main-wrap">
    <!-- Topbar -->
    <header class="topbar">
      <div class="breadcrumb">{breadcrumb}</div>
      <div class="topbar-search">
        <span class="search-icon">⌕</span>
        <input type="text" placeholder="Search issues..." id="globalSearch" oninput="filterTable(this.value)">
      </div>
      <div class="topbar-actions">
        <button class="icon-btn" title="Notifications">🔔</button>
        <button class="icon-btn" title="API Docs" onclick="window.open('/docs')">⚡</button>
      </div>
    </header>

    <!-- Page -->
    <main class="page">
      {content}
    </main>
  </div>

  <!-- Modal -->
  <div id="modal" class="modal" onclick="if(event.target===this)closeModal()">
    <div class="modal-box">
      <div class="modal-head">
        <h3 id="modal-title">Form</h3>
        <button class="modal-close" onclick="closeModal()">×</button>
      </div>
      <div id="modal-content" class="modal-body"></div>
    </div>
  </div>

  <script>
    function openModal(title) {{
      document.getElementById('modal-title').textContent = title || 'Form';
      document.getElementById('modal').classList.add('show');
    }}
    function closeModal() {{
      document.getElementById('modal').classList.remove('show');
    }}
    // Auto-open modal when HTMX loads content into it
    document.body.addEventListener('htmx:afterSettle', function(e) {{
      if (e.detail.target && e.detail.target.id === 'modal-content') {{
        document.getElementById('modal').classList.add('show');
      }}
    }});
    // Table search filter
    function filterTable(q) {{
      q = q.toLowerCase();
      document.querySelectorAll('#backlog-table tr').forEach(function(row) {{
        row.style.display = !q || row.textContent.toLowerCase().includes(q) ? '' : 'none';
      }});
    }}
    // Drag & drop reorder
    let dragSrc = null;
    document.addEventListener('dragstart', function(e) {{
      const row = e.target.closest('tr[data-issue-id]');
      if (!row) return;
      dragSrc = row;
      row.classList.add('dragging');
      e.dataTransfer.effectAllowed = 'move';
    }});
    document.addEventListener('dragend', function(e) {{
      const row = e.target.closest('tr[data-issue-id]');
      if (row) row.classList.remove('dragging');
      document.querySelectorAll('tr.drag-over').forEach(r => r.classList.remove('drag-over'));
    }});
    document.addEventListener('dragover', function(e) {{
      const row = e.target.closest('tr[data-issue-id]');
      if (!row || row === dragSrc) return;
      e.preventDefault();
      document.querySelectorAll('tr.drag-over').forEach(r => r.classList.remove('drag-over'));
      row.classList.add('drag-over');
    }});
    document.addEventListener('drop', async function(e) {{
      const row = e.target.closest('tr[data-issue-id]');
      if (!row || row === dragSrc || !dragSrc) return;
      e.preventDefault();
      row.classList.remove('drag-over');
      const tbody = row.parentNode;
      tbody.insertBefore(dragSrc, row);
      const ordered = Array.from(tbody.querySelectorAll('tr[data-issue-id]')).map(r => r.dataset.issueId);
      const pid = tbody.dataset.projectId;
      if (pid) fetch('/project/' + pid + '/backlog/bulk-reorder', {{
        method:'POST', headers:{{'Content-Type':'application/json'}},
        body: JSON.stringify({{project_id: pid, ordered_ids: ordered}})
      }});
    }});
    // Status update
    function updateStatus(issueId, newStatus, projectId) {{
      fetch('/project/' + projectId + '/backlog/update-status', {{
        method:'POST', headers:{{'Content-Type':'application/json'}},
        body: JSON.stringify({{issue_id: issueId, status: newStatus}})
      }});
    }}
  </script>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
PROJECTS = [
    {"id": "proj-1", "name": "Project Alpha", "description": "Main product backlog", "issues": 0},
    {"id": "proj-2", "name": "Project Beta", "description": "Infrastructure & DevOps", "issues": 0},
    {"id": "proj-3", "name": "Project Gamma", "description": "Research & Experimentation", "issues": 0},
]

STATUS_BADGE = {
    "backlog":     ("badge-gray",   "Backlog"),
    "ready":       ("badge-blue",   "Ready"),
    "in_progress": ("badge-yellow", "In Progress"),
    "in_review":   ("badge-purple", "In Review"),
    "blocked":     ("badge-red",    "Blocked"),
    "done":        ("badge-green",  "Done"),
    "cancelled":   ("badge-gray",   "Cancelled"),
}

STATUS_DOT = {
    "backlog": "#94a3b8", "ready": "#3b82f6", "in_progress": "#f59e0b",
    "in_review": "#8b5cf6", "blocked": "#ef4444", "done": "#10b981", "cancelled": "#94a3b8",
}

TYPE_BADGE = {
    "story": "badge-blue", "task": "badge-gray", "bug": "badge-red",
    "feature": "badge-purple", "spike": "badge-yellow", "epic": "badge-green",
}


def status_badge(s: str) -> str:
    cls, label = STATUS_BADGE.get(s, ("badge-gray", s.replace("_", " ").title()))
    dot = STATUS_DOT.get(s, "#94a3b8")
    return f'<span class="badge {cls}"><span style="width:6px;height:6px;border-radius:50%;background:{dot};display:inline-block"></span>{label}</span>'


def type_badge(t: str) -> str:
    cls = TYPE_BADGE.get(t, "badge-gray")
    return f'<span class="badge {cls}">{t.title()}</span>'


def priority_html(p: str) -> str:
    return f'<span class="prio prio-{p}"><span class="prio-dot"></span>{p.title()}</span>'


def render_app(title: str, content: str, project_id: str = "", active_tab: str = "",
               breadcrumb: str = "", user_name: str = "User") -> str:
    initials = "".join(w[0].upper() for w in user_name.split()[:2]) or "U"

    sidebar_projects = ""
    nav_projects = "active" if not project_id and active_tab not in ("admin", "agents", "models") else ""
    nav_admin = "active" if active_tab == "admin" else ""
    nav_agents = "active" if active_tab == "agents" else ""
    nav_models = "active" if active_tab == "models" else ""
    for p in PROJECTS:
        active = "active" if p["id"] == project_id else ""
        sidebar_projects += f'<a href="/project/{p["id"]}/backlog" class="nav-item nav-project {active}">{p["name"]}</a>\n'

    if not breadcrumb:
        if project_id:
            proj_name = next((p["name"] for p in PROJECTS if p["id"] == project_id), project_id)
            breadcrumb = f'<a href="/projects">Projects</a><span class="sep">›</span><a href="/project/{project_id}/backlog">{proj_name}</a>'
            if active_tab and active_tab != "backlog":
                breadcrumb += f'<span class="sep">›</span><span class="current">{active_tab.title()}</span>'
        else:
            breadcrumb = '<span class="current">Projects</span>'

    return APP_HTML.format(
        title=title,
        content=content,
        sidebar_projects=sidebar_projects,
        nav_projects=nav_projects,
        nav_admin=nav_admin,
        nav_agents=nav_agents,
        nav_models=nav_models,
        breadcrumb=breadcrumb,
        user_initials=initials,
        user_name=user_name,
    )


def project_tabs(project_id: str, active: str) -> str:
    tabs = [
        ("backlog", "📋 Backlog", f"/project/{project_id}/backlog"),
        ("prioritized", "📊 Prioritized", f"/project/{project_id}/prioritized"),
        ("sprints", "🏃 Sprints", f"/project/{project_id}/sprints"),
        ("settings", "⚙️ Settings", f"/project/{project_id}/settings"),
    ]
    html = '<div class="tabs">'
    for tid, label, href in tabs:
        cls = "tab active" if tid == active else "tab"
        html += f'<a href="{href}" class="{cls}">{label}</a>'
    html += '</div>'
    return html


def status_select(issue_id: str, current: str, project_id: str) -> str:
    opts = [
        ("backlog", "Backlog"), ("ready", "Ready"), ("in_progress", "In Progress"),
        ("in_review", "In Review"), ("blocked", "Blocked"), ("done", "Done"),
    ]
    color = STATUS_DOT.get(current, "#94a3b8")
    html = f'<select class="status-sel" style="color:{color}" onchange="updateStatus(\'{issue_id}\',this.value,\'{project_id}\');this.style.color=\'{{\'#94a3b8\':\'#94a3b8\',\'#3b82f6\':\'#3b82f6\',\'#f59e0b\':\'#f59e0b\',\'#8b5cf6\':\'#8b5cf6\',\'#ef4444\':\'#ef4444\',\'#10b981\':\'#10b981\'}}[this.value]||\'#94a3b8\'">'
    # Simpler version without color update:
    html = f'<select class="status-sel" onchange="updateStatus(\'{issue_id}\',this.value,\'{project_id}\')">'
    for val, label in opts:
        sel = "selected" if val == current else ""
        html += f'<option value="{val}" {sel}>{label}</option>'
    html += '</select>'
    return html


def get_user_from_cookie(request: Request) -> str:
    """Extract user ID from JWT cookie."""
    from jose import jwt, JWTError
    token = request.cookies.get("auth_token", "")
    if not token:
        return ""
    try:
        payload = jwt.decode(token, "your-secret-key-change-in-production", algorithms=["HS256"])
        return payload.get("sub", "")
    except JWTError:
        return ""


# ---------------------------------------------------------------------------
# Auth routes
# ---------------------------------------------------------------------------
@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    if request.cookies.get("auth_token"):
        return RedirectResponse(url="/projects", status_code=302)
    return RedirectResponse(url="/login", status_code=302)


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    content = """
    <h2>Sign in to your account</h2>
    <form method="post" action="/login">
      <div class="form-group">
        <label>Email address</label>
        <input type="email" name="email" placeholder="you@example.com" required>
      </div>
      <div class="form-group">
        <label>Password</label>
        <input type="password" name="password" placeholder="••••••••" required>
      </div>
      <button type="submit" class="btn-primary">Sign in →</button>
    </form>
    <hr class="divider">
    <div class="link-row">Don't have an account? <a href="/register">Create one</a></div>
    """
    return HTMLResponse(AUTH_HTML.format(title="Sign In - AgileAI", content=content))


@router.post("/login", response_class=HTMLResponse)
async def login_form(
    request: Request,
    email: str = Form(None),
    password: str = Form(None),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import select

    def _login_page(error=""):
        err_html = f'<div class="error">{error}</div>' if error else ""
        content = f"""
        <h2>Sign in to your account</h2>
        {err_html}
        <form method="post" action="/login">
          <div class="form-group">
            <label>Email address</label>
            <input type="email" name="email" value="{email or ''}" placeholder="you@example.com" required>
          </div>
          <div class="form-group">
            <label>Password</label>
            <input type="password" name="password" placeholder="••••••••" required>
          </div>
          <button type="submit" class="btn-primary">Sign in →</button>
        </form>
        <hr class="divider">
        <div class="link-row">Don't have an account? <a href="/register">Create one</a></div>
        """
        return HTMLResponse(AUTH_HTML.format(title="Sign In - AgileAI", content=content), status_code=400)

    if not email or not password:
        return _login_page("Email and password are required.")

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(password, user.password_hash):
        return _login_page("Invalid email or password.")

    token = create_access_token(user_id=user.id)
    resp = RedirectResponse(url="/projects", status_code=302)
    resp.set_cookie("auth_token", token, httponly=True, max_age=86400)
    return resp


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    content = """
    <h2>Create your account</h2>
    <form method="post" action="/register">
      <div class="form-group">
        <label>Full name</label>
        <input type="text" name="name" placeholder="Jane Smith" required>
      </div>
      <div class="form-group">
        <label>Email address</label>
        <input type="email" name="email" placeholder="you@example.com" required>
      </div>
      <div class="form-group">
        <label>Password</label>
        <input type="password" name="password" placeholder="••••••••" required>
      </div>
      <button type="submit" class="btn-primary">Create account →</button>
    </form>
    <hr class="divider">
    <div class="link-row">Already have an account? <a href="/login">Sign in</a></div>
    """
    return HTMLResponse(AUTH_HTML.format(title="Register - AgileAI", content=content))


@router.post("/register", response_class=HTMLResponse)
async def register_form(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    name: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import select

    def _reg_page(error=""):
        err_html = f'<div class="error">{error}</div>' if error else ""
        content = f"""
        <h2>Create your account</h2>
        {err_html}
        <form method="post" action="/register">
          <div class="form-group">
            <label>Full name</label>
            <input type="text" name="name" value="{name}" placeholder="Jane Smith" required>
          </div>
          <div class="form-group">
            <label>Email address</label>
            <input type="email" name="email" value="{email}" placeholder="you@example.com" required>
          </div>
          <div class="form-group">
            <label>Password</label>
            <input type="password" name="password" placeholder="••••••••" required>
          </div>
          <button type="submit" class="btn-primary">Create account →</button>
        </form>
        <hr class="divider">
        <div class="link-row">Already have an account? <a href="/login">Sign in</a></div>
        """
        return HTMLResponse(AUTH_HTML.format(title="Register - AgileAI", content=content), status_code=400)

    result = await db.execute(select(User).where(User.email == email))
    if result.scalar_one_or_none():
        return _reg_page("That email is already registered.")

    username = email.split("@")[0]
    # Make username unique if taken
    result2 = await db.execute(select(User).where(User.username == username))
    if result2.scalar_one_or_none():
        username = username + "_" + str(abs(hash(email)) % 1000)

    user = User(email=email, username=username, password_hash=hash_password(password), name=name)
    db.add(user)
    await db.commit()
    await db.refresh(user)

    token = create_access_token(user_id=user.id)
    resp = RedirectResponse(url="/projects", status_code=302)
    resp.set_cookie("auth_token", token, httponly=True, max_age=86400)
    return resp


@router.get("/logout")
async def logout():
    resp = RedirectResponse(url="/login", status_code=302)
    resp.delete_cookie("auth_token")
    return resp


# ---------------------------------------------------------------------------
# Projects page
# ---------------------------------------------------------------------------
@router.get("/projects", response_class=HTMLResponse)
async def projects_page(request: Request, db: AsyncSession = Depends(get_db)):
    if not request.cookies.get("auth_token"):
        return RedirectResponse(url="/login", status_code=302)

    from sqlalchemy import select, func

    cards = ""
    for proj in PROJECTS:
        # Count issues for this project
        try:
            result = await db.execute(
                select(func.count()).select_from(Issue).where(Issue.project_id == proj["id"])
            )
            count = result.scalar() or 0
        except Exception:
            count = 0

        cards += f"""
        <a href="/project/{proj['id']}/backlog" class="project-card">
          <h3>{proj['name']}</h3>
          <p>{proj['description']}</p>
          <div class="proj-meta">
            <span class="badge badge-gray">{count} issues</span>
            <span class="badge badge-blue">Active</span>
          </div>
        </a>"""

    content = f"""
    <div style="margin-bottom:1.5rem;display:flex;justify-content:space-between;align-items:center">
      <div>
        <h2 style="font-size:1.35rem;font-weight:700">Projects</h2>
        <p style="color:var(--c-muted);font-size:0.875rem;margin-top:0.25rem">Select a project to manage its backlog</p>
      </div>
    </div>
    <div class="card-grid">{cards}</div>"""

    return HTMLResponse(render_app("Projects - AgileAI", content, user_name="Demo User"))


# ---------------------------------------------------------------------------
# Project redirect
# ---------------------------------------------------------------------------
@router.get("/project/{project_id}")
async def project_index(project_id: str):
    return RedirectResponse(url=f"/project/{project_id}/backlog", status_code=302)


# ---------------------------------------------------------------------------
# Backlog tab
# ---------------------------------------------------------------------------
@router.get("/project/{project_id}/backlog", response_class=HTMLResponse)
@router.get("/backlog/{project_id}", response_class=HTMLResponse)
async def backlog_view(project_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    if not request.cookies.get("auth_token"):
        return RedirectResponse(url="/login", status_code=302)

    from agileai.services.backlog import BacklogService
    svc = BacklogService(db)
    try:
        issues = await svc.get_backlog(project_id, include_scores=False)
    except Exception:
        issues = []

    proj_name = next((p["name"] for p in PROJECTS if p["id"] == project_id), project_id)

    # Count by status for stat chips
    counts = {}
    for iss in issues:
        s = getattr(iss, "status", "backlog")
        counts[s] = counts.get(s, 0) + 1

    stat_chips = ""
    for s, label in [("backlog","Backlog"),("in_progress","In Progress"),("done","Done")]:
        n = counts.get(s, 0)
        dot = STATUS_DOT.get(s, "#94a3b8")
        stat_chips += f'<div class="stat-chip"><span class="dot" style="background:{dot}"></span>{label}: <strong>{n}</strong></div>'

    rows = ""
    if issues:
        for iss in issues:
            iid = getattr(iss, "id", "")
            title = getattr(iss, "title", "Untitled")
            s = getattr(iss, "status", "backlog")
            itype = getattr(iss, "issue_type", getattr(iss, "type", "task"))
            prio = getattr(iss, "priority", "medium")
            pts = getattr(iss, "story_points", None)
            pts_html = f'<strong>{pts}</strong>' if pts else '<span style="color:#cbd5e1">—</span>'
            sprint = getattr(iss, "sprint_id", None)
            sprint_btn = "" if sprint else f'<button class="btn btn-ghost btn-sm" hx-get="/project/{project_id}/backlog/sprint-select?issue_id={iid}" hx-target="#modal-content" onclick="openModal(\'Add to Sprint\')">+ Sprint</button>'

            rows += f"""
            <tr draggable="true" data-issue-id="{iid}">
              <td><span class="drag-handle">⠿</span></td>
              <td><span class="issue-id">{iid}</span></td>
              <td><a href="/project/{project_id}/issue/{iid}" class="issue-link">{title}</a></td>
              <td>{status_select(iid, s, project_id)}</td>
              <td>{type_badge(itype)}</td>
              <td>{priority_html(prio)}</td>
              <td style="text-align:center">{pts_html}</td>
              <td>
                <div style="display:flex;gap:0.4rem;align-items:center">
                  <button class="btn btn-ghost btn-sm" hx-get="/project/{project_id}/backlog/estimate?issue_id={iid}" hx-target="#modal-content" onclick="openModal('Estimate Issue')">Est</button>
                  {sprint_btn}
                </div>
              </td>
            </tr>"""
    else:
        rows = f"""<tr><td colspan="8">
          <div class="empty-state">
            <div class="empty-icon">📋</div>
            <h3>No issues yet</h3>
            <p>Create your first issue to get started</p>
          </div>
        </td></tr>"""

    content = f"""
    {project_tabs(project_id, "backlog")}
    <div class="toolbar">
      <button class="btn btn-success" hx-get="/project/{project_id}/backlog/create-issue" hx-target="#modal-content" onclick="openModal('New Issue')">＋ New Issue</button>
      <select class="filter-select" onchange="filterStatus(this.value)">
        <option value="">All Statuses</option>
        <option value="backlog">Backlog</option>
        <option value="ready">Ready</option>
        <option value="in_progress">In Progress</option>
        <option value="in_review">In Review</option>
        <option value="done">Done</option>
      </select>
      <select class="filter-select" onchange="filterType(this.value)">
        <option value="">All Types</option>
        <option value="story">Story</option>
        <option value="task">Task</option>
        <option value="bug">Bug</option>
        <option value="feature">Feature</option>
      </select>
      <div class="spacer"></div>
      <span style="font-size:0.8rem;color:var(--c-muted)">{len(issues)} issues</span>
    </div>
    <div class="stats-row">{stat_chips}</div>
    <table class="data-table">
      <thead>
        <tr>
          <th style="width:36px"></th>
          <th style="width:100px">ID</th>
          <th>Title</th>
          <th style="width:140px">Status</th>
          <th style="width:90px">Type</th>
          <th style="width:100px">Priority</th>
          <th style="width:70px;text-align:center">Pts</th>
          <th style="width:160px">Actions</th>
        </tr>
      </thead>
      <tbody id="backlog-table" data-project-id="{project_id}">{rows}</tbody>
    </table>
    <script>
      function filterStatus(v) {{
        document.querySelectorAll('#backlog-table tr[data-issue-id]').forEach(function(row) {{
          const sel = row.querySelector('select');
          row.style.display = !v || (sel && sel.value === v) ? '' : 'none';
        }});
      }}
      function filterType(v) {{
        document.querySelectorAll('#backlog-table tr[data-issue-id]').forEach(function(row) {{
          const badge = row.querySelector('td:nth-child(5) .badge');
          row.style.display = !v || (badge && badge.textContent.toLowerCase() === v) ? '' : 'none';
        }});
      }}
    </script>"""

    return HTMLResponse(render_app(f"{proj_name} · Backlog", content, project_id, "backlog", user_name="Demo User"))


# ---------------------------------------------------------------------------
# Backlog sub-routes (estimate, sprint, reorder)
# ---------------------------------------------------------------------------
@router.get("/project/{project_id}/backlog/estimate", response_class=HTMLResponse)
@router.get("/backlog/{project_id}/estimate", response_class=HTMLResponse)
async def estimate_form(project_id: str, issue_id: str, request: Request):
    return HTMLResponse(f"""
    <form hx-post="/project/{project_id}/backlog/estimate" hx-target="#modal-content">
      <input type="hidden" name="issue_id" value="{issue_id}">
      <div class="form-group">
        <label>Story Points</label>
        <select name="story_points" class="form-control" required>
          <option value="">Select…</option>
          {"".join(f'<option value="{n}">{n} pt{"s" if n>1 else ""} — {d}</option>' for n,d in [(1,"Trivial"),(2,"Very small"),(3,"Small"),(5,"Medium"),(8,"Large"),(13,"Very large"),(21,"Huge")])}
        </select>
      </div>
      <div class="form-group">
        <label>Rationale</label>
        <textarea name="rationale" class="form-control" rows="3" placeholder="Why this estimate?"></textarea>
      </div>
      <div class="modal-foot">
        <button type="button" class="btn btn-ghost" onclick="closeModal()">Cancel</button>
        <button type="submit" class="btn btn-primary">Save Estimate</button>
      </div>
    </form>""")


@router.post("/project/{project_id}/backlog/estimate", response_class=HTMLResponse)
@router.post("/backlog/{project_id}/estimate", response_class=HTMLResponse)
async def save_estimate(
    project_id: str, issue_id: str = Form(...), story_points: int = Form(...),
    rationale: str = Form(default=""), request: Request = None, db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import update
    try:
        await db.execute(update(Issue).where(Issue.id == issue_id).values(story_points=story_points))
        await db.commit()
        return HTMLResponse(f'<div class="alert alert-success">✓ Set to <strong>{story_points} pts</strong>. <a href="/project/{project_id}/backlog" style="color:inherit;font-weight:600">Reload</a> to see updated table.</div>')
    except Exception as e:
        return HTMLResponse(f'<div class="alert alert-error">✗ {e}</div>', status_code=400)


@router.get("/project/{project_id}/backlog/create-issue", response_class=HTMLResponse)
async def create_issue_form(project_id: str, request: Request):
    return HTMLResponse(f"""
    <form hx-post="/project/{project_id}/backlog/create-issue" hx-target="#modal-content">
      <div class="form-group">
        <label>Title</label>
        <input type="text" name="title" class="form-control" placeholder="Short descriptive title" required autofocus>
      </div>
      <div class="form-group">
        <label>Description</label>
        <textarea name="description" class="form-control" rows="3" placeholder="Context, acceptance criteria…"></textarea>
      </div>
      <div class="form-row">
        <div class="form-group">
          <label>Type</label>
          <select name="issue_type" class="form-control">
            <option value="task">Task</option>
            <option value="story">Story</option>
            <option value="bug">Bug</option>
            <option value="feature">Feature</option>
            <option value="spike">Spike</option>
          </select>
        </div>
        <div class="form-group">
          <label>Priority</label>
          <select name="priority" class="form-control">
            <option value="low">Low</option>
            <option value="medium" selected>Medium</option>
            <option value="high">High</option>
            <option value="critical">Critical</option>
          </select>
        </div>
      </div>
      <div class="modal-foot">
        <button type="button" class="btn btn-ghost" onclick="closeModal()">Cancel</button>
        <button type="submit" class="btn btn-primary">Create Issue</button>
      </div>
    </form>""")


@router.post("/project/{project_id}/backlog/create-issue", response_class=HTMLResponse)
async def save_new_issue(
    project_id: str, title: str = Form(...), description: str = Form(default=""),
    issue_type: str = Form(default="task"), priority: str = Form(default="medium"),
    request: Request = None, db: AsyncSession = Depends(get_db),
):
    try:
        import uuid
        issue_id = f"{project_id.upper()}-{abs(hash(title + str(uuid.uuid4()))) % 9000 + 1000}"
        new_issue = Issue(id=issue_id, project_id=project_id, title=title,
                          description=description, issue_type=issue_type, priority=priority, status="backlog")
        db.add(new_issue)
        await db.commit()
        return HTMLResponse(f'<div class="alert alert-success">✓ Issue <strong>{issue_id}</strong> created. <a href="/project/{project_id}/backlog" style="color:inherit;font-weight:600">View backlog</a></div>')
    except Exception as e:
        return HTMLResponse(f'<div class="alert alert-error">✗ {e}</div>', status_code=400)


@router.get("/project/{project_id}/backlog/sprint-select", response_class=HTMLResponse)
@router.get("/backlog/{project_id}/sprint-select", response_class=HTMLResponse)
async def sprint_select_form(project_id: str, issue_id: str, request: Request):
    return HTMLResponse(f"""
    <form hx-post="/project/{project_id}/backlog/add-to-sprint" hx-target="#modal-content">
      <input type="hidden" name="issue_id" value="{issue_id}">
      <div class="form-group">
        <label>Sprint</label>
        <select name="sprint_id" class="form-control" required>
          <option value="">Select sprint…</option>
          <option value="sprint-1">Sprint 1 (Active)</option>
          <option value="sprint-2">Sprint 2 (Planned)</option>
          <option value="sprint-3">Sprint 3 (Planned)</option>
        </select>
      </div>
      <div class="modal-foot">
        <button type="button" class="btn btn-ghost" onclick="closeModal()">Cancel</button>
        <button type="submit" class="btn btn-primary">Add to Sprint</button>
      </div>
    </form>""")


@router.post("/project/{project_id}/backlog/add-to-sprint", response_class=HTMLResponse)
@router.post("/backlog/{project_id}/add-to-sprint", response_class=HTMLResponse)
async def add_to_sprint(
    project_id: str, issue_id: str = Form(...), sprint_id: str = Form(...),
    request: Request = None, db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import update
    try:
        await db.execute(update(Issue).where(Issue.id == issue_id).values(sprint_id=sprint_id))
        await db.commit()
        return HTMLResponse(f'<div class="alert alert-success">✓ Added to <strong>{sprint_id}</strong>. <a href="/project/{project_id}/backlog" style="color:inherit;font-weight:600">Reload</a></div>')
    except Exception as e:
        return HTMLResponse(f'<div class="alert alert-error">✗ {e}</div>', status_code=400)


@router.post("/project/{project_id}/backlog/bulk-reorder")
@router.post("/backlog/{project_id}/bulk-reorder")
async def bulk_reorder(project_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import update
    try:
        body = await request.json()
        for order, iid in enumerate(body.get("ordered_ids", [])):
            await db.execute(update(Issue).where(Issue.id == iid).values(backlog_order=order))
        await db.commit()
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}


@router.post("/project/{project_id}/backlog/update-status")
async def update_status(project_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import update
    try:
        body = await request.json()
        await db.execute(update(Issue).where(Issue.id == body["issue_id"]).values(status=body["status"]))
        await db.commit()
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}


# ---------------------------------------------------------------------------
# Prioritized tab
# ---------------------------------------------------------------------------
@router.get("/project/{project_id}/prioritized", response_class=HTMLResponse)
@router.get("/backlog/{project_id}/prioritize", response_class=HTMLResponse)
async def prioritize_view(project_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    if not request.cookies.get("auth_token"):
        return RedirectResponse(url="/login", status_code=302)

    from agileai.services.backlog import BacklogService
    svc = BacklogService(db)
    try:
        ranked = await svc.prioritize_backlog(project_id)
    except Exception:
        ranked = []

    proj_name = next((p["name"] for p in PROJECTS if p["id"] == project_id), project_id)

    rows = ""
    if ranked:
        for i, iss in enumerate(ranked, 1):
            score_obj = getattr(iss, "_priority_score", None)
            score = f"{score_obj.score:.1f}" if score_obj else "—"
            title = getattr(iss, "title", "Untitled")
            iid = getattr(iss, "id", "")
            prio = getattr(iss, "priority", "medium")
            s = getattr(iss, "status", "backlog")
            bar_w = min(100, float(score_obj.score if score_obj else 0))
            rows += f"""
            <tr>
              <td><strong style="font-size:1.1rem;color:var(--c-muted)">#{i}</strong></td>
              <td><span class="issue-id">{iid}</span></td>
              <td><a href="/project/{project_id}/issue/{iid}" class="issue-link">{title}</a></td>
              <td>{status_badge(s)}</td>
              <td>{priority_html(prio)}</td>
              <td>
                <div style="display:flex;align-items:center;gap:0.75rem">
                  <div class="progress-bar" style="width:80px"><div class="progress-fill" style="width:{bar_w}%"></div></div>
                  <span style="font-size:0.8rem;font-weight:600;color:var(--c-primary)">{score}</span>
                </div>
              </td>
            </tr>"""
    else:
        rows = '<tr><td colspan="6"><div class="empty-state"><div class="empty-icon">📊</div><h3>No ranked issues</h3><p>Add issues to your backlog first</p></div></td></tr>'

    content = f"""
    {project_tabs(project_id, "prioritized")}
    <table class="data-table">
      <thead>
        <tr>
          <th style="width:50px">Rank</th>
          <th style="width:110px">ID</th>
          <th>Title</th>
          <th style="width:130px">Status</th>
          <th style="width:100px">Priority</th>
          <th style="width:160px">Score</th>
        </tr>
      </thead>
      <tbody>{rows}</tbody>
    </table>"""

    return HTMLResponse(render_app(f"{proj_name} · Prioritized", content, project_id, "prioritized", user_name="Demo User"))


# ---------------------------------------------------------------------------
# Sprints tab — real DB-backed
# ---------------------------------------------------------------------------
_SPRINT_STATUS_COLORS = {
    "planned": ("#3b82f6", "#dbeafe", "Planned"),
    "active":  ("#10b981", "#d1fae5", "Active"),
    "completed": ("#94a3b8", "#f1f5f9", "Completed"),
    "cancelled": ("#ef4444", "#fee2e2", "Cancelled"),
}


@router.get("/project/{project_id}/sprints", response_class=HTMLResponse)
async def sprints_view(project_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    if not request.cookies.get("auth_token"):
        return RedirectResponse(url="/login", status_code=302)

    user_name = get_user_from_cookie(request) or "User"
    proj_name = next((p["name"] for p in PROJECTS if p["id"] == project_id), project_id)

    from sqlalchemy import select, func as sqlfunc
    sprints = []
    try:
        res = await db.execute(
            select(Sprint).where(Sprint.project_id == project_id).order_by(Sprint.created_at.desc())
        )
        sprints = list(res.scalars().all())
    except Exception:
        pass

    cards = ""
    for sp in sprints:
        st = sp.status or "planned"
        col, bg, lbl = _SPRINT_STATUS_COLORS.get(st, ("#94a3b8", "#f1f5f9", st.title()))

        # Count issues in sprint
        total = done = 0
        try:
            r = await db.execute(
                select(sqlfunc.count(Issue.id)).where(Issue.sprint_id == sp.id)
            )
            total = r.scalar() or 0
            r2 = await db.execute(
                select(sqlfunc.count(Issue.id)).where(
                    Issue.sprint_id == sp.id, Issue.status == "done"
                )
            )
            done = r2.scalar() or 0
        except Exception:
            pass

        pct = int(done / total * 100) if total else 0
        goal_text = sp.goal or "No goal set"
        dates = ""
        if sp.start_date or sp.end_date:
            dates = f'<span style="font-size:0.75rem;color:var(--c-muted)">{sp.start_date or "?"} → {sp.end_date or "?"}</span>'

        actions = ""
        if st == "planned":
            actions = f'<form method="post" action="/project/{project_id}/sprints/{sp.id}/start" style="display:inline"><button class="btn btn-success btn-sm" type="submit">▶ Start</button></form>'
        elif st == "active":
            actions = f'<form method="post" action="/project/{project_id}/sprints/{sp.id}/complete" style="display:inline"><button class="btn btn-ghost btn-sm" type="submit">✓ Complete</button></form>'

        cards += f"""
        <div class="sprint-card">
          <div class="sprint-card-head">
            <div style="flex:1;min-width:0">
              <div style="display:flex;align-items:center;gap:0.75rem;flex-wrap:wrap;margin-bottom:0.25rem">
                <a href="/project/{project_id}/sprints/{sp.id}" style="font-size:1rem;font-weight:700;color:var(--c-text);text-decoration:none">{sp.name or sp.id}</a>
                <span class="badge" style="background:{bg};color:{col}">{lbl}</span>
                {dates}
              </div>
              <p style="font-size:0.8rem;color:var(--c-muted)">{goal_text}</p>
            </div>
            <div style="display:flex;gap:0.5rem;align-items:center;flex-shrink:0">
              {actions}
              <a href="/project/{project_id}/sprints/{sp.id}" class="btn btn-ghost btn-sm">Details →</a>
            </div>
          </div>
          <div style="display:flex;align-items:center;gap:1rem;margin-top:0.75rem">
            <div class="progress-bar" style="flex:1"><div class="progress-fill" style="width:{pct}%;background:{col}"></div></div>
            <span style="font-size:0.8rem;font-weight:600;color:{col}">{done}/{total} done · {pct}%</span>
          </div>
        </div>"""

    if not sprints:
        cards = """
        <div class="empty-state">
          <div class="empty-icon">🏃</div>
          <h3>No sprints yet</h3>
          <p>Create your first sprint to start planning.</p>
        </div>"""

    create_modal = f"""
    <div id="sprint-modal" class="modal" onclick="if(event.target===this)document.getElementById('sprint-modal').classList.remove('show')">
      <div class="modal-box">
        <div class="modal-head">
          <h3>Create Sprint</h3>
          <button class="modal-close" onclick="document.getElementById('sprint-modal').classList.remove('show')">×</button>
        </div>
        <form method="post" action="/project/{project_id}/sprints/create">
          <div class="modal-body">
            <div class="form-group">
              <label>Sprint Name <span style="color:#ef4444">*</span></label>
              <input type="text" name="name" class="form-control" placeholder="Sprint 1" required>
            </div>
            <div class="form-group">
              <label>Goal</label>
              <textarea name="goal" class="form-control" rows="2" placeholder="What will the team achieve?"></textarea>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>Start Date</label>
                <input type="date" name="start_date" class="form-control">
              </div>
              <div class="form-group">
                <label>End Date</label>
                <input type="date" name="end_date" class="form-control">
              </div>
            </div>
          </div>
          <div class="modal-foot">
            <button type="button" class="btn btn-ghost" onclick="document.getElementById('sprint-modal').classList.remove('show')">Cancel</button>
            <button type="submit" class="btn btn-primary">Create Sprint</button>
          </div>
        </form>
      </div>
    </div>"""

    content = f"""
    {project_tabs(project_id, "sprints")}
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:1.25rem">
      <div>
        <h2 style="font-size:1.15rem;font-weight:700">Sprints</h2>
        <p style="color:var(--c-muted);font-size:0.85rem">{len(sprints)} sprint{'s' if len(sprints) != 1 else ''}</p>
      </div>
      <button class="btn btn-primary" onclick="document.getElementById('sprint-modal').classList.add('show')">+ New Sprint</button>
    </div>
    <div style="max-width:760px">{cards}</div>
    {create_modal}"""

    return HTMLResponse(render_app(f"{proj_name} · Sprints", content, project_id, "sprints", user_name=user_name))


@router.post("/project/{project_id}/sprints/create")
async def sprint_create(
    project_id: str, request: Request,
    name: str = Form(...),
    goal: str = Form(""),
    start_date: str = Form(""),
    end_date: str = Form(""),
    db: AsyncSession = Depends(get_db),
):
    if not request.cookies.get("auth_token"):
        return RedirectResponse(url="/login", status_code=302)
    sp = Sprint(
        project_id=project_id,
        name=name,
        goal=goal or None,
        start_date=start_date or None,
        end_date=end_date or None,
        status="planned",
    )
    db.add(sp)
    try:
        await db.commit()
    except Exception:
        await db.rollback()
    return RedirectResponse(url=f"/project/{project_id}/sprints", status_code=303)


@router.post("/project/{project_id}/sprints/{sprint_id}/start")
async def sprint_start(project_id: str, sprint_id: str, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select, update
    await db.execute(update(Sprint).where(Sprint.id == sprint_id).values(status="active"))
    await db.commit()
    return RedirectResponse(url=f"/project/{project_id}/sprints", status_code=303)


@router.post("/project/{project_id}/sprints/{sprint_id}/complete")
async def sprint_complete(project_id: str, sprint_id: str, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import update
    await db.execute(update(Sprint).where(Sprint.id == sprint_id).values(status="completed"))
    await db.commit()
    return RedirectResponse(url=f"/project/{project_id}/sprints", status_code=303)


@router.get("/project/{project_id}/sprints/{sprint_id}", response_class=HTMLResponse)
async def sprint_detail(project_id: str, sprint_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    if not request.cookies.get("auth_token"):
        return RedirectResponse(url="/login", status_code=302)

    user_name = get_user_from_cookie(request) or "User"
    proj_name = next((p["name"] for p in PROJECTS if p["id"] == project_id), project_id)

    from sqlalchemy import select, func as sqlfunc
    sp = None
    try:
        res = await db.execute(select(Sprint).where(Sprint.id == sprint_id))
        sp = res.scalar_one_or_none()
    except Exception:
        pass

    if not sp:
        content = '<div class="alert alert-error">Sprint not found.</div>'
        return HTMLResponse(render_app("Sprint Not Found", content, project_id, user_name=user_name), status_code=404)

    # Issues in this sprint
    issues = []
    try:
        res = await db.execute(select(Issue).where(Issue.sprint_id == sprint_id))
        issues = list(res.scalars().all())
    except Exception:
        pass

    # Ceremonies
    ceremonies = []
    try:
        res = await db.execute(select(Ceremony).where(Ceremony.sprint_id == sprint_id).order_by(Ceremony.scheduled_at))
        ceremonies = list(res.scalars().all())
    except Exception:
        pass

    # Sprint goals
    goals = []
    try:
        res = await db.execute(select(SprintGoal).where(SprintGoal.sprint_id == sprint_id).order_by(SprintGoal.order_index))
        goals = list(res.scalars().all())
    except Exception:
        pass

    total = len(issues)
    done = sum(1 for i in issues if getattr(i, "status", "") == "done")
    pct = int(done / total * 100) if total else 0
    st = sp.status or "planned"
    col, bg, lbl = _SPRINT_STATUS_COLORS.get(st, ("#94a3b8", "#f1f5f9", st.title()))

    # Build issue rows
    issue_rows = ""
    for iss in issues:
        issue_rows += f"""<tr>
          <td><a href="/project/{project_id}/issue/{iss.id}" class="issue-link">{getattr(iss,'title','Untitled')}</a></td>
          <td>{status_badge(getattr(iss,'status','backlog'))}</td>
          <td>{type_badge(getattr(iss,'issue_type','task'))}</td>
          <td>{priority_html(getattr(iss,'priority','medium'))}</td>
          <td>{getattr(iss,'story_points','—') or '—'}</td>
        </tr>"""

    issues_section = f"""
    <table class="data-table">
      <thead><tr><th>Title</th><th>Status</th><th>Type</th><th>Priority</th><th>Points</th></tr></thead>
      <tbody>{issue_rows or '<tr><td colspan="5" class="empty-state" style="padding:2rem">No issues in this sprint yet. Assign issues from the <a href="/project/'+project_id+'/backlog">backlog</a>.</td></tr>'}</tbody>
    </table>"""

    # Ceremonies section
    cer_rows = ""
    cer_types = {"planning": "📋", "review": "📊", "retro": "🔍", "standup": "☀️"}
    for c in ceremonies:
        ct = c.ceremony_type or "standup"
        icon = cer_types.get(ct, "📌")
        done_badge = '<span class="badge badge-green">Done</span>' if c.is_completed else '<span class="badge badge-yellow">Upcoming</span>'
        cer_rows += f"<tr><td>{icon} {ct.title()}</td><td>{c.scheduled_at or '—'}</td><td>{c.duration_minutes or '—'} min</td><td>{done_badge}</td><td>{c.notes or ''}</td></tr>"

    ceremony_section = f"""
    <table class="data-table">
      <thead><tr><th>Type</th><th>Scheduled</th><th>Duration</th><th>Status</th><th>Notes</th></tr></thead>
      <tbody>{cer_rows or '<tr><td colspan="5" class="empty-state" style="padding:2rem">No ceremonies scheduled</td></tr>'}</tbody>
    </table>"""

    # Goals section
    goal_rows = ""
    gst_colors = {"not_started": "badge-gray", "in_progress": "badge-yellow", "achieved": "badge-green", "missed": "badge-red"}
    for g in goals:
        gst = g.status or "not_started"
        goal_rows += f'<div style="display:flex;align-items:center;gap:0.75rem;padding:0.625rem 0;border-bottom:1px solid #f1f5f9"><span class="badge {gst_colors.get(gst,"badge-gray")}">{gst.replace("_"," ").title()}</span><span style="font-size:0.9rem">{g.description or "—"}</span></div>'

    ceremony_modal = f"""
    <div id="ceremony-modal" class="modal" onclick="if(event.target===this)document.getElementById('ceremony-modal').classList.remove('show')">
      <div class="modal-box">
        <div class="modal-head"><h3>Schedule Ceremony</h3><button class="modal-close" onclick="document.getElementById('ceremony-modal').classList.remove('show')">×</button></div>
        <form method="post" action="/project/{project_id}/sprints/{sprint_id}/ceremony">
          <div class="modal-body">
            <div class="form-group">
              <label>Type</label>
              <select name="ceremony_type" class="form-control">
                <option value="planning">Planning</option>
                <option value="review">Review</option>
                <option value="retro">Retrospective</option>
                <option value="standup">Daily Standup</option>
              </select>
            </div>
            <div class="form-row">
              <div class="form-group"><label>Date & Time</label><input type="datetime-local" name="scheduled_at" class="form-control"></div>
              <div class="form-group"><label>Duration (min)</label><input type="number" name="duration_minutes" class="form-control" value="60"></div>
            </div>
            <div class="form-group"><label>Notes</label><textarea name="notes" class="form-control" rows="2"></textarea></div>
          </div>
          <div class="modal-foot">
            <button type="button" class="btn btn-ghost" onclick="document.getElementById('ceremony-modal').classList.remove('show')">Cancel</button>
            <button type="submit" class="btn btn-primary">Schedule</button>
          </div>
        </form>
      </div>
    </div>"""

    goal_modal = f"""
    <div id="goal-modal" class="modal" onclick="if(event.target===this)document.getElementById('goal-modal').classList.remove('show')">
      <div class="modal-box">
        <div class="modal-head"><h3>Add Sprint Goal</h3><button class="modal-close" onclick="document.getElementById('goal-modal').classList.remove('show')">×</button></div>
        <form method="post" action="/project/{project_id}/sprints/{sprint_id}/goal">
          <div class="modal-body">
            <div class="form-group"><label>Goal Description</label><textarea name="description" class="form-control" rows="3" placeholder="What should be accomplished?" required></textarea></div>
          </div>
          <div class="modal-foot">
            <button type="button" class="btn btn-ghost" onclick="document.getElementById('goal-modal').classList.remove('show')">Cancel</button>
            <button type="submit" class="btn btn-primary">Add Goal</button>
          </div>
        </form>
      </div>
    </div>"""

    breadcrumb = (
        f'<a href="/projects">Projects</a><span class="sep">›</span>'
        f'<a href="/project/{project_id}/sprints">{proj_name} · Sprints</a>'
        f'<span class="sep">›</span><span class="current">{sp.name or sprint_id}</span>'
    )

    content = f"""
    {project_tabs(project_id, "sprints")}
    <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:1.5rem;flex-wrap:wrap;gap:1rem">
      <div>
        <div style="display:flex;align-items:center;gap:0.75rem;margin-bottom:0.25rem">
          <h2 style="font-size:1.35rem;font-weight:700">{sp.name or sprint_id}</h2>
          <span class="badge" style="background:{bg};color:{col}">{lbl}</span>
        </div>
        <p style="color:var(--c-muted);font-size:0.875rem">{sp.goal or 'No goal set'}</p>
        {'<p style="color:var(--c-muted);font-size:0.8rem;margin-top:0.25rem">'+sp.start_date+' → '+sp.end_date+'</p>' if sp.start_date or sp.end_date else ''}
      </div>
      <div style="display:flex;gap:0.5rem;flex-wrap:wrap">
        <button class="btn btn-ghost btn-sm" onclick="document.getElementById('goal-modal').classList.add('show')">+ Goal</button>
        <button class="btn btn-ghost btn-sm" onclick="document.getElementById('ceremony-modal').classList.add('show')">+ Ceremony</button>
        {'<form method="post" action="/project/'+project_id+'/sprints/'+sprint_id+'/start" style="display:inline"><button class="btn btn-success btn-sm">▶ Start Sprint</button></form>' if st=='planned' else ''}
        {'<form method="post" action="/project/'+project_id+'/sprints/'+sprint_id+'/complete" style="display:inline"><button class="btn btn-ghost btn-sm">✓ Complete</button></form>' if st=='active' else ''}
      </div>
    </div>

    <div class="stats-row">
      <div class="stat-chip"><span class="dot" style="background:{col}"></span>{total} Issues</div>
      <div class="stat-chip"><span class="dot" style="background:#10b981"></span>{done} Done</div>
      <div class="stat-chip"><span class="dot" style="background:#3b82f6"></span>{pct}% Complete</div>
      <div class="stat-chip"><span class="dot" style="background:#8b5cf6"></span>{len(ceremonies)} Ceremonies</div>
    </div>

    <div style="margin-bottom:0.75rem">
      <div class="progress-bar" style="height:10px;border-radius:5px">
        <div class="progress-fill" style="width:{pct}%;background:{col};height:100%"></div>
      </div>
    </div>

    {'<div class="detail-card" style="margin-bottom:1.25rem"><div class="detail-card-head">Sprint Goals</div><div class="detail-card-body">'+goal_rows+'<p style="color:var(--c-muted);font-size:0.85rem;margin-top:0.75rem">No goals yet</p></div></div>' if not goals else '<div class="detail-card" style="margin-bottom:1.25rem"><div class="detail-card-head">Sprint Goals</div><div class="detail-card-body">'+goal_rows+'</div></div>'}

    <h3 style="font-size:0.95rem;font-weight:700;margin-bottom:0.75rem">Issues ({total})</h3>
    {issues_section}

    <h3 style="font-size:0.95rem;font-weight:700;margin:1.25rem 0 0.75rem">Ceremonies</h3>
    {ceremony_section}

    {ceremony_modal}
    {goal_modal}"""

    return HTMLResponse(render_app(f"{sp.name or sprint_id} · Sprint", content, project_id, "sprints",
                                   breadcrumb=breadcrumb, user_name=user_name))


@router.post("/project/{project_id}/sprints/{sprint_id}/ceremony")
async def sprint_ceremony_create(
    project_id: str, sprint_id: str,
    ceremony_type: str = Form("standup"),
    scheduled_at: str = Form(""),
    duration_minutes: str = Form("60"),
    notes: str = Form(""),
    db: AsyncSession = Depends(get_db),
):
    cer = Ceremony(
        sprint_id=sprint_id,
        ceremony_type=ceremony_type,
        scheduled_at=scheduled_at or None,
        duration_minutes=int(duration_minutes) if duration_minutes.isdigit() else None,
        notes=notes or None,
    )
    db.add(cer)
    try:
        await db.commit()
    except Exception:
        await db.rollback()
    return RedirectResponse(url=f"/project/{project_id}/sprints/{sprint_id}", status_code=303)


@router.post("/project/{project_id}/sprints/{sprint_id}/goal")
async def sprint_goal_create(
    project_id: str, sprint_id: str,
    description: str = Form(""),
    db: AsyncSession = Depends(get_db),
):
    g = SprintGoal(sprint_id=sprint_id, description=description)
    db.add(g)
    try:
        await db.commit()
    except Exception:
        await db.rollback()
    return RedirectResponse(url=f"/project/{project_id}/sprints/{sprint_id}", status_code=303)


# ---------------------------------------------------------------------------
# Settings tab
# ---------------------------------------------------------------------------
@router.get("/project/{project_id}/settings", response_class=HTMLResponse)
async def settings_view(project_id: str, request: Request):
    if not request.cookies.get("auth_token"):
        return RedirectResponse(url="/login", status_code=302)

    proj = next((p for p in PROJECTS if p["id"] == project_id), {"name": project_id, "description": ""})
    proj_name = proj["name"]

    content = f"""
    {project_tabs(project_id, "settings")}
    <div style="max-width:640px;display:flex;flex-direction:column;gap:1.25rem">
      <div class="detail-card">
        <div class="detail-card-head">Project Information</div>
        <div class="detail-card-body">
          <div class="meta-row"><span class="meta-label">Project ID</span><code style="font-size:0.85rem;background:#f1f5f9;padding:0.2rem 0.5rem;border-radius:0.25rem">{project_id}</code></div>
          <div class="meta-row"><span class="meta-label">Name</span><span>{proj_name}</span></div>
          <div class="meta-row"><span class="meta-label">Description</span><span>{proj['description']}</span></div>
          <div class="meta-row"><span class="meta-label">Status</span>{status_badge("ready")}</div>
        </div>
      </div>
      <div class="detail-card">
        <div class="detail-card-head">Members</div>
        <div class="detail-card-body">
          <div class="meta-row">
            <div style="display:flex;align-items:center;gap:0.75rem">
              <div class="avatar" style="width:28px;height:28px;font-size:0.7rem">DU</div>
              <span>Demo User</span>
            </div>
            <span class="badge badge-blue">Owner</span>
          </div>
        </div>
      </div>
      <div class="detail-card" style="border-color:#fecaca">
        <div class="detail-card-head" style="color:var(--c-danger)">Danger Zone</div>
        <div class="detail-card-body" style="display:flex;justify-content:space-between;align-items:center">
          <div>
            <p style="font-weight:600;font-size:0.9rem">Delete this project</p>
            <p style="color:var(--c-muted);font-size:0.8rem;margin-top:0.2rem">Permanently remove this project and all its issues.</p>
          </div>
          <button class="btn btn-danger btn-sm" onclick="confirm('Delete {proj_name}?')">Delete</button>
        </div>
      </div>
    </div>"""

    return HTMLResponse(render_app(f"{proj_name} · Settings", content, project_id, "settings", user_name="Demo User"))


# ---------------------------------------------------------------------------
# Issue detail
# ---------------------------------------------------------------------------
@router.get("/project/{project_id}/issue/{issue_id}", response_class=HTMLResponse)
async def issue_detail(project_id: str, issue_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    if not request.cookies.get("auth_token"):
        return RedirectResponse(url="/login", status_code=302)

    from sqlalchemy import select
    try:
        result = await db.execute(select(Issue).where(Issue.id == issue_id))
        iss = result.scalar_one_or_none()
    except Exception:
        iss = None

    proj_name = next((p["name"] for p in PROJECTS if p["id"] == project_id), project_id)

    if not iss:
        content = '<div class="alert alert-error">Issue not found.</div><a href="javascript:history.back()" class="btn btn-ghost">← Back</a>'
        return HTMLResponse(render_app("Issue Not Found", content, project_id, user_name="Demo User"), status_code=404)

    title = getattr(iss, "title", "Untitled")
    desc = getattr(iss, "description", "") or "<em style='color:var(--c-muted)'>No description provided.</em>"
    s = getattr(iss, "status", "backlog")
    itype = getattr(iss, "issue_type", "task")
    prio = getattr(iss, "priority", "medium")
    pts = getattr(iss, "story_points", None)
    created = getattr(iss, "created_at", "")

    breadcrumb = f'<a href="/projects">Projects</a><span class="sep">›</span><a href="/project/{project_id}/backlog">{proj_name}</a><span class="sep">›</span><span class="current">{issue_id}</span>'

    content = f"""
    <div style="margin-bottom:1.25rem;display:flex;align-items:center;gap:1rem">
      <a href="/project/{project_id}/backlog" class="btn btn-ghost btn-sm">← Backlog</a>
      <span class="issue-id" style="font-size:0.9rem">{issue_id}</span>
      {status_badge(s)}
    </div>
    <div class="detail-grid">
      <div style="display:flex;flex-direction:column;gap:1.25rem">
        <div class="detail-card">
          <div class="detail-card-body">
            <h1 style="font-size:1.35rem;font-weight:700;margin-bottom:1rem">{title}</h1>
            <div style="font-size:0.9rem;line-height:1.7;color:var(--c-text)">{desc}</div>
          </div>
        </div>
        <div class="detail-card">
          <div class="detail-card-head">Activity</div>
          <div class="detail-card-body" style="color:var(--c-muted);font-size:0.85rem">
            <p>Created {created}</p>
          </div>
        </div>
      </div>
      <div style="display:flex;flex-direction:column;gap:1rem">
        <div class="detail-card">
          <div class="detail-card-head">Details</div>
          <div class="detail-card-body">
            <div class="meta-row"><span class="meta-label">Status</span>
              <select class="status-sel" onchange="updateStatus('{issue_id}',this.value,'{project_id}')">
                {"".join(f'<option value="{v}" {"selected" if v==s else ""}>{l}</option>' for v,l in [("backlog","Backlog"),("ready","Ready"),("in_progress","In Progress"),("in_review","In Review"),("blocked","Blocked"),("done","Done")])}
              </select>
            </div>
            <div class="meta-row"><span class="meta-label">Type</span>{type_badge(itype)}</div>
            <div class="meta-row"><span class="meta-label">Priority</span>{priority_html(prio)}</div>
            <div class="meta-row"><span class="meta-label">Story Points</span><strong>{pts or "—"}</strong></div>
          </div>
        </div>
        <button class="btn btn-primary" style="width:100%" hx-get="/project/{project_id}/backlog/estimate?issue_id={issue_id}" hx-target="#modal-content" onclick="openModal('Estimate Issue')">🎯 Estimate Story Points</button>
      </div>
    </div>"""

    return HTMLResponse(render_app(f"{issue_id} · {proj_name}", content, project_id, breadcrumb=breadcrumb, user_name="Demo User"))


# ---------------------------------------------------------------------------
# Agents roster
# ---------------------------------------------------------------------------
_AGENT_ROLE_BADGES = {
    "actor":        ("badge-blue",   "Actor"),
    "reviewer":     ("badge-purple", "Reviewer"),
    "assistant":    ("badge-green",  "Assistant"),
    "compressor":   ("badge-gray",   "Compressor"),
    "scrum_master": ("badge-yellow", "Scrum Master"),
}
_AGENT_STATUS_DOT = {
    "idle":    "#10b981",
    "busy":    "#f59e0b",
    "paused":  "#94a3b8",
    "offline": "#475569",
    "error":   "#ef4444",
}


@router.get("/agents", response_class=HTMLResponse)
async def agents_list(request: Request, db: AsyncSession = Depends(get_db)):
    if not request.cookies.get("auth_token"):
        return RedirectResponse(url="/login", status_code=302)
    user_name = get_user_from_cookie(request) or "User"

    from sqlalchemy import select
    agents = []
    models_map: dict = {}
    try:
        res = await db.execute(select(Agent).order_by(Agent.name))
        agents = list(res.scalars().all())
        mres = await db.execute(select(AIModel))
        for m in mres.scalars().all():
            models_map[m.id] = m
    except Exception:
        pass

    rows = ""
    for ag in agents:
        role_cls, role_lbl = _AGENT_ROLE_BADGES.get(ag.role, ("badge-gray", ag.role.title()))
        st_dot = _AGENT_STATUS_DOT.get(ag.availability_status, "#94a3b8")
        mdl = models_map.get(ag.model_id)
        mdl_name = f"{mdl.provider}/{mdl.model_name}" if mdl else "—"
        active_badge = '<span class="badge badge-green">Active</span>' if ag.is_active else '<span class="badge badge-gray">Inactive</span>'
        emoji = ag.avatar_emoji or "🤖"
        rows += f"""<tr>
          <td>
            <div style="display:flex;align-items:center;gap:0.75rem">
              <div class="avatar" style="background:#1e293b;width:32px;height:32px;font-size:1rem">{emoji}</div>
              <div>
                <a href="/agents/{ag.id}" class="issue-link">{ag.name}</a>
                <div style="font-size:0.75rem;color:var(--c-muted)">{ag.description or ''}</div>
              </div>
            </div>
          </td>
          <td><span class="badge {role_cls}">{role_lbl}</span></td>
          <td>
            <span class="prio"><span class="prio-dot" style="background:{st_dot}"></span>{ag.availability_status.title()}</span>
          </td>
          <td><code style="font-size:0.75rem;background:#f1f5f9;padding:0.15rem 0.4rem;border-radius:0.25rem">{mdl_name}</code></td>
          <td>{active_badge}</td>
          <td>
            <a href="/agents/{ag.id}/edit" class="btn btn-ghost btn-sm">Edit</a>
          </td>
        </tr>"""

    if not rows:
        rows = '<tr><td colspan="6" class="empty-state" style="padding:3rem">No agents registered yet</td></tr>'

    create_modal = """
    <div id="agent-modal" class="modal" onclick="if(event.target===this)document.getElementById('agent-modal').classList.remove('show')">
      <div class="modal-box">
        <div class="modal-head"><h3>Register Agent</h3><button class="modal-close" onclick="document.getElementById('agent-modal').classList.remove('show')">×</button></div>
        <form method="post" action="/agents/create">
          <div class="modal-body">
            <div class="form-row">
              <div class="form-group">
                <label>Name <span style="color:#ef4444">*</span></label>
                <input type="text" name="name" class="form-control" placeholder="Alpha Agent" required>
              </div>
              <div class="form-group">
                <label>Avatar Emoji</label>
                <input type="text" name="avatar_emoji" class="form-control" placeholder="🤖" maxlength="4">
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>Role <span style="color:#ef4444">*</span></label>
                <select name="role" class="form-control" required>
                  <option value="actor">Actor</option>
                  <option value="reviewer">Reviewer</option>
                  <option value="assistant">Assistant</option>
                  <option value="compressor">Compressor</option>
                  <option value="scrum_master">Scrum Master</option>
                </select>
              </div>
              <div class="form-group">
                <label>Model ID <span style="color:#ef4444">*</span></label>
                <input type="text" name="model_id" class="form-control" placeholder="(paste AI Model ID)" required>
              </div>
            </div>
            <div class="form-group">
              <label>Description</label>
              <textarea name="description" class="form-control" rows="2"></textarea>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>Temperature</label>
                <input type="number" name="temperature" class="form-control" value="0.7" step="0.1" min="0" max="2">
              </div>
              <div class="form-group">
                <label>Max Tokens</label>
                <input type="number" name="max_tokens" class="form-control" value="4096">
              </div>
            </div>
            <div class="form-group">
              <label>System Prompt</label>
              <textarea name="system_prompt" class="form-control" rows="3" placeholder="You are..."></textarea>
            </div>
          </div>
          <div class="modal-foot">
            <button type="button" class="btn btn-ghost" onclick="document.getElementById('agent-modal').classList.remove('show')">Cancel</button>
            <button type="submit" class="btn btn-primary">Register Agent</button>
          </div>
        </form>
      </div>
    </div>"""

    stats = {}
    for ag in agents:
        stats[ag.availability_status] = stats.get(ag.availability_status, 0) + 1

    stat_chips = "".join(
        f'<div class="stat-chip"><span class="dot" style="background:{_AGENT_STATUS_DOT.get(k,"#94a3b8")}"></span>{v} {k.title()}</div>'
        for k, v in stats.items()
    )

    content = f"""
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:1.25rem">
      <div>
        <h2 style="font-size:1.35rem;font-weight:700">🤖 Agents</h2>
        <p style="color:var(--c-muted);font-size:0.85rem">{len(agents)} registered agent{'s' if len(agents) != 1 else ''}</p>
      </div>
      <div style="display:flex;gap:0.75rem">
        <a href="/models" class="btn btn-ghost">⚡ AI Models</a>
        <button class="btn btn-primary" onclick="document.getElementById('agent-modal').classList.add('show')">+ Register Agent</button>
      </div>
    </div>
    <div class="stats-row">{stat_chips}</div>
    <table class="data-table">
      <thead><tr><th>Agent</th><th>Role</th><th>Status</th><th>Model</th><th>Active</th><th></th></tr></thead>
      <tbody>{rows}</tbody>
    </table>
    {create_modal}"""

    breadcrumb = '<a href="/projects">Home</a><span class="sep">›</span><span class="current">Agents</span>'
    return HTMLResponse(render_app("Agents · AgileAI", content, breadcrumb=breadcrumb, user_name=user_name))


@router.post("/agents/create")
async def agent_create(
    request: Request,
    name: str = Form(...),
    role: str = Form("actor"),
    model_id: str = Form(...),
    description: str = Form(""),
    avatar_emoji: str = Form(""),
    temperature: str = Form("0.7"),
    max_tokens: str = Form("4096"),
    system_prompt: str = Form(""),
    db: AsyncSession = Depends(get_db),
):
    ag = Agent(
        name=name,
        role=role,
        model_id=model_id,
        description=description or None,
        avatar_emoji=avatar_emoji or None,
        temperature=float(temperature) if temperature else 0.7,
        max_tokens=int(max_tokens) if max_tokens.isdigit() else 4096,
        system_prompt=system_prompt or None,
    )
    db.add(ag)
    try:
        await db.commit()
    except Exception:
        await db.rollback()
    return RedirectResponse(url="/agents", status_code=303)


@router.get("/agents/{agent_id}", response_class=HTMLResponse)
async def agent_detail(agent_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    if not request.cookies.get("auth_token"):
        return RedirectResponse(url="/login", status_code=302)
    user_name = get_user_from_cookie(request) or "User"

    from sqlalchemy import select
    ag = None
    mdl = None
    try:
        res = await db.execute(select(Agent).where(Agent.id == agent_id))
        ag = res.scalar_one_or_none()
        if ag:
            mres = await db.execute(select(AIModel).where(AIModel.id == ag.model_id))
            mdl = mres.scalar_one_or_none()
    except Exception:
        pass

    if not ag:
        return HTMLResponse(render_app("Agent Not Found", '<div class="alert alert-error">Agent not found</div>', user_name=user_name), status_code=404)

    role_cls, role_lbl = _AGENT_ROLE_BADGES.get(ag.role, ("badge-gray", ag.role.title()))
    st_dot = _AGENT_STATUS_DOT.get(ag.availability_status, "#94a3b8")

    content = f"""
    <div style="margin-bottom:1.25rem;display:flex;align-items:center;gap:1rem">
      <a href="/agents" class="btn btn-ghost btn-sm">← Agents</a>
      <a href="/agents/{agent_id}/edit" class="btn btn-ghost btn-sm">Edit</a>
    </div>
    <div class="detail-grid">
      <div style="display:flex;flex-direction:column;gap:1.25rem">
        <div class="detail-card">
          <div class="detail-card-body">
            <div style="display:flex;align-items:center;gap:1rem;margin-bottom:1.25rem">
              <div class="avatar" style="background:#1e293b;width:52px;height:52px;font-size:1.75rem">{ag.avatar_emoji or '🤖'}</div>
              <div>
                <h1 style="font-size:1.35rem;font-weight:700">{ag.name}</h1>
                <div style="display:flex;gap:0.5rem;margin-top:0.25rem">
                  <span class="badge {role_cls}">{role_lbl}</span>
                  <span class="prio"><span class="prio-dot" style="background:{st_dot}"></span>{ag.availability_status.title()}</span>
                </div>
              </div>
            </div>
            <p style="font-size:0.9rem;color:var(--c-muted)">{ag.description or 'No description.'}</p>
          </div>
        </div>
        {'<div class="detail-card"><div class="detail-card-head">System Prompt</div><div class="detail-card-body"><pre style="font-size:0.8rem;white-space:pre-wrap;color:var(--c-muted)">'+ag.system_prompt+'</pre></div></div>' if ag.system_prompt else ''}
      </div>
      <div style="display:flex;flex-direction:column;gap:1rem">
        <div class="detail-card">
          <div class="detail-card-head">Configuration</div>
          <div class="detail-card-body">
            <div class="meta-row"><span class="meta-label">Model</span><code style="font-size:0.8rem">{mdl.provider+"/"+mdl.model_name if mdl else ag.model_id}</code></div>
            <div class="meta-row"><span class="meta-label">Temperature</span><strong>{ag.temperature}</strong></div>
            <div class="meta-row"><span class="meta-label">Max Tokens</span><strong>{ag.max_tokens}</strong></div>
            <div class="meta-row"><span class="meta-label">Max Concurrent</span><strong>{ag.max_concurrent_tasks}</strong></div>
            <div class="meta-row"><span class="meta-label">Active</span>{'<span class="badge badge-green">Yes</span>' if ag.is_active else '<span class="badge badge-gray">No</span>'}</div>
          </div>
        </div>
        <a href="/admin/agent_token_usage?agent_id={agent_id}" class="btn btn-ghost" style="text-align:center">📊 Token Usage</a>
        <a href="/admin/execution_logs?agent_id={agent_id}" class="btn btn-ghost" style="text-align:center">📋 Execution Logs</a>
      </div>
    </div>"""

    breadcrumb = f'<a href="/agents">Agents</a><span class="sep">›</span><span class="current">{ag.name}</span>'
    return HTMLResponse(render_app(f"{ag.name} · Agent", content, breadcrumb=breadcrumb, user_name=user_name))


@router.get("/agents/{agent_id}/edit", response_class=HTMLResponse)
async def agent_edit_form(agent_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    if not request.cookies.get("auth_token"):
        return RedirectResponse(url="/login", status_code=302)
    user_name = get_user_from_cookie(request) or "User"

    from sqlalchemy import select
    ag = None
    try:
        res = await db.execute(select(Agent).where(Agent.id == agent_id))
        ag = res.scalar_one_or_none()
    except Exception:
        pass

    if not ag:
        return RedirectResponse(url="/agents", status_code=302)

    content = f"""
    <div style="max-width:640px">
      <div style="margin-bottom:1.25rem"><a href="/agents/{agent_id}" class="btn btn-ghost btn-sm">← Cancel</a></div>
      <h2 style="font-size:1.2rem;font-weight:700;margin-bottom:1.25rem">Edit Agent: {ag.name}</h2>
      <form method="post" action="/agents/{agent_id}/update" style="background:white;border:1.5px solid var(--c-border);border-radius:0.75rem;padding:1.5rem">
        <div class="form-row">
          <div class="form-group"><label>Name</label><input type="text" name="name" value="{ag.name}" class="form-control" required></div>
          <div class="form-group"><label>Avatar Emoji</label><input type="text" name="avatar_emoji" value="{ag.avatar_emoji or ''}" class="form-control" maxlength="4"></div>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label>Role</label>
            <select name="role" class="form-control">
              {''.join(f'<option value="{v}" {"selected" if v==ag.role else ""}>{l}</option>' for v,l in [("actor","Actor"),("reviewer","Reviewer"),("assistant","Assistant"),("compressor","Compressor"),("scrum_master","Scrum Master")])}
            </select>
          </div>
          <div class="form-group">
            <label>Status</label>
            <select name="availability_status" class="form-control">
              {''.join(f'<option value="{v}" {"selected" if v==ag.availability_status else ""}>{v.title()}</option>' for v in ["idle","busy","paused","offline","error"])}
            </select>
          </div>
        </div>
        <div class="form-group"><label>Description</label><textarea name="description" class="form-control" rows="2">{ag.description or ''}</textarea></div>
        <div class="form-row">
          <div class="form-group"><label>Temperature</label><input type="number" name="temperature" value="{ag.temperature}" step="0.1" min="0" max="2" class="form-control"></div>
          <div class="form-group"><label>Max Tokens</label><input type="number" name="max_tokens" value="{ag.max_tokens}" class="form-control"></div>
        </div>
        <div class="form-group"><label>System Prompt</label><textarea name="system_prompt" class="form-control" rows="4">{ag.system_prompt or ''}</textarea></div>
        <div style="display:flex;gap:0.75rem;justify-content:flex-end;margin-top:1rem">
          <a href="/agents/{agent_id}" class="btn btn-ghost">Cancel</a>
          <button type="submit" class="btn btn-primary">Save Changes</button>
        </div>
      </form>
    </div>"""

    breadcrumb = f'<a href="/agents">Agents</a><span class="sep">›</span><a href="/agents/{agent_id}">{ag.name}</a><span class="sep">›</span><span class="current">Edit</span>'
    return HTMLResponse(render_app(f"Edit {ag.name}", content, breadcrumb=breadcrumb, user_name=user_name))


@router.post("/agents/{agent_id}/update")
async def agent_update(
    agent_id: str, request: Request,
    name: str = Form(...),
    role: str = Form("actor"),
    avatar_emoji: str = Form(""),
    description: str = Form(""),
    availability_status: str = Form("idle"),
    temperature: str = Form("0.7"),
    max_tokens: str = Form("4096"),
    system_prompt: str = Form(""),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import select, update
    await db.execute(update(Agent).where(Agent.id == agent_id).values(
        name=name, role=role,
        avatar_emoji=avatar_emoji or None,
        description=description or None,
        availability_status=availability_status,
        temperature=float(temperature) if temperature else 0.7,
        max_tokens=int(max_tokens) if max_tokens.isdigit() else 4096,
        system_prompt=system_prompt or None,
    ))
    try:
        await db.commit()
    except Exception:
        await db.rollback()
    return RedirectResponse(url=f"/agents/{agent_id}", status_code=303)


# ---------------------------------------------------------------------------
# AI Models registry
# ---------------------------------------------------------------------------
@router.get("/models", response_class=HTMLResponse)
async def models_list(request: Request, db: AsyncSession = Depends(get_db)):
    if not request.cookies.get("auth_token"):
        return RedirectResponse(url="/login", status_code=302)
    user_name = get_user_from_cookie(request) or "User"

    from sqlalchemy import select
    models = []
    try:
        res = await db.execute(select(AIModel).order_by(AIModel.provider, AIModel.model_name))
        models = list(res.scalars().all())
    except Exception:
        pass

    rows = ""
    type_colors = {
        "llm": "badge-blue", "embedding": "badge-purple", "vision": "badge-green",
        "code": "badge-yellow", "compressor": "badge-gray",
    }
    for m in models:
        local_badge = '<span class="badge badge-green">Local</span>' if m.is_local else '<span class="badge badge-gray">API</span>'
        active_badge = '<span class="badge badge-green">Active</span>' if m.is_active else '<span class="badge badge-gray">Off</span>'
        tc = type_colors.get(m.model_type, "badge-gray")
        cost = ""
        if m.cost_input_per_1k is not None:
            cost = f"${m.cost_input_per_1k:.4f}/$" + (f"{m.cost_output_per_1k:.4f}" if m.cost_output_per_1k else "—") + " /1k"
        rows += f"""<tr>
          <td>
            <div style="font-weight:600">{m.model_name}</div>
            <div style="font-size:0.75rem;color:var(--c-muted)">{m.provider}</div>
          </td>
          <td><span class="badge {tc}">{m.model_type}</span></td>
          <td>{local_badge}</td>
          <td>{m.context_window or '—'}</td>
          <td style="font-size:0.8rem;color:var(--c-muted)">{cost or '—'}</td>
          <td>{active_badge}</td>
          <td>
            <button class="btn btn-ghost btn-sm" onclick="navigator.clipboard.writeText('{m.id}')" title="Copy ID">⊕ Copy ID</button>
          </td>
        </tr>"""

    if not rows:
        rows = '<tr><td colspan="7" class="empty-state" style="padding:3rem">No AI models registered yet</td></tr>'

    register_modal = """
    <div id="model-modal" class="modal" onclick="if(event.target===this)document.getElementById('model-modal').classList.remove('show')">
      <div class="modal-box">
        <div class="modal-head"><h3>Register AI Model</h3><button class="modal-close" onclick="document.getElementById('model-modal').classList.remove('show')">×</button></div>
        <form method="post" action="/models/create">
          <div class="modal-body">
            <div class="form-row">
              <div class="form-group">
                <label>Provider <span style="color:#ef4444">*</span></label>
                <input type="text" name="provider" class="form-control" placeholder="anthropic / ollama" required>
              </div>
              <div class="form-group">
                <label>Model Name <span style="color:#ef4444">*</span></label>
                <input type="text" name="model_name" class="form-control" placeholder="claude-sonnet-4-6" required>
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>Type</label>
                <select name="model_type" class="form-control">
                  <option value="llm">LLM</option>
                  <option value="embedding">Embedding</option>
                  <option value="vision">Vision</option>
                  <option value="code">Code</option>
                  <option value="compressor">Compressor</option>
                </select>
              </div>
              <div class="form-group">
                <label>Context Window</label>
                <input type="number" name="context_window" class="form-control" placeholder="200000">
              </div>
            </div>
            <div class="form-group">
              <label>API Endpoint (for Ollama)</label>
              <input type="text" name="api_endpoint" class="form-control" placeholder="http://localhost:11434">
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>Cost Input /1k tokens</label>
                <input type="number" name="cost_input_per_1k" step="0.0001" class="form-control" placeholder="0.0030">
              </div>
              <div class="form-group">
                <label>Cost Output /1k tokens</label>
                <input type="number" name="cost_output_per_1k" step="0.0001" class="form-control" placeholder="0.0150">
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label><input type="checkbox" name="is_local"> Local (Ollama)</label>
              </div>
              <div class="form-group">
                <label><input type="checkbox" name="is_active" checked> Active</label>
              </div>
            </div>
            <div class="form-group"><label>Notes</label><textarea name="notes" class="form-control" rows="2"></textarea></div>
          </div>
          <div class="modal-foot">
            <button type="button" class="btn btn-ghost" onclick="document.getElementById('model-modal').classList.remove('show')">Cancel</button>
            <button type="submit" class="btn btn-primary">Register Model</button>
          </div>
        </form>
      </div>
    </div>"""

    content = f"""
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:1.25rem">
      <div>
        <h2 style="font-size:1.35rem;font-weight:700">⚡ AI Models</h2>
        <p style="color:var(--c-muted);font-size:0.85rem">{len(models)} registered model{'s' if len(models) != 1 else ''}</p>
      </div>
      <div style="display:flex;gap:0.75rem">
        <a href="/agents" class="btn btn-ghost">🤖 Agents</a>
        <button class="btn btn-primary" onclick="document.getElementById('model-modal').classList.add('show')">+ Register Model</button>
      </div>
    </div>
    <table class="data-table">
      <thead><tr><th>Model</th><th>Type</th><th>Source</th><th>Context</th><th>Cost</th><th>Status</th><th></th></tr></thead>
      <tbody>{rows}</tbody>
    </table>
    {register_modal}"""

    breadcrumb = '<a href="/projects">Home</a><span class="sep">›</span><span class="current">AI Models</span>'
    return HTMLResponse(render_app("AI Models · AgileAI", content, breadcrumb=breadcrumb, user_name=user_name))


@router.post("/models/create")
async def model_create(
    request: Request,
    provider: str = Form(...),
    model_name: str = Form(...),
    model_type: str = Form("llm"),
    context_window: str = Form(""),
    api_endpoint: str = Form(""),
    cost_input_per_1k: str = Form(""),
    cost_output_per_1k: str = Form(""),
    is_local: str = Form(""),
    is_active: str = Form("on"),
    notes: str = Form(""),
    db: AsyncSession = Depends(get_db),
):
    m = AIModel(
        provider=provider,
        model_name=model_name,
        model_type=model_type,
        context_window=int(context_window) if context_window.isdigit() else None,
        api_endpoint=api_endpoint or None,
        cost_input_per_1k=float(cost_input_per_1k) if cost_input_per_1k else None,
        cost_output_per_1k=float(cost_output_per_1k) if cost_output_per_1k else None,
        is_local=is_local in ("on", "true", "1"),
        is_active=is_active in ("on", "true", "1"),
        notes=notes or None,
    )
    db.add(m)
    try:
        await db.commit()
    except Exception:
        await db.rollback()
    return RedirectResponse(url="/models", status_code=303)
