import datetime
import os
from typing import List

from fastapi import APIRouter, Depends, Form, Query, Request
from fastapi.responses import HTMLResponse

from PyTM import settings
from PyTM.core import invoice_handler
from PyTM.web.app import templates
from PyTM.web.dependencies import DataStore, get_data_store
from PyTM.web.routes._helpers import active_session, oob_flash

router = APIRouter(prefix="/invoices")


def _render_list(request: Request, store: DataStore) -> HTMLResponse:
    invoices = store.load_invoices()
    return templates.TemplateResponse(
        "partials/invoice_list.html",
        {"request": request, "invoices": invoices},
    )


def _render_row(request: Request, record: dict) -> HTMLResponse:
    return templates.TemplateResponse(
        "partials/invoice_row.html",
        {"request": request, "inv": record},
    )


# ── List ──────────────────────────────────────────────────────────────────────

@router.get("", response_class=HTMLResponse)
async def list_invoices(
    request: Request,
    sort: str = Query("number"),
    order: str = Query("asc"),
    store: DataStore = Depends(get_data_store),
):
    invoices = store.load_invoices()
    reverse = order == "desc"
    if sort == "period":
        key = lambda kv: kv[1].get("date_from") or ""
    else:
        key = lambda kv: int(kv[0]) if str(kv[0]).isdigit() else 0
    sorted_invoices = dict(sorted(invoices.items(), key=key, reverse=reverse))
    return templates.TemplateResponse(
        "partials/invoice_list.html",
        {"request": request, "invoices": sorted_invoices, "sort": sort, "order": order},
    )


# ── Full invoice page ─────────────────────────────────────────────────────────

@router.get("/page", response_class=HTMLResponse)
async def invoices_page(request: Request, store: DataStore = Depends(get_data_store)):
    invoices = store.load_invoices()
    data = store.load_data()
    active = active_session(request)
    next_num = max((int(k) for k in invoices if str(k).isdigit()), default=0) + 1
    return templates.TemplateResponse(
        "invoices.html",
        {
            "request": request,
            "invoices": invoices,
            "projects": data,
            "active": active,
            "next_invoice_number": next_num,
        },
    )


# ── Generate ──────────────────────────────────────────────────────────────────

@router.post("/generate", response_class=HTMLResponse)
async def generate_invoice(
    request: Request,
    invoice_number: str = Form(...),
    title: str = Form("Invoice"),
    project_keys: List[str] = Form([]),  # multi-select values; empty = all billable
    date_from: str = Form(""),
    date_to: str = Form(""),
    discount: float = Form(0.0),
    foot_note: str = Form("Thank you for your business."),
    store: DataStore = Depends(get_data_store),
    # Manual tasks encoded as JSON string (for manual entry mode)
    manual_tasks_json: str = Form(""),
):
    from PyTM.core import data_handler as dh

    state = dh.load_data(settings.state_filepath)
    user = state.get("config", {}).get("user", {})
    invoice_config = state.get("config", {}).get("invoice", {})
    logo = invoice_config.get("logo", "")

    try:
        df = datetime.date.fromisoformat(date_from) if date_from else None
        dt = datetime.date.fromisoformat(date_to) if date_to else None
    except ValueError:
        return HTMLResponse("<p class='text-red-600'>Invalid date format. Use YYYY-MM-DD.</p>")

    data = store.load_data()

    # Build projects_data dict
    keys_list = [k.strip() for k in project_keys if k.strip()]
    if manual_tasks_json:
        import json
        try:
            manual_tasks = json.loads(manual_tasks_json)
        except ValueError:
            return HTMLResponse("<p class='text-red-600'>Invalid task data.</p>")
        projects_data = {
            "manual": {
                "meta": {"title": title, "client_name": "", "billable": True},
                "tasks": {
                    t["name"]: {
                        "created_at": datetime.datetime.now().isoformat(),
                        "status": settings.FINISHED,
                        "duration": float(t.get("hours", 0)) * 3600,
                        "description": t.get("description", ""),
                        "since": "",
                    }
                    for t in manual_tasks if t.get("name")
                },
            }
        }
    elif keys_list:
        missing = [k for k in keys_list if k not in data]
        if missing:
            return HTMLResponse(
                f"<p class='text-red-600'>Unknown project(s): {', '.join(missing)}</p>"
            )
        projects_data = {k: data[k] for k in keys_list}
    else:
        projects_data = data

    html, total = invoice_handler.generate_multi(
        projects_data, invoice_number, user, discount, title,
        date_from=df, date_to=dt, logo=logo, foot_note=foot_note,
    )

    if html is None:
        return HTMLResponse("<p class='text-yellow-600'>No billable tasks matched the filters.</p>")

    # Save to disk
    inv_dir = os.path.join(settings.data_folder, "invoices")
    os.makedirs(inv_dir, exist_ok=True)
    html_path = os.path.join(inv_dir, f"{title}.html")
    with open(html_path, "w") as f:
        f.write(html)

    # Preserve payment status/date if this invoice number already exists
    existing = store.load_invoices().get(invoice_number) or store.load_invoices().get(str(invoice_number))
    record = {
        "invoice_number": invoice_number,
        "title": title,
        "date_from": str(df) if df else None,
        "date_to": str(dt) if dt else None,
        "total": total,
        "foot_note": foot_note,
        "status": existing["status"] if existing else "unpaid",
        "paid_date": existing.get("paid_date") if existing else None,
        "created_at": existing.get("created_at", str(datetime.date.today())) if existing else str(datetime.date.today()),
    }
    store.save_invoice_record(record)

    invoices = store.load_invoices()
    return templates.TemplateResponse(
        "partials/invoice_list.html",
        {
            "request": request,
            "invoices": invoices,
            "flash": f"Invoice #{invoice_number} generated — ${total:,.2f}",
            "invoice_path": html_path,
        },
    )


# ── View invoice HTML ─────────────────────────────────────────────────────────

@router.get("/{invoice_number}/view", response_class=HTMLResponse)
async def view_invoice(invoice_number: str, store: DataStore = Depends(get_data_store)):
    invoices = store.load_invoices()
    record = invoices.get(invoice_number) or invoices.get(str(invoice_number))
    if not record:
        return HTMLResponse("<p style='font-family:sans-serif;padding:2rem'>Invoice not found.</p>", status_code=404)
    title = record.get("title", invoice_number)
    inv_path = os.path.join(settings.data_folder, "invoices", f"{title}.html")
    if not os.path.exists(inv_path):
        return HTMLResponse(
            f"<p style='font-family:sans-serif;padding:2rem'>Invoice file not found on disk: {inv_path}</p>",
            status_code=404,
        )
    with open(inv_path, encoding="utf-8") as f:
        return HTMLResponse(f.read())


# ── Mark paid ─────────────────────────────────────────────────────────────────

@router.post("/{invoice_number}/mark-paid", response_class=HTMLResponse)
async def mark_paid(
    request: Request,
    invoice_number: str,
    paid_date: str = Form(""),
    store: DataStore = Depends(get_data_store),
):
    date = paid_date or str(datetime.date.today())
    record = store.update_invoice_status(invoice_number, "paid", date)
    row_html = _render_row(request, record).body.decode()
    return HTMLResponse(row_html + oob_flash(f"Invoice #{invoice_number} marked as paid"))


# ── Write off ─────────────────────────────────────────────────────────────────

@router.post("/{invoice_number}/write-off", response_class=HTMLResponse)
async def write_off(
    request: Request,
    invoice_number: str,
    store: DataStore = Depends(get_data_store),
):
    record = store.update_invoice_status(invoice_number, "written_off")
    row_html = _render_row(request, record).body.decode()
    return HTMLResponse(row_html + oob_flash(f"Invoice #{invoice_number} written off", "warning"))
