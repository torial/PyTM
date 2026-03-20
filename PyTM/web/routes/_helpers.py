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
        "task": request.session.get("active_task"),
        "since": request.session.get("task_since"),      # ISO string
        "base": request.session.get("task_base", 0.0),   # seconds already accumulated
    }


def clear_active(request: Request) -> None:
    for key in ("active_project", "active_task", "task_since", "task_base"):
        request.session.pop(key, None)


def set_active(request: Request, project: str, task: str, base: float) -> None:
    request.session["active_project"] = project
    request.session["active_task"] = task
    request.session["task_since"] = datetime.datetime.now().isoformat()
    request.session["task_base"] = base


def fmt_duration(seconds: float) -> str:
    return get_duration_str(int(round(seconds)))


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
        "is_active": is_active_proj,
    }


def oob_timer(request: Request, templates: Jinja2Templates) -> str:
    """Render the active-timer partial as an OOB swap string."""
    active = active_session(request)
    return templates.get_template("partials/active_timer.html").render(
        {"request": request, "active": active}
    )
