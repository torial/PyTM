import json

import pytest

from PyTM.core import data_handler


def test_init_data(tmpdir):
    tmp_path = tmpdir.join("pytm-test.json")
    data_handler.init_data(tmp_path)
    saved = json.loads(tmp_path.read())
    assert saved["_schema_version"] == 1
    assert {k: v for k, v in saved.items() if k != "_schema_version"} == {}


def test_load_data_exists(tmpdir):
    tmp_path = tmpdir.join("pytm-test.json")
    data = {"user": "test"}
    tmp_path.write(json.dumps(data))
    assert data_handler.load_data(tmp_path) == data


def test_load_data_doesnot_exists(tmpdir):
    tmp_path = tmpdir.join("pytm-test.json")
    assert data_handler.load_data(tmp_path) == {}


def test_save_data(tmpdir):
    tmp_path = tmpdir.join("pytm-test.json")
    data = {"user": "test"}
    data_handler.save_data(data, tmp_path)
    assert data_handler.load_data(tmp_path) == data


def test_update(tmpdir):
    f = lambda d: {"user": "test"}
    tmp_path = tmpdir.join("pytm-test.json")
    tmp_path.write("[]")
    data_handler.update(f, tmp_path)
    assert data_handler.load_data(tmp_path) == {"user": "test"}


# ── Invoice record functions ───────────────────────────────────────────────────

def test_load_invoices_not_exists(tmpdir):
    tmp_path = tmpdir.join("invoices.json")
    assert data_handler.load_invoices(tmp_path) == {}


def test_load_invoices_exists(tmpdir):
    tmp_path = tmpdir.join("invoices.json")
    records = {"1": {"invoice_number": "1", "title": "Jan", "total": 500.0, "status": "unpaid"}}
    tmp_path.write(json.dumps(records))
    assert data_handler.load_invoices(tmp_path) == records


def test_save_invoices(tmpdir):
    tmp_path = tmpdir.join("invoices.json")
    records = {"2": {"invoice_number": "2", "title": "Feb", "total": 1000.0, "status": "paid"}}
    data_handler.save_invoices(records, tmp_path)
    assert data_handler.load_invoices(tmp_path) == records


def test_save_invoice_record_new(tmpdir):
    tmp_path = tmpdir.join("invoices.json")
    record = {"invoice_number": "1", "title": "Test", "total": 420.0, "status": "unpaid", "paid_date": None}
    data_handler.save_invoice_record(record, tmp_path)
    saved = json.loads(tmp_path.read())
    assert saved["1"] == record


def test_save_invoice_record_upserts(tmpdir):
    tmp_path = tmpdir.join("invoices.json")
    old = {"1": {"invoice_number": "1", "title": "Old", "total": 100.0, "status": "unpaid"}}
    tmp_path.write(json.dumps(old))
    updated = {"invoice_number": "1", "title": "New", "total": 200.0, "status": "unpaid", "paid_date": None}
    data_handler.save_invoice_record(updated, tmp_path)
    saved = json.loads(tmp_path.read())
    assert saved["1"]["title"] == "New"
    assert saved["1"]["total"] == 200.0


def test_save_invoice_record_preserves_other_records(tmpdir):
    tmp_path = tmpdir.join("invoices.json")
    existing = {"1": {"invoice_number": "1", "title": "Existing", "total": 100.0, "status": "paid"}}
    tmp_path.write(json.dumps(existing))
    new_record = {"invoice_number": "2", "title": "New", "total": 500.0, "status": "unpaid", "paid_date": None}
    data_handler.save_invoice_record(new_record, tmp_path)
    saved = json.loads(tmp_path.read())
    assert "1" in saved
    assert "2" in saved


def test_update_invoice_status_existing(tmpdir):
    tmp_path = tmpdir.join("invoices.json")
    records = {"3": {"invoice_number": "3", "title": "Mar", "total": 300.0, "status": "unpaid", "paid_date": None}}
    tmp_path.write(json.dumps(records))
    result = data_handler.update_invoice_status("3", "paid", "2026-03-20", tmp_path)
    assert result["status"] == "paid"
    assert result["paid_date"] == "2026-03-20"
    saved = json.loads(tmp_path.read())
    assert saved["3"]["status"] == "paid"


def test_update_invoice_status_write_off(tmpdir):
    tmp_path = tmpdir.join("invoices.json")
    records = {"4": {"invoice_number": "4", "title": "Apr", "total": 400.0, "status": "unpaid", "paid_date": None}}
    tmp_path.write(json.dumps(records))
    result = data_handler.update_invoice_status("4", "written_off", path=tmp_path)
    assert result["status"] == "written_off"
    assert result["paid_date"] is None


def test_update_invoice_status_creates_stub_when_missing(tmpdir):
    tmp_path = tmpdir.join("invoices.json")
    result = data_handler.update_invoice_status("99", "paid", "2026-01-01", tmp_path)
    assert result["invoice_number"] == "99"
    assert result["status"] == "paid"
    assert result["paid_date"] == "2026-01-01"
    saved = json.loads(tmp_path.read())
    assert "99" in saved


# ── Archive functions ─────────────────────────────────────────────────────────

def test_load_archive_not_exists(tmpdir):
    tmp_path = tmpdir.join("archive.json")
    assert data_handler.load_archive(tmp_path) == {}


def test_load_archive_exists(tmpdir):
    tmp_path = tmpdir.join("archive.json")
    data = {"alpha": [{"archived_at": "2026-03-20T10:00:00", "data": {"tasks": {}}}]}
    tmp_path.write(json.dumps(data))
    assert data_handler.load_archive(tmp_path) == data


def test_archive_project_creates_entry(tmpdir):
    tmp_path = tmpdir.join("archive.json")
    project_data = {"tasks": {"t1": {"status": "finished", "duration": 3600}}}
    data_handler.archive_project("alpha", project_data, tmp_path)
    archive = json.loads(tmp_path.read())
    assert "alpha" in archive
    assert len(archive["alpha"]) == 1
    assert archive["alpha"][0]["data"] == project_data
    assert "archived_at" in archive["alpha"][0]


def test_archive_project_appends_multiple_snapshots(tmpdir):
    tmp_path = tmpdir.join("archive.json")
    data_handler.archive_project("alpha", {"tasks": {}}, tmp_path)
    data_handler.archive_project("alpha", {"tasks": {"new": {}}}, tmp_path)
    archive = json.loads(tmp_path.read())
    assert len(archive["alpha"]) == 2


def test_archive_project_multiple_names(tmpdir):
    tmp_path = tmpdir.join("archive.json")
    data_handler.archive_project("alpha", {"tasks": {}}, tmp_path)
    data_handler.archive_project("beta", {"tasks": {}}, tmp_path)
    archive = json.loads(tmp_path.read())
    assert "alpha" in archive
    assert "beta" in archive


def test_pop_archived_project_returns_most_recent(tmpdir):
    tmp_path = tmpdir.join("archive.json")
    data_handler.archive_project("alpha", {"tasks": {"old": {}}}, tmp_path)
    data_handler.archive_project("alpha", {"tasks": {"new": {}}}, tmp_path)
    snapshot = data_handler.pop_archived_project("alpha", tmp_path)
    assert snapshot["data"] == {"tasks": {"new": {}}}


def test_pop_archived_project_removes_entry(tmpdir):
    tmp_path = tmpdir.join("archive.json")
    data_handler.archive_project("alpha", {"tasks": {}}, tmp_path)
    data_handler.pop_archived_project("alpha", tmp_path)
    archive = json.loads(tmp_path.read())
    assert "alpha" not in archive


def test_pop_archived_project_leaves_older_snapshots(tmpdir):
    tmp_path = tmpdir.join("archive.json")
    data_handler.archive_project("alpha", {"tasks": {"first": {}}}, tmp_path)
    data_handler.archive_project("alpha", {"tasks": {"second": {}}}, tmp_path)
    data_handler.pop_archived_project("alpha", tmp_path)
    archive = json.loads(tmp_path.read())
    assert len(archive["alpha"]) == 1
    assert archive["alpha"][0]["data"] == {"tasks": {"first": {}}}


def test_pop_archived_project_not_found_returns_none(tmpdir):
    tmp_path = tmpdir.join("archive.json")
    assert data_handler.pop_archived_project("nonexistent", tmp_path) is None


def test_save_data_saves_empty_dict(tmpdir):
    tmp_path = tmpdir.join("data.json")
    data_handler.save_data({}, tmp_path)
    assert data_handler.load_data(tmp_path) == {}


def test_update_invoice_status_no_paid_date_unchanged(tmpdir):
    tmp_path = tmpdir.join("invoices.json")
    records = {"5": {"invoice_number": "5", "title": "May", "total": 50.0, "status": "unpaid", "paid_date": "2026-02-01"}}
    tmp_path.write(json.dumps(records))
    result = data_handler.update_invoice_status("5", "written_off", path=tmp_path)
    # paid_date not passed — existing value should be preserved
    assert result["paid_date"] == "2026-02-01"
