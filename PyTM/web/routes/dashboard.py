from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from PyTM.web.app import templates
from PyTM.web.dependencies import DataStore, get_data_store
from PyTM.web.routes._helpers import active_session

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, store: DataStore = Depends(get_data_store)):
    data = store.load_data()
    active = active_session(request)
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "projects": data, "active": active},
    )
