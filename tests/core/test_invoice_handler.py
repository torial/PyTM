import datetime

import pytest

from PyTM.core import invoice_handler

TEST_TIME_NOW = datetime.datetime(2023, 11, 9)

USER = {
    "name": "Test User",
    "address": "123 Main St",
    "email": "test@example.com",
    "phone": "+1234567890",
    "website": "test.com",
    "hourly_rate": "100",
}

PROJECTS_MULTI = {
    "alpha": {
        "meta": {
            "title": "Alpha",
            "client_name": "Acme Corp",
            "client_address": "1 Corp Lane",
            "client_email": "acme@example.com",
        },
        "tasks": {
            "2026-01-10-design-work": {
                "created_at": "2026-01-10 09:00:00",
                "status": "finished",
                "duration": 3600.0,
                "description": "Initial design",
            },
            "2026-02-05-code-review": {
                "created_at": "2026-02-05 10:00:00",
                "status": "finished",
                "duration": 7200.0,
                "description": "Code review",
            },
            "2026-02-10-abandoned": {
                "created_at": "2026-02-10 10:00:00",
                "status": "aborted",
                "duration": 1800.0,
                "description": "Abandoned work",
            },
        },
    }
}


@pytest.fixture
def patch_datetime_now(monkeypatch):
    class mydatetime(datetime.datetime):
        @classmethod
        def now(cls):
            return TEST_TIME_NOW

    monkeypatch.setattr(invoice_handler.datetime, "datetime", mydatetime)


# ── format_task_name ───────────────────────────────────────────────────────────

def test_format_task_name_dated():
    assert invoice_handler.format_task_name("2026-03-16-initial-doc-review") == "3/16/2026 - Initial Doc Review"


def test_format_task_name_undated():
    result = invoice_handler.format_task_name("some-plain-task")
    assert result == "Some Plain Task"


def test_format_task_name_acronym_llm():
    result = invoice_handler.format_task_name("2026-01-01-llm-integration")
    assert "LLM" in result


def test_format_task_name_acronym_rag():
    result = invoice_handler.format_task_name("2026-01-01-rag-pipeline")
    assert "RAG" in result


def test_format_task_name_no_date_with_underscores():
    result = invoice_handler.format_task_name("task_with_underscores")
    assert result == "Task With Underscores"


# ── generate_multi ─────────────────────────────────────────────────────────────

def test_generate_multi_returns_tuple(patch_datetime_now):
    result = invoice_handler.generate_multi(PROJECTS_MULTI, "1", USER, 0, "Test Invoice")
    assert isinstance(result, tuple)
    assert len(result) == 2


def test_generate_multi_no_tasks_returns_none():
    empty = {"proj": {"meta": {}, "tasks": {}}}
    html, total = invoice_handler.generate_multi(empty, "1", USER, 0, "Empty")
    assert html is None
    assert total == 0.0


def test_generate_multi_aborted_tasks_excluded(patch_datetime_now):
    aborted_only = {
        "proj": {
            "meta": {},
            "tasks": {
                "2026-01-01-done": {"created_at": "2026-01-01 09:00:00", "status": "aborted", "duration": 3600.0},
            },
        }
    }
    html, total = invoice_handler.generate_multi(aborted_only, "1", USER, 0, "Test")
    assert html is None
    assert total == 0.0


def test_generate_multi_total_calculation(patch_datetime_now):
    # 1h + 2h = 3h @ $100/hr = $300
    html, total = invoice_handler.generate_multi(PROJECTS_MULTI, "1", USER, 0, "Test")
    assert total == pytest.approx(300.0)


def test_generate_multi_discount_applied(patch_datetime_now):
    html, total = invoice_handler.generate_multi(PROJECTS_MULTI, "1", USER, 50.0, "Test")
    assert total == pytest.approx(250.0)


def test_generate_multi_date_from_excludes_earlier(patch_datetime_now):
    date_from = datetime.date(2026, 2, 1)
    html, total = invoice_handler.generate_multi(PROJECTS_MULTI, "1", USER, 0, "Test", date_from=date_from)
    # Only the Feb 5 task (2h @ $100 = $200) should be included; Jan 10 excluded
    assert total == pytest.approx(200.0)


def test_generate_multi_date_to_excludes_later(patch_datetime_now):
    date_to = datetime.date(2026, 1, 31)
    html, total = invoice_handler.generate_multi(PROJECTS_MULTI, "1", USER, 0, "Test", date_to=date_to)
    # Only the Jan 10 task (1h @ $100 = $100) should be included
    assert total == pytest.approx(100.0)


def test_generate_multi_date_range_no_match(patch_datetime_now):
    date_from = datetime.date(2025, 1, 1)
    date_to = datetime.date(2025, 12, 31)
    html, total = invoice_handler.generate_multi(PROJECTS_MULTI, "1", USER, 0, "Test", date_from=date_from, date_to=date_to)
    assert html is None
    assert total == 0.0


def test_generate_multi_html_contains_invoice_number(patch_datetime_now):
    html, _ = invoice_handler.generate_multi(PROJECTS_MULTI, "42", USER, 0, "Test")
    assert "Invoice #42" in html


def test_generate_multi_html_contains_user_name(patch_datetime_now):
    html, _ = invoice_handler.generate_multi(PROJECTS_MULTI, "1", USER, 0, "Test")
    assert USER["name"] in html


def test_generate_multi_html_contains_client_name(patch_datetime_now):
    html, _ = invoice_handler.generate_multi(PROJECTS_MULTI, "1", USER, 0, "Test")
    assert "Acme Corp" in html


def test_generate_multi_html_contains_total(patch_datetime_now):
    html, total = invoice_handler.generate_multi(PROJECTS_MULTI, "1", USER, 0, "Test")
    assert "$300.00" in html


def test_generate_multi_includes_logo(patch_datetime_now):
    html, _ = invoice_handler.generate_multi(PROJECTS_MULTI, "1", USER, 0, "Test", logo="/path/to/logo.png")
    assert 'src="/path/to/logo.png"' in html


def test_generate_multi_no_logo_no_img_tag(patch_datetime_now):
    html, _ = invoice_handler.generate_multi(PROJECTS_MULTI, "1", USER, 0, "Test", logo=None)
    assert "<img" not in html


def test_generate_multi_custom_foot_note(patch_datetime_now):
    html, _ = invoice_handler.generate_multi(PROJECTS_MULTI, "1", USER, 0, "Test", foot_note="Net 30.")
    assert "Net 30." in html


def test_generate_multi_empty_foot_note_omitted(patch_datetime_now):
    html, _ = invoice_handler.generate_multi(PROJECTS_MULTI, "1", USER, 0, "Test", foot_note="")
    assert "Thank you for your business." not in html


def test_acronyms_use_settings(monkeypatch):
    import PyTM.settings as s
    monkeypatch.setattr(s, "ACRONYMS", {"API"})
    result = invoice_handler.format_task_name("2026-01-01-api-call")
    assert "API" in result


def test_generate_multi_skips_non_billable_project(patch_datetime_now):
    projects = {
        "billable": {
            "meta": {"billable": True, "title": "Billable", "client_name": ""},
            "tasks": {
                "2026-01-10-work": {
                    "created_at": "2026-01-10 09:00:00",
                    "status": "finished",
                    "duration": 3600.0,
                }
            },
        },
        "internal": {
            "meta": {"billable": False, "title": "Internal"},
            "tasks": {
                "2026-01-11-overhead": {
                    "created_at": "2026-01-11 09:00:00",
                    "status": "finished",
                    "duration": 7200.0,
                }
            },
        },
    }
    html, total = invoice_handler.generate_multi(projects, "1", USER, 0, "Test")
    # Only billable project (1h @ $100 = $100); non-billable 2h excluded
    assert total == pytest.approx(100.0)
    assert "Internal" not in html
