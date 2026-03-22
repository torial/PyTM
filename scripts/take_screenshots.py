"""
Take PyTM screenshots using dummy data.

Backs up ~/.pytm, installs fake data, starts the dev server, captures
all screenshots, then restores the original data.
"""

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
HOME = Path.home()
PYTM_DIR = HOME / ".pytm"
BACKUP_DIR = HOME / ".pytm_screenshot_backup"
INVOICES_DIR = PYTM_DIR / "invoices"
OUT_DIR = Path(__file__).parent.parent / "ext" / "images"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Dummy data
# ---------------------------------------------------------------------------
NOW = "2026-03-15T10:00:00"

DATA = {
    "_schema_version": 1,
    "acme-website": {
        "name": "acme-website",
        "meta": {
            "title": "Acme Corp — Website Redesign",
            "client": "Acme Corporation",
            "hourly_rate": 120,
            "billable": True,
        },
        "status": "paused",
        "tasks": {
            "discovery": {
                "name": "discovery",
                "status": "finished",
                "duration": 5400,
                "start": "2026-03-01T09:00:00",
                "end": "2026-03-01T10:30:00",
                "description": "Kickoff and requirements gathering",
            },
            "wireframes": {
                "name": "wireframes",
                "status": "finished",
                "duration": 10800,
                "start": "2026-03-03T09:00:00",
                "end": "2026-03-03T12:00:00",
                "description": "Home, about, and contact wireframes",
            },
            "frontend-build": {
                "name": "frontend-build",
                "status": "paused",
                "duration": 7200,
                "start": "2026-03-10T13:00:00",
                "end": None,
                "description": "",
            },
        },
        "created": "2026-03-01T08:00:00",
        "updated": "2026-03-15T09:45:00",
    },
    "beta-api": {
        "name": "beta-api",
        "meta": {
            "title": "Beta Labs — REST API",
            "client": "Beta Labs",
            "hourly_rate": 150,
            "billable": True,
        },
        "status": "running",
        "tasks": {
            "auth-module": {
                "name": "auth-module",
                "status": "finished",
                "duration": 14400,
                "start": "2026-02-20T09:00:00",
                "end": "2026-02-20T13:00:00",
                "description": "JWT auth and refresh token logic",
            },
            "endpoint-design": {
                "name": "endpoint-design",
                "status": "running",
                "duration": 3600,
                "start": "2026-03-15T09:00:00",
                "end": None,
                "description": "",
            },
        },
        "created": "2026-02-18T08:00:00",
        "updated": "2026-03-15T09:00:00",
    },
    "gamma-dashboard": {
        "name": "gamma-dashboard",
        "meta": {
            "title": "Gamma Analytics Dashboard",
            "client": "Gamma Inc",
            "hourly_rate": 100,
            "billable": True,
        },
        "status": "finished",
        "tasks": {
            "data-model": {
                "name": "data-model",
                "status": "finished",
                "duration": 9000,
                "start": "2026-01-10T09:00:00",
                "end": "2026-01-10T11:30:00",
                "description": "",
            },
            "chart-components": {
                "name": "chart-components",
                "status": "finished",
                "duration": 18000,
                "start": "2026-01-15T09:00:00",
                "end": "2026-01-15T14:00:00",
                "description": "Bar, line, and pie chart components",
            },
            "export-feature": {
                "name": "export-feature",
                "status": "finished",
                "duration": 7200,
                "start": "2026-01-20T10:00:00",
                "end": "2026-01-20T12:00:00",
                "description": "CSV and PDF export",
            },
        },
        "created": "2026-01-08T08:00:00",
        "updated": "2026-01-22T15:00:00",
    },
    "internal-tools": {
        "name": "internal-tools",
        "meta": {
            "title": "Internal Tooling",
            "client": "",
            "hourly_rate": 0,
            "billable": False,
        },
        "status": "paused",
        "tasks": {
            "ci-pipeline": {
                "name": "ci-pipeline",
                "status": "paused",
                "duration": 5400,
                "start": "2026-03-12T14:00:00",
                "end": None,
                "description": "GitHub Actions workflow",
            },
        },
        "created": "2026-03-12T13:00:00",
        "updated": "2026-03-12T15:30:00",
    },
}

STATE = {
    "_schema_version": 1,
    "current_project": "beta-api",
    "current_task": "endpoint-design",
}

INVOICES = {
    "_schema_version": 1,
    "1": {
        "invoice_number": 1,
        "title": "Gamma Analytics — January 2026",
        "projects": ["gamma-dashboard"],
        "from_date": "2026-01-01",
        "to_date": "2026-01-31",
        "total": 3400.00,
        "status": "paid",
        "paid_date": "2026-02-10",
        "discount": 0,
        "foot_note": "Net 30",
        "file": str(INVOICES_DIR / "invoice-001.html"),
        "created": "2026-02-01T10:00:00",
    },
    "2": {
        "invoice_number": 2,
        "title": "Beta Labs — February 2026",
        "projects": ["beta-api"],
        "from_date": "2026-02-01",
        "to_date": "2026-02-28",
        "total": 2160.00,
        "status": "unpaid",
        "paid_date": None,
        "discount": 0,
        "foot_note": "Net 30",
        "file": str(INVOICES_DIR / "invoice-002.html"),
        "created": "2026-03-01T09:00:00",
    },
    "3": {
        "invoice_number": 3,
        "title": "Acme Corp — March 2026 (partial)",
        "projects": ["acme-website"],
        "from_date": "2026-03-01",
        "to_date": "2026-03-15",
        "total": 2760.00,
        "status": "unpaid",
        "paid_date": None,
        "discount": 10,
        "foot_note": "10% early-project discount applied",
        "file": str(INVOICES_DIR / "invoice-003.html"),
        "created": "2026-03-15T08:00:00",
    },
}

INVOICE_HTML = """<!DOCTYPE html><html><body>
<h1>Invoice #{num}</h1><p>Dummy invoice for screenshots.</p>
</body></html>"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def write_dummy_data():
    PYTM_DIR.mkdir(exist_ok=True)
    INVOICES_DIR.mkdir(exist_ok=True)
    (PYTM_DIR / "data.json").write_text(json.dumps(DATA, indent=2))
    (PYTM_DIR / "state.json").write_text(json.dumps(STATE, indent=2))
    (PYTM_DIR / "invoices.json").write_text(json.dumps(INVOICES, indent=2))
    for num in [1, 2, 3]:
        (INVOICES_DIR / f"invoice-00{num}.html").write_text(
            INVOICE_HTML.format(num=num)
        )


def backup_real_data():
    if BACKUP_DIR.exists():
        shutil.rmtree(BACKUP_DIR)
    if PYTM_DIR.exists():
        shutil.copytree(PYTM_DIR, BACKUP_DIR)
        print(f"Backed up {PYTM_DIR} to {BACKUP_DIR}")


def restore_real_data():
    if BACKUP_DIR.exists():
        if PYTM_DIR.exists():
            shutil.rmtree(PYTM_DIR)
        shutil.copytree(BACKUP_DIR, PYTM_DIR)
        shutil.rmtree(BACKUP_DIR)
        print(f"Restored {PYTM_DIR} from backup")


def wait_for_server(url, timeout=15):
    import urllib.request
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            urllib.request.urlopen(url, timeout=1)
            return True
        except Exception:
            time.sleep(0.3)
    return False


# ---------------------------------------------------------------------------
# Screenshots
# ---------------------------------------------------------------------------
def take_screenshots(base_url):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 800})

        def shot(filename, settle=600):
            page.wait_for_timeout(settle)
            page.screenshot(path=str(OUT_DIR / filename))
            print(f"  saved {filename}")

        # --- 01: Dashboard overview ---
        page.goto(f"{base_url}/")
        page.wait_for_load_state("networkidle")
        shot("screenshot-01-dashboard.png")

        # --- 02: Filter ---
        page.locator("input[placeholder*='Filter']").fill("acme")
        shot("screenshot-02-dashboard-filter.png")
        page.locator("input[placeholder*='Filter']").fill("")

        # --- 03: Sort by hours ---
        page.locator("button", has_text="Hours").click()
        page.wait_for_load_state("networkidle")
        shot("screenshot-03-dashboard-sort.png")

        # --- 04: Project metadata edit ---
        # Click ⚙ gear on acme-website row
        acme_row = page.locator("#project-row-acme-website")
        acme_row.locator("button", has_text="⚙").click()
        page.wait_for_timeout(400)
        shot("screenshot-04-project-meta-edit.png")
        # Close by clicking gear again
        acme_row.locator("button", has_text="⚙").click()

        # --- 05: Task panel ---
        page.locator("#project-row-acme-website").click()
        page.wait_for_selector("#task-panel input[placeholder*='New task']", state="visible")
        shot("screenshot-05-task-panel.png")

        # --- 06: Backfill form ---
        page.locator("button", has_text="Backfill past entry").click()
        page.wait_for_timeout(400)
        shot("screenshot-06-task-backfill.png")

        # --- 07: Active timer ---
        # beta-api / endpoint-design is running; reload dashboard and wait for Alpine
        page.goto(f"{base_url}/")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(1200)  # let Alpine initialize and x-show evaluate
        shot("screenshot-07-active-timer.png")

        # --- 08: Inline confirm (abort on a task row) ---
        # Open beta-api task panel to get a running task with Abort button
        page.locator("#project-row-beta-api").click()
        page.wait_for_selector("#task-panel input[placeholder*='New task']", state="visible")
        page.wait_for_timeout(400)
        abort_btn = page.locator("#task-panel").locator("button", has_text="Abort").first
        abort_btn.click()
        page.wait_for_timeout(300)
        shot("screenshot-08-inline-confirm.png")
        # Navigate away instead of cancelling — next step goes to /invoices

        # --- 09: Invoices list ---
        page.goto(f"{base_url}/invoices/page")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(1500)  # Tailwind Play CDN needs time to process dense table markup
        shot("screenshot-09-invoices.png")

        # --- 10: Invoice edit mode ---
        page.locator("button", has_text="Edit").first.click()
        page.wait_for_timeout(800)
        shot("screenshot-10-invoice-edit.png")

        # --- 11: Mark as paid ---
        page.goto(f"{base_url}/invoices/page")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(1500)
        rows = page.locator("tbody tr")
        for i in range(rows.count()):
            row = rows.nth(i)
            if row.locator("button", has_text="Paid").count():
                row.locator("button", has_text="Paid").click()
                page.wait_for_timeout(800)
                shot("screenshot-11-invoice-mark-paid.png")
                break

        # --- 12: Write-off confirm ---
        page.goto(f"{base_url}/invoices/page")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(1500)
        rows = page.locator("tbody tr")
        for i in range(rows.count()):
            row = rows.nth(i)
            if row.locator("button", has_text="Write off").count():
                row.locator("button", has_text="Write off").click()
                page.wait_for_timeout(800)
                shot("screenshot-12-invoice-writeoff-confirm.png")
                break

        browser.close()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    base_url = "http://127.0.0.1:8765"

    print("Backing up real data...")
    backup_real_data()

    try:
        print("Writing dummy data...")
        write_dummy_data()

        print("Starting PyTM web server...")
        server = subprocess.Popen(
            [sys.executable, "-m", "PyTM.cli", "web", "--port", "8765", "--no-browser"],
            cwd=str(Path(__file__).parent.parent),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        if not wait_for_server(base_url):
            server.terminate()
            print("ERROR: server did not start in time")
            sys.exit(1)

        print("Server ready. Taking screenshots...")
        try:
            take_screenshots(base_url)
        finally:
            server.terminate()
            server.wait()

        print(f"\nDone — {len(list(OUT_DIR.glob('screenshot-*.png')))} screenshots in {OUT_DIR}")

    finally:
        print("Restoring real data...")
        restore_real_data()


if __name__ == "__main__":
    main()
