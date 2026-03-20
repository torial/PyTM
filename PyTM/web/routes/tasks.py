import datetime
from functools import partial as fp

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse

from PyTM import settings
from PyTM.core import task_handler
from PyTM.web.app import templates
from PyTM.web.dependencies import DataStore, get_data_store
from PyTM.web.routes._helpers import (
    active_session, clear_active, set_active,
    oob_timer, fmt_duration,
)

router = APIRouter(prefix="/projects/{project_name}/tasks")


def _render_list(request: Request, store: DataStore, project_name: str) -> HTMLResponse:
    data = store.load_data()
    active = active_session(request)
    proj = data.get(project_name, {})
    return templates.TemplateResponse(
        "partials/task_list.html",
        {
            "request": request,
            "project_name": project_name,
            "tasks": proj.get("tasks", {}),
            "active": active,
        },
    )


def _render_row(
    request: Request, store: DataStore, project_name: str, task_name: str
) -> str:
    data = store.load_data()
    active = active_session(request)
    task = data.get(project_name, {}).get("tasks", {}).get(task_name, {})
    return templates.TemplateResponse(
        "partials/task_row.html",
        {
            "request": request,
            "project_name": project_name,
            "task_name": task_name,
            "task": task,
            "active": active,
            "fmt_duration": fmt_duration,
        },
    )


# ── Create + Start ────────────────────────────────────────────────────────────

@router.post("", response_class=HTMLResponse)
async def create_task(
    request: Request,
    project_name: str,
    name: str = Form(...),
    store: DataStore = Depends(get_data_store),
):
    name = name.strip()
    if not name:
        return _render_list(request, store, project_name)

    # Pause any currently running task first
    active = active_session(request)
    if active["task"] and active["project"]:
        store.update(
            fp(task_handler.pause,
               project_name=active["project"],
               task_name=active["task"])
        )
    clear_active(request)

    store.update(fp(task_handler.create, project_name=project_name, task_name=name))
    set_active(request, project_name, name, base=0.0)

    list_html = _render_list(request, store, project_name).body.decode()
    timer_html = oob_timer(request, templates)
    return HTMLResponse(list_html + timer_html)


# ── Start (resume existing) ───────────────────────────────────────────────────

@router.post("/{task_name}/start", response_class=HTMLResponse)
async def start_task(
    request: Request,
    project_name: str,
    task_name: str,
    store: DataStore = Depends(get_data_store),
):
    # Pause any other running task
    active = active_session(request)
    if active["task"] and active["project"]:
        store.update(
            fp(task_handler.pause,
               project_name=active["project"],
               task_name=active["task"])
        )
    clear_active(request)

    store.update(fp(task_handler.create, project_name=project_name, task_name=task_name))
    data = store.load_data()
    base = data.get(project_name, {}).get("tasks", {}).get(task_name, {}).get("duration", 0.0)
    set_active(request, project_name, task_name, base=base)

    row_html = _render_row(request, store, project_name, task_name).body.decode()
    timer_html = oob_timer(request, templates)
    return HTMLResponse(row_html + timer_html)


# ── Pause ─────────────────────────────────────────────────────────────────────

@router.post("/{task_name}/pause", response_class=HTMLResponse)
async def pause_task(
    request: Request,
    project_name: str,
    task_name: str,
    store: DataStore = Depends(get_data_store),
):
    store.update(fp(task_handler.pause, project_name=project_name, task_name=task_name))
    clear_active(request)
    row_html = _render_row(request, store, project_name, task_name).body.decode()
    timer_html = oob_timer(request, templates)
    return HTMLResponse(row_html + timer_html)


# ── Finish ────────────────────────────────────────────────────────────────────

@router.post("/{task_name}/finish", response_class=HTMLResponse)
async def finish_task(
    request: Request,
    project_name: str,
    task_name: str,
    store: DataStore = Depends(get_data_store),
):
    store.update(fp(task_handler.finish, project_name=project_name, task_name=task_name))
    clear_active(request)
    row_html = _render_row(request, store, project_name, task_name).body.decode()
    timer_html = oob_timer(request, templates)
    return HTMLResponse(row_html + timer_html)


# ── Abort ─────────────────────────────────────────────────────────────────────

@router.post("/{task_name}/abort", response_class=HTMLResponse)
async def abort_task(
    request: Request,
    project_name: str,
    task_name: str,
    store: DataStore = Depends(get_data_store),
):
    store.update(fp(task_handler.abort, project_name=project_name, task_name=task_name))
    active = active_session(request)
    if active["project"] == project_name and active["task"] == task_name:
        clear_active(request)
    row_html = _render_row(request, store, project_name, task_name).body.decode()
    timer_html = oob_timer(request, templates)
    return HTMLResponse(row_html + timer_html)


# ── Delete ────────────────────────────────────────────────────────────────────

@router.delete("/{task_name}", response_class=HTMLResponse)
async def delete_task(
    request: Request,
    project_name: str,
    task_name: str,
    store: DataStore = Depends(get_data_store),
):
    active = active_session(request)
    if active["project"] == project_name and active["task"] == task_name:
        clear_active(request)
    store.update(fp(task_handler.remove, project_name=project_name, task_name=task_name))
    return _render_list(request, store, project_name)


# ── Backfill ──────────────────────────────────────────────────────────────────

@router.post("/backfill", response_class=HTMLResponse)
async def backfill_task(
    request: Request,
    project_name: str,
    name: str = Form(...),          # task name from form
    entry_date: str = Form(...),
    hours: float = Form(...),
    entry_time: str = Form("00:00"),
    description: str = Form(""),
    store: DataStore = Depends(get_data_store),
):
    task_name = name.strip()
    if hours < 0:
        return _render_list(request, store, project_name)
    try:
        datetime.date.fromisoformat(entry_date)
        datetime.time.fromisoformat(entry_time)
    except ValueError:
        return _render_list(request, store, project_name)

    timestamp = f"{entry_date} {entry_time}:00.000000"
    duration_seconds = hours * 3600.0
    task_data = {
        "created_at": timestamp,
        "status": settings.FINISHED,
        "duration": duration_seconds,
        "since": "",
        "finished_at": timestamp,
    }
    if description:
        task_data["description"] = description

    def _insert(data):
        if data.get(project_name):
            data[project_name]["tasks"][task_name] = task_data
        return data

    store.update(_insert)
    return _render_list(request, store, project_name)
