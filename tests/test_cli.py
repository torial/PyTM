"""
Tests for `PyTM` module.
"""
import json
from unittest.mock import patch, MagicMock

import pytest

from PyTM import __version__
from PyTM.cli import cli
from PyTM.commands.project import get_duration_str
from PyTM.core import data_handler
from click.testing import CliRunner


# ── Fixtures ──────────────────────────────────────────────────────────────────

SAMPLE_STATE = {
    "config": {
        "user": {
            "name": "Test User",
            "address": "123 Main St",
            "email": "test@example.com",
            "phone": "+1234567890",
            "website": "test.com",
            "hourly_rate": "100",
        },
        "invoice": {"invoice_number": "5"},
    }
}

SAMPLE_PROJECTS = {
    "alpha": {
        "meta": {"title": "Alpha", "client_name": "Acme", "client_address": "", "client_email": ""},
        "tasks": {
            "2026-01-10-design": {
                "created_at": "2026-01-10 09:00:00",
                "status": "finished",
                "duration": 3600.0,
                "description": "Design work",
            }
        },
    }
}

SAMPLE_INVOICES = {
    "1": {
        "invoice_number": "1",
        "title": "Invoice-Jan",
        "date_from": "2026-01-01",
        "date_to": "2026-01-31",
        "total": 420.0,
        "status": "unpaid",
        "paid_date": None,
        "created_at": "2026-02-01",
    },
    "2": {
        "invoice_number": "2",
        "title": "Invoice-Feb",
        "date_from": "2026-02-01",
        "date_to": "2026-02-28",
        "total": 630.0,
        "status": "paid",
        "paid_date": "2026-03-01",
        "created_at": "2026-03-01",
    },
}


# ── Basic CLI ─────────────────────────────────────────────────────────────────

def test_help_exit_successfully():
    runner = CliRunner()
    result = runner.invoke(cli, args=["--help"])
    assert result.exit_code == 0


def test_help_output():
    runner = CliRunner()
    result = runner.invoke(cli, args=["--help"])
    assert "Options" in result.output


def test_version():
    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])
    assert __version__ in result.output
    assert result.exit_code == 0
    result = runner.invoke(cli, ["--v"])
    assert __version__ in result.output
    assert result.exit_code == 0
    result = runner.invoke(cli, ["-v"])
    assert __version__ in result.output
    assert result.exit_code == 0


def test_command_project():
    runner = CliRunner()
    result = runner.invoke(cli, ["project", "--help"])
    assert result.exit_code == 0
    assert "Commands" in result.output


def test_command_task():
    runner = CliRunner()
    result = runner.invoke(cli, ["task", "--help"])
    assert result.exit_code == 0
    assert "Commands" in result.output


def test_command_invoice():
    runner = CliRunner()
    result = runner.invoke(cli, ["invoice", "--help"])
    assert result.exit_code == 0
    assert "Commands" in result.output


# ── invoice generate ──────────────────────────────────────────────────────────

def test_invoice_generate_no_tasks_warns(tmp_path):
    runner = CliRunner()
    with patch("PyTM.cli.data_handler.load_data", side_effect=[{}, SAMPLE_STATE]), \
         patch("PyTM.cli.settings.data_folder", str(tmp_path)):
        result = runner.invoke(cli, ["invoice", "generate", "--from", "2026-01-01", "--to", "2026-01-31"])
    assert result.exit_code == 0
    assert "No tasks found" in result.output


def test_invoice_generate_writes_file(tmp_path):
    runner = CliRunner()
    (tmp_path / "invoices").mkdir()
    with patch("PyTM.cli.data_handler.load_data", side_effect=[SAMPLE_PROJECTS, SAMPLE_STATE]), \
         patch("PyTM.cli.data_handler.save_invoice_record"), \
         patch("PyTM.cli.settings.data_folder", str(tmp_path)), \
         patch("PyTM.cli.webbrowser.open"):
        result = runner.invoke(cli, ["invoice", "generate", "--from", "2026-01-01", "--to", "2026-01-31", "--title", "TestInvoice"])
    assert result.exit_code == 0
    assert (tmp_path / "invoices" / "TestInvoice.html").exists()


def test_invoice_generate_saves_record(tmp_path):
    runner = CliRunner()
    (tmp_path / "invoices").mkdir()
    saved_records = []

    def capture_record(record, *args, **kwargs):
        saved_records.append(record)

    with patch("PyTM.cli.data_handler.load_data", side_effect=[SAMPLE_PROJECTS, SAMPLE_STATE]), \
         patch("PyTM.cli.data_handler.save_invoice_record", side_effect=capture_record), \
         patch("PyTM.cli.settings.data_folder", str(tmp_path)), \
         patch("PyTM.cli.webbrowser.open"):
        runner.invoke(cli, ["invoice", "generate", "--from", "2026-01-01", "--to", "2026-01-31",
                             "--invoice-number", "7", "--title", "TestInvoice"])

    assert len(saved_records) == 1
    assert saved_records[0]["invoice_number"] == "7"
    assert saved_records[0]["status"] == "unpaid"
    assert saved_records[0]["total"] == pytest.approx(100.0)


def test_invoice_generate_invalid_date():
    runner = CliRunner()
    result = runner.invoke(cli, ["invoice", "generate", "--from", "not-a-date"])
    assert result.exit_code == 0
    assert "Invalid date" in result.output


def test_invoice_generate_unknown_project():
    runner = CliRunner()
    with patch("PyTM.cli.data_handler.load_data", side_effect=[SAMPLE_PROJECTS, SAMPLE_STATE]):
        result = runner.invoke(cli, ["invoice", "generate", "--projects", "nonexistent"])
    assert result.exit_code == 0
    assert "Unknown project" in result.output


# ── invoice mark-paid ─────────────────────────────────────────────────────────

def test_invoice_mark_paid(tmp_path):
    inv_file = tmp_path / "invoices.json"
    inv_file.write_text(json.dumps(SAMPLE_INVOICES))
    runner = CliRunner()
    real_fn = data_handler.update_invoice_status  # capture before patching to avoid recursion
    with patch("PyTM.cli.data_handler.update_invoice_status",
               side_effect=lambda num, status, paid_date=None: real_fn(num, status, paid_date, inv_file)):
        result = runner.invoke(cli, ["invoice", "mark-paid", "1"])
    assert result.exit_code == 0
    assert "marked as paid" in result.output


def test_invoice_mark_paid_with_explicit_date(tmp_path):
    inv_file = tmp_path / "invoices.json"
    inv_file.write_text(json.dumps({"3": {"invoice_number": "3", "title": "Mar", "total": 100.0, "status": "unpaid", "paid_date": None}}))
    saved = {}

    def capture(num, status, paid_date=None, path=None):
        saved["paid_date"] = paid_date
        return {"invoice_number": num, "title": "Mar", "status": status, "paid_date": paid_date}

    runner = CliRunner()
    with patch("PyTM.cli.data_handler.update_invoice_status", side_effect=capture):
        result = runner.invoke(cli, ["invoice", "mark-paid", "3", "--date", "2026-02-15"])
    assert result.exit_code == 0
    assert saved["paid_date"] == "2026-02-15"
    assert "2026-02-15" in result.output


# ── invoice write-off ─────────────────────────────────────────────────────────

def test_invoice_write_off(tmp_path):
    inv_file = tmp_path / "invoices.json"
    inv_file.write_text(json.dumps(SAMPLE_INVOICES))
    runner = CliRunner()
    real_fn = data_handler.update_invoice_status  # capture before patching to avoid recursion
    with patch("PyTM.cli.data_handler.update_invoice_status",
               side_effect=lambda num, status, paid_date=None: real_fn(num, status, paid_date, inv_file)):
        result = runner.invoke(cli, ["invoice", "write-off", "1"])
    assert result.exit_code == 0
    assert "written off" in result.output


# ── invoice status ────────────────────────────────────────────────────────────

def test_invoice_status_empty():
    runner = CliRunner()
    with patch("PyTM.cli.data_handler.load_invoices", return_value={}):
        result = runner.invoke(cli, ["invoice", "status"])
    assert result.exit_code == 0
    assert "No invoices recorded" in result.output


def test_invoice_status_shows_invoices():
    runner = CliRunner()
    with patch("PyTM.cli.data_handler.load_invoices", return_value=SAMPLE_INVOICES):
        result = runner.invoke(cli, ["invoice", "status"])
    assert result.exit_code == 0
    assert "Invoice-Jan" in result.output
    assert "Invoice-Feb" in result.output


def test_invoice_status_shows_totals():
    runner = CliRunner()
    with patch("PyTM.cli.data_handler.load_invoices", return_value=SAMPLE_INVOICES):
        result = runner.invoke(cli, ["invoice", "status"])
    assert result.exit_code == 0
    # $630 paid, $420 unpaid
    assert "630.00" in result.output
    assert "420.00" in result.output


def test_invoice_status_shows_status_labels():
    runner = CliRunner()
    with patch("PyTM.cli.data_handler.load_invoices", return_value=SAMPLE_INVOICES):
        result = runner.invoke(cli, ["invoice", "status"])
    assert result.exit_code == 0
    assert "paid" in result.output
    assert "unpaid" in result.output


# ── project soft-delete / archive / recover ───────────────────────────────────

def test_project_remove_archives_project(tmp_path):
    archive_file = tmp_path / "archive.json"
    runner = CliRunner()

    def load_data_side_effect(path=None):
        # Second call uses state_filepath; first call uses data_filepath (no arg)
        if path is not None:
            return {"current_project": "", "current_task": ""}
        return dict(SAMPLE_PROJECTS)

    real_archive = data_handler.archive_project
    with patch("PyTM.commands.project.data_handler.load_data", side_effect=load_data_side_effect), \
         patch("PyTM.commands.project.data_handler.archive_project",
               side_effect=lambda name, proj_data, path=None: real_archive(name, proj_data, archive_file)), \
         patch("PyTM.commands.project.data_handler.update"), \
         patch("PyTM.commands.project.data_handler.save_data"):
        result = runner.invoke(cli, ["project", "remove", "alpha"])
    assert result.exit_code == 0
    assert "archived" in result.output
    archive = json.loads(archive_file.read_text())
    assert "alpha" in archive


def test_project_remove_nonexistent_warns():
    runner = CliRunner()
    with patch("PyTM.commands.project.data_handler.load_data", return_value={}), \
         patch("PyTM.commands.project.data_handler.load_data", return_value=SAMPLE_PROJECTS):
        result = runner.invoke(cli, ["project", "remove", "nonexistent"])
    assert result.exit_code == 0


def test_project_archived_empty():
    runner = CliRunner()
    with patch("PyTM.commands.project.data_handler.load_archive", return_value={}):
        result = runner.invoke(cli, ["project", "archived"])
    assert result.exit_code == 0
    assert "No archived" in result.output


def test_project_archived_shows_entries():
    archive = {
        "alpha": [{"archived_at": "2026-03-20T10:00:00", "data": {"tasks": {}}}],
        "beta": [
            {"archived_at": "2026-02-01T08:00:00", "data": {"tasks": {}}},
            {"archived_at": "2026-03-01T09:00:00", "data": {"tasks": {}}},
        ],
    }
    runner = CliRunner()
    with patch("PyTM.commands.project.data_handler.load_archive", return_value=archive):
        result = runner.invoke(cli, ["project", "archived"])
    assert result.exit_code == 0
    assert "alpha" in result.output
    assert "beta" in result.output


def test_project_recover_restores(tmp_path):
    archive = {"alpha": [{"archived_at": "2026-03-20T10:00:00", "data": SAMPLE_PROJECTS["alpha"]}]}
    archive_file = tmp_path / "archive.json"
    archive_file.write_text(json.dumps(archive))
    saved = {}

    def capture_save(data, path=None):
        saved["data"] = data

    runner = CliRunner()
    real_pop = data_handler.pop_archived_project
    with patch("PyTM.commands.project.data_handler.load_data", return_value={}), \
         patch("PyTM.commands.project.data_handler.pop_archived_project",
               side_effect=lambda name, path=None: real_pop(name, archive_file)), \
         patch("PyTM.commands.project.data_handler.save_data", side_effect=capture_save):
        result = runner.invoke(cli, ["project", "recover", "alpha"])
    assert result.exit_code == 0
    assert "restored" in result.output
    assert "alpha" in saved.get("data", {})


def test_project_recover_conflict_warns():
    runner = CliRunner()
    with patch("PyTM.commands.project.data_handler.load_data", return_value=SAMPLE_PROJECTS):
        result = runner.invoke(cli, ["project", "recover", "alpha"])
    assert result.exit_code == 0
    assert "already exists" in result.output


def test_project_recover_not_in_archive():
    runner = CliRunner()
    real_pop = data_handler.pop_archived_project
    with patch("PyTM.commands.project.data_handler.load_data", return_value={}), \
         patch("PyTM.commands.project.data_handler.pop_archived_project", return_value=None):
        result = runner.invoke(cli, ["project", "recover", "ghost"])
    assert result.exit_code == 0
    assert "No archived snapshot" in result.output


# ── get_duration_str boundary ─────────────────────────────────────────────────

def test_get_duration_str_exactly_60_minutes():
    # 3600 seconds == exactly 60 minutes — must be reported as "1 hours 00 mins 00 secs"
    # (previously the m > 60 bug would fall through to "mm mins ss secs" at 60 minutes)
    result = get_duration_str(3600)
    assert "hours" in result
    assert "1" in result


def test_get_duration_str_59_minutes():
    result = get_duration_str(59 * 60)
    assert "mins" in result
    assert "hours" not in result


def test_get_duration_str_under_1_minute():
    result = get_duration_str(45)
    assert "seconds" in result


# ── task backfill ─────────────────────────────────────────────────────────────

def test_task_backfill_rejects_negative_hours(tmp_path):
    runner = CliRunner()
    state = {"current_project": "alpha", "current_task": ""}
    data = dict(SAMPLE_PROJECTS)
    with patch("PyTM.commands.task.data_handler.load_data", return_value=data), \
         patch("PyTM.commands.task.data_handler.save_data"), \
         patch("PyTM.commands.task.data_handler.update"):
        result = runner.invoke(cli, [
            "task", "backfill", "alpha", "bad-entry",
            "--date", "2026-03-01", "--hours", "-1"
        ])
    assert result.exit_code == 0
    assert "Hours must be 0 or greater" in result.output


def test_task_backfill_rejects_invalid_date(tmp_path):
    runner = CliRunner()
    data = dict(SAMPLE_PROJECTS)
    with patch("PyTM.commands.task.data_handler.load_data", return_value=data):
        result = runner.invoke(cli, [
            "task", "backfill", "alpha", "some-entry",
            "--date", "not-a-date", "--hours", "1"
        ])
    assert result.exit_code == 0
    assert "Invalid date" in result.output


# ── invoice auto saves record ─────────────────────────────────────────────────

def test_invoice_auto_saves_record(tmp_path):
    runner = CliRunner()
    (tmp_path / "invoices").mkdir()
    saved_records = []

    def capture_record(record, *args, **kwargs):
        saved_records.append(record)

    state = {
        "config": {
            "user": {"name": "T", "email": "", "phone": "", "address": "", "website": "", "hourly_rate": "100"},
            "invoice": {"invoice_number": "10", "title": "AutoTest", "foot_note": "", "logo": ""},
        }
    }
    project_data = {
        "proj": {
            "meta": {"title": "Proj", "client_name": "Client", "client_address": "", "client_email": ""},
            "tasks": {
                "2026-01-15-work": {
                    "created_at": "2026-01-15 09:00:00",
                    "status": "finished",
                    "duration": 3600.0,
                    "description": "Work",
                }
            },
        }
    }

    inputs = "\n".join([
        "10",       # invoice number
        "AutoTest", # title
        "",         # foot note
        "",         # logo
        "Proj",     # project name
        "T",        # your name
        "",         # email
        "",         # phone
        "",         # address
        "",         # website
        "100",      # hourly rate
        "Client",   # bill to name
        "",         # address
        "",         # phone
        "",         # email
        "",         # website
        "",         # discount
    ]) + "\n"

    with patch("PyTM.cli.data_handler.load_data", side_effect=[state, project_data]), \
         patch("PyTM.cli.data_handler.save_data"), \
         patch("PyTM.cli.data_handler.save_invoice_record", side_effect=capture_record), \
         patch("PyTM.cli.settings.data_folder", str(tmp_path)), \
         patch("PyTM.cli.webbrowser.open"):
        result = runner.invoke(cli, ["invoice", "auto", "proj"], input=inputs)

    assert len(saved_records) == 1, f"Expected 1 saved record, got {len(saved_records)}. Output: {result.output}"
    assert saved_records[0]["status"] == "unpaid"
    assert saved_records[0]["total"] == pytest.approx(100.0)
