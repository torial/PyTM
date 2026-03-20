from functools import partial as fp

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse

from PyTM import settings
from PyTM.core import project_handler, task_handler
from PyTM.web.app import templates
from PyTM.web.dependencies import DataStore, get_data_store
from PyTM.web.routes._helpers import (
    active_session, clear_active, set_active,
    oob_timer, project_view,
)

router = APIRouter(prefix="/projects")


def _render_list(request: Request, store: DataStore) -> str:
    data = store.load_data()
    active = active_session(request)
    projects = [project_view(n, data, active) for n in data]
    return templates.TemplateResponse(
        "partials/project_list.html",
        {"request": request, "projects": projects, "active": active},
    )


def _render_row(request: Request, store: DataStore, name: str) -> str:
    data = store.load_data()
    active = active_session(request)
    pv = project_view(name, data, active)
    return templates.TemplateResponse(
        "partials/project_row.html",
        {"request": request, "p": pv, "active": active},
    )


# ── List ──────────────────────────────────────────────────────────────────────

@router.get("", response_class=HTMLResponse)
async def list_projects(request: Request, store: DataStore = Depends(get_data_store)):
    return _render_list(request, store)


# ── Create ────────────────────────────────────────────────────────────────────

@router.post("", response_class=HTMLResponse)
async def create_project(
    request: Request,
    name: str = Form(...),
    store: DataStore = Depends(get_data_store),
):
    name = name.strip()
    if not name:
        return _render_list(request, store)
    store.update(fp(project_handler.create, project_name=name))
    return _render_list(request, store)


# ── Pause ─────────────────────────────────────────────────────────────────────

@router.post("/{name}/pause", response_class=HTMLResponse)
async def pause_project(
    request: Request, name: str, store: DataStore = Depends(get_data_store)
):
    active = active_session(request)
    # Also pause the active task if it belongs to this project
    if active["project"] == name and active["task"]:
        store.update(fp(task_handler.pause, project_name=name, task_name=active["task"]))
    store.update(fp(project_handler.pause, project_name=name))
    clear_active(request)
    row_html = _render_row(request, store, name).body.decode()
    timer_html = oob_timer(request, templates)
    return HTMLResponse(row_html + timer_html)


# ── Finish ────────────────────────────────────────────────────────────────────

@router.post("/{name}/finish", response_class=HTMLResponse)
async def finish_project(
    request: Request, name: str, store: DataStore = Depends(get_data_store)
):
    active = active_session(request)
    if active["project"] == name and active["task"]:
        store.update(fp(task_handler.finish, project_name=name, task_name=active["task"]))
    store.update(fp(project_handler.finish, project_name=name))
    clear_active(request)
    row_html = _render_row(request, store, name).body.decode()
    timer_html = oob_timer(request, templates)
    return HTMLResponse(row_html + timer_html)


# ── Abort ─────────────────────────────────────────────────────────────────────

@router.post("/{name}/abort", response_class=HTMLResponse)
async def abort_project(
    request: Request, name: str, store: DataStore = Depends(get_data_store)
):
    active = active_session(request)
    if active["project"] == name and active["task"]:
        store.update(fp(task_handler.abort, project_name=name, task_name=active["task"]))
    store.update(fp(project_handler.abort, project_name=name))
    clear_active(request)
    row_html = _render_row(request, store, name).body.decode()
    timer_html = oob_timer(request, templates)
    return HTMLResponse(row_html + timer_html)


# ── Delete (archive) ──────────────────────────────────────────────────────────

@router.delete("/{name}", response_class=HTMLResponse)
async def delete_project(
    request: Request, name: str, store: DataStore = Depends(get_data_store)
):
    data = store.load_data()
    if data.get(name):
        store.archive_project(name, data[name])
        store.update(fp(project_handler.remove, project_name=name))
    active = active_session(request)
    if active["project"] == name:
        clear_active(request)
    return _render_list(request, store)


# ── Task list for a project ───────────────────────────────────────────────────

@router.get("/{name}/tasks", response_class=HTMLResponse)
async def task_panel(
    request: Request, name: str, store: DataStore = Depends(get_data_store)
):
    data = store.load_data()
    active = active_session(request)
    proj = data.get(name, {})
    return templates.TemplateResponse(
        "partials/task_list.html",
        {
            "request": request,
            "project_name": name,
            "tasks": proj.get("tasks", {}),
            "active": active,
        },
    )
