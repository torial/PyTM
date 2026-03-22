"""
FastAPI application factory.

Usage:
    from PyTM.web.app import create_app
    app = create_app()          # uses settings.data_folder
    app = create_app("/tmp/d")  # test override
"""
import os
from typing import Optional

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from PyTM import settings
from PyTM.web.dependencies import DataStore, set_data_store

# Resolve paths relative to this file so they work regardless of cwd.
_HERE = os.path.dirname(__file__)
TEMPLATES_DIR = os.path.join(_HERE, "templates")
STATIC_DIR = os.path.join(_HERE, "static")

templates = Jinja2Templates(directory=TEMPLATES_DIR)


def create_app(data_folder: Optional[str] = None) -> FastAPI:
    from PyTM.web.routes import dashboard, projects, tasks, invoices

    app = FastAPI(title="PyTM", docs_url=None, redoc_url=None)

    # Session middleware — signs cookie with a secret key so it cannot be
    # tampered with. For a localhost personal tool the default key is fine;
    # override via PYTM_SECRET env var for any shared deployment.
    secret = os.environ.get("PYTM_SECRET", "pytm-local-dev-secret-do-not-deploy")
    app.add_middleware(SessionMiddleware, secret_key=secret, https_only=False)

    # Initialise the DataStore singleton for this process.
    store = DataStore(data_folder or settings.data_folder)
    set_data_store(store)

    # Static assets (htmx.min.js, alpine.min.js, tailwind.js, pytm.css)
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    # Routers
    app.include_router(dashboard.router)
    app.include_router(projects.router)
    app.include_router(tasks.router)
    app.include_router(invoices.router)

    return app
