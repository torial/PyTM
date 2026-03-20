"""
DataStore — the sole gateway between web routes and the filesystem.

All file I/O is serialised through a threading.Lock so that concurrent
HTTP requests from the same browser session cannot interleave reads and
writes. The web server is intentionally launched with workers=1, which
makes a threading.Lock sufficient (no need for cross-process file locks).
"""
import os
import threading
from functools import partial
from typing import Optional

from PyTM import settings
from PyTM.core import data_handler, project_handler, task_handler


class DataStore:
    def __init__(self, data_folder: str):
        self._folder = data_folder
        self._lock = threading.Lock()
        self._data_path = os.path.join(data_folder, settings.data_filename)
        self._state_path = os.path.join(data_folder, settings.state_filename)
        self._invoices_path = os.path.join(data_folder, settings.invoices_filename)
        self._archive_path = os.path.join(data_folder, settings.archive_filename)

    # ── Projects / Tasks (data.json) ─────────────────────────────────────────

    def load_data(self) -> dict:
        return data_handler.load_data(self._data_path)

    def update(self, fn) -> None:
        with self._lock:
            data = data_handler.load_data(self._data_path)
            data_handler.save_data(fn(data), self._data_path)

    # ── Invoices ──────────────────────────────────────────────────────────────

    def load_invoices(self) -> dict:
        return data_handler.load_invoices(self._invoices_path)

    def save_invoice_record(self, record: dict) -> None:
        with self._lock:
            data_handler.save_invoice_record(record, self._invoices_path)

    def update_invoice_status(
        self, invoice_number: str, status: str, paid_date: Optional[str] = None
    ) -> dict:
        with self._lock:
            return data_handler.update_invoice_status(
                invoice_number, status, paid_date, self._invoices_path
            )

    # ── Archive ───────────────────────────────────────────────────────────────

    def load_archive(self) -> dict:
        return data_handler.load_archive(self._archive_path)

    def archive_project(self, project_name: str, project_data: dict) -> None:
        with self._lock:
            data_handler.archive_project(project_name, project_data, self._archive_path)

    def pop_archived_project(self, project_name: str) -> Optional[dict]:
        with self._lock:
            return data_handler.pop_archived_project(project_name, self._archive_path)


# ── Singleton + FastAPI dependency injection ──────────────────────────────────

_store: Optional[DataStore] = None


def set_data_store(store: DataStore) -> None:
    global _store
    _store = store


def get_data_store() -> DataStore:
    if _store is None:
        raise RuntimeError("DataStore not initialised — call set_data_store() first.")
    return _store
