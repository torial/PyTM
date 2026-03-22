from functools import partial as fp

from fastapi import APIRouter, Depends, Form, Query, Request
from fastapi.responses import HTMLResponse

from PyTM import settings
from PyTM.core import project_handler, task_handler
from PyTM.web.app import templates
from PyTM.web.dependencies import DataStore, get_data_store
from PyTM.web.routes._helpers import (
    active_session, clear_active, set_active,
    oob_timer, oob_flash, project_view, fmt_duration,
)

router = APIRouter(prefix="/projects")


def _render_list(request: Request, store: DataStore, sort: str = "name") -> str:
    data = store.load_data()
    active = active_session(request)
    projects = [project_view(n, data, active) for n in data]
    if sort == "hours":
        projects.sort(key=lambda p: p["total_seconds"], reverse=True)
    elif sort == "updated":
        projects.sort(key=lambda p: p["last_updated"], reverse=True)
    else:
        projects.sort(key=lambda p: p["name"].lower())
    total_secs = sum(p["total_seconds"] for p in projects)
    billable_secs = sum(p["total_seconds"] for p in projects if p["meta"].get("billable", True))
    return templates.TemplateResponse(
        "partials/project_list.html",
        {
            "request": request,
            "projects": projects,
            "active": active,
            "sort": sort,
            "total_duration": fmt_duration(total_secs),
            "billable_duration": fmt_duration(billable_secs),
        },
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
async def list_projects(
    request: Request,
    sort: str = Query("name"),
    store: DataStore = Depends(get_data_store),
):
    return _render_list(request, store, sort)


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
    list_html = _render_list(request, store).body.decode()
    return HTMLResponse(list_html + oob_flash(f"Project '{name}' created"))


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
    return HTMLResponse(row_html + timer_html + oob_flash("Project paused"))


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
    return HTMLResponse(row_html + timer_html + oob_flash("Project finished"))


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
    return HTMLResponse(row_html + timer_html + oob_flash("Project aborted", "warning"))


# ── Resume ────────────────────────────────────────────────────────────────────

@router.post("/{name}/resume", response_class=HTMLResponse)
async def resume_project(
    request: Request, name: str, store: DataStore = Depends(get_data_store)
):
    store.update(fp(project_handler.create, project_name=name))
    row_html = _render_row(request, store, name).body.decode()
    timer_html = oob_timer(request, templates)
    return HTMLResponse(row_html + timer_html + oob_flash("Project resumed"))


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
    list_html = _render_list(request, store).body.decode()
    return HTMLResponse(list_html + oob_flash("Project archived", "info"))


# ── Update project meta ───────────────────────────────────────────────────────

@router.post("/{name}/meta", response_class=HTMLResponse)
async def update_project_meta(
    request: Request,
    name: str,
    title: str = Form(""),
    client_name: str = Form(""),
    rate: float = Form(0.0),
    billable: str = Form(""),
    store: DataStore = Depends(get_data_store),
):
    def _update(data):
        if data.get(name):
            meta = data[name].setdefault("meta", {})
            meta["title"] = title.strip() or None
            meta["client_name"] = client_name.strip()
            meta["rate"] = rate
            meta["billable"] = billable == "on"
        return data
    store.update(_update)
    row_html = _render_row(request, store, name).body.decode()
    return HTMLResponse(row_html + oob_flash("Project updated"))


# ── Task list for a project ───────────────────────────────────────────────────

@router.get("/{name}/tasks", response_class=HTMLResponse)
async def task_panel(
    request: Request, name: str, store: DataStore = Depends(get_data_store)
):
    data = store.load_data()
    active = active_session(request)
    proj = data.get(name, {})
    proj_title = proj.get("meta", {}).get("title") or name
    return templates.TemplateResponse(
        "partials/task_list.html",
        {
            "request": request,
            "project_name": name,
            "proj_title": proj_title,
            "tasks": proj.get("tasks", {}),
            "active": active,
        },
    )
