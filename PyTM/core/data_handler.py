import datetime
import json

from PyTM import settings


# ── Schema versioning helpers ─────────────────────────────────────────────────

def _migrate(data, from_version):
    """Apply schema migrations from from_version up to SCHEMA_VERSION.

    No-op at version 1. Add migration steps here as the schema evolves:
        if from_version < 2:
            # transform data for v1 → v2
            from_version = 2
    """
    return data


def _versioned(data):
    """Wrap a data dict with the current schema version for serialisation."""
    return {"_schema_version": settings.SCHEMA_VERSION, **data}


def _strip_version(raw):
    """Remove _schema_version from a loaded dict, returning (data, version)."""
    if not isinstance(raw, dict):
        return raw, 0
    version = raw.pop("_schema_version", 0)
    return raw, version


# ── Core data / state ─────────────────────────────────────────────────────────

def init_data(path=settings.data_filepath, data={}):
    """Creates the data file at the given path."""
    with open(path, "w") as f:
        json.dump(_versioned(data), f)


def load_data(path=settings.data_filepath):
    """Loads and migrates data from the given path."""
    try:
        with open(path, "r") as f:
            raw = json.load(f)
    except FileNotFoundError:
        return {}
    data, version = _strip_version(raw)
    if version < settings.SCHEMA_VERSION:
        data = _migrate(data, version)
    return data


def save_data(data, path=settings.data_filepath):
    """Saves data to the given path, stamping the current schema version."""
    if data is not None:
        with open(path, "w") as f:
            json.dump(_versioned(data), f)


def update(func, path=settings.data_filepath):
    """Load → transform → save."""
    data = load_data(path)
    save_data(func(data), path)


# ── Invoice records ───────────────────────────────────────────────────────────

def load_invoices(path=settings.invoices_filepath):
    """Load invoice records from invoices.json."""
    try:
        with open(path, "r") as f:
            raw = json.load(f)
    except FileNotFoundError:
        return {}
    data, version = _strip_version(raw)
    if version < settings.SCHEMA_VERSION:
        data = _migrate(data, version)
    return data


def save_invoices(invoices, path=settings.invoices_filepath):
    """Save invoice records to invoices.json."""
    with open(path, "w") as f:
        json.dump(_versioned(invoices), f, indent=2)


def save_invoice_record(record, path=settings.invoices_filepath):
    """Upsert an invoice record keyed by invoice_number."""
    invoices = load_invoices(path)
    invoices[record["invoice_number"]] = record
    save_invoices(invoices, path)


def update_invoice_status(invoice_number, status, paid_date=None, path=settings.invoices_filepath):
    """Update status of an existing invoice record, creating a stub if missing.

    Returns the updated record.
    """
    invoices = load_invoices(path)
    if invoice_number not in invoices:
        invoices[invoice_number] = {
            "invoice_number": invoice_number,
            "title": "",
            "date_from": None,
            "date_to": None,
            "total": 0.0,
            "status": status,
            "paid_date": paid_date,
            "created_at": None,
        }
    else:
        invoices[invoice_number]["status"] = status
        if paid_date:
            invoices[invoice_number]["paid_date"] = paid_date
    save_invoices(invoices, path)
    return invoices[invoice_number]


# ── Archive ───────────────────────────────────────────────────────────────────

def load_archive(path=settings.archive_filepath):
    """Load archived projects. Returns dict keyed by project name, values are lists of snapshots."""
    try:
        with open(path, "r") as f:
            raw = json.load(f)
    except FileNotFoundError:
        return {}
    data, version = _strip_version(raw)
    if version < settings.SCHEMA_VERSION:
        data = _migrate(data, version)
    return data


def save_archive(archive, path=settings.archive_filepath):
    """Persist the archive to disk."""
    with open(path, "w") as f:
        json.dump(_versioned(archive), f, indent=2)


def archive_project(project_name, project_data, path=settings.archive_filepath):
    """Append a snapshot of project_data to the archive under project_name."""
    archive = load_archive(path)
    if project_name not in archive:
        archive[project_name] = []
    archive[project_name].append({
        "archived_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "data": project_data,
    })
    save_archive(archive, path)


def pop_archived_project(project_name, path=settings.archive_filepath):
    """Remove and return the most recent archived snapshot for project_name.

    Returns the snapshot dict (with 'archived_at' and 'data' keys), or None if not found.
    """
    archive = load_archive(path)
    entries = archive.get(project_name)
    if not entries:
        return None
    snapshot = entries.pop()
    if not entries:
        del archive[project_name]
    save_archive(archive, path)
    return snapshot
