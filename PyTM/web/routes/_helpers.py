"""
Shared helpers used across route modules.
"""
import datetime
from typing import Optional

from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from PyTM import settings
from PyTM.commands.project import get_duration_str


def active_session(request: Request) -> dict:
    """Return the web session's active project/task info (Option B)."""
    return {
        "project": request.session.get("active_project"),
        "project_title": request.session.get("active_project_title"),
        "task": request.session.get("active_task"),
        "since": request.session.get("task_since"),      # ISO string
        "base": request.session.get("task_base", 0.0),   # seconds already accumulated
    }


def clear_active(request: Request) -> None:
    for key in ("active_project", "active_project_title", "active_task", "task_since", "task_base"):
        request.session.pop(key, None)


def set_active(request: Request, project: str, task: str, base: float, project_title: str = "") -> None:
    request.session["active_project"] = project
    request.session["active_project_title"] = project_title or project
    request.session["active_task"] = task
    request.session["task_since"] = datetime.datetime.now().isoformat()
    request.session["task_base"] = base


def fmt_duration(seconds: float) -> str:
    return get_duration_str(int(round(seconds)))


def _last_updated(tasks: dict) -> str:
    """Return the most recent timestamp string across all tasks, or '' if none."""
    stamps = [
        t.get(key, "")
        for t in tasks.values()
        for key in ("created_at", "finished_at", "since")
        if t.get(key)
    ]
    return max(stamps) if stamps else ""


def project_view(name: str, data: dict, active: dict) -> dict:
    """Build a template-friendly dict for a single project."""
    proj = data.get(name, {})
    tasks = proj.get("tasks", {})
    total = sum(t.get("duration", 0) for t in tasks.values()
                if t.get("status") != settings.ABORTED)
    is_active_proj = active["project"] == name
    # If this project has the running task, add live duration hint
    if is_active_proj and active["task"] and active["since"]:
        running_task = tasks.get(active["task"], {})
        total += running_task.get("duration", 0)  # base already in task; since gives live delta
    return {
        "name": name,
        "status": proj.get("status", ""),
        "meta": proj.get("meta", {}),
        "tasks": tasks,
        "total_duration": fmt_duration(total),
        "total_seconds": total,
        "last_updated": _last_updated(tasks),
        "is_active": is_active_proj,
    }


def oob_timer(request: Request, templates: Jinja2Templates) -> str:
    """Render the active-timer partial as an OOB swap string."""
    active = active_session(request)
    return templates.get_template("partials/active_timer.html").render(
        {"request": request, "active": active}
    )


def oob_flash(msg: str, kind: str = "success") -> str:
    """Return an HTMX OOB HTML string that injects a toast into #flash-container."""
    palette = {
        "success": "bg-green-100 text-green-800 border-green-200",
        "error":   "bg-red-100 text-red-800 border-red-200",
        "warning": "bg-yellow-100 text-yellow-800 border-yellow-200",
        "info":    "bg-blue-100 text-blue-800 border-blue-200",
    }
    cls = palette.get(kind, palette["success"])
    return (
        f'<div id="flash-container" hx-swap-oob="true" class="ml-auto">'
        f'<div x-data="{{show:true}}" x-show="show" x-transition'
        f' x-init="setTimeout(()=>show=false,3000)"'
        f' class="text-sm px-3 py-1.5 rounded border {cls} whitespace-nowrap">'
        f'{msg}'
        f'</div></div>'
    )
