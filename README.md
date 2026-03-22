# PyTM — CLI time tracker with web UI, project management, and invoice generation

[![License](https://img.shields.io/pypi/l/pytm-web.svg)](https://pypi.org/project/pytm-web/)
[![Python Versions](https://img.shields.io/pypi/pyversions/pytm-web.svg)](https://pypi.org/project/pytm-web/)

> This is a fork of [python-pytm](https://github.com/wasi0013/PyTM) by
> [Wasi (wasi0013)](https://github.com/wasi0013), significantly extended
> with additional CLI commands, schema versioning, and a full web UI.
> See [Attribution](#attribution) below.

## Screenshots

**Dashboard** — project list with sort controls and totals summary bar:

![PyTM Web UI — Dashboard](ext/images/screenshot-01-dashboard.png)

**Filter** — type to narrow projects by name or title in real time:

![PyTM Web UI — Project filter](ext/images/screenshot-02-dashboard-filter.png)

**Sort by hours** — re-order projects by total time tracked:

![PyTM Web UI — Sort by hours](ext/images/screenshot-03-dashboard-sort.png)

**Project metadata** — click ⚙ to edit title, client, hourly rate, and billable flag inline:

![PyTM Web UI — Project metadata editing](ext/images/screenshot-04-project-meta-edit.png)

**Task panel** — click a project to see its tasks; start new tasks or resume existing ones:

![PyTM Web UI — Task panel](ext/images/screenshot-05-task-panel.png)

**Backfill** — log past work with date, hours, start time, and description:

![PyTM Web UI — Backfill form](ext/images/screenshot-06-task-backfill.png)

**Active timer** — live HH:MM:SS counter in the nav bar; press Space to pause:

![PyTM Web UI — Active timer](ext/images/screenshot-07-active-timer.png)

**Inline confirm** — destructive actions show an in-place confirmation instead of a browser dialog:

![PyTM Web UI — Inline confirmation](ext/images/screenshot-08-inline-confirm.png)

**Invoices** — history table with sortable columns, totals by status, and action buttons per row:

![PyTM Web UI — Invoice list](ext/images/screenshot-09-invoices.png)

**Invoice edit / regenerate** — click Edit to pre-fill the form with existing values and regenerate:

![PyTM Web UI — Invoice edit mode](ext/images/screenshot-10-invoice-edit.png)

**Mark as paid** — date picker (defaulting to today) appears inline to record a payment:

![PyTM Web UI — Mark invoice paid](ext/images/screenshot-11-invoice-mark-paid.png)

**Write-off confirm** — inline Yes/No confirmation before changing invoice status:

![PyTM Web UI — Write-off confirmation](ext/images/screenshot-12-invoice-writeoff-confirm.png)


## Goals

Project time management, billing, and invoice generation — usable from the
terminal or a local web browser.


## Installing

Install the CLI only:

```
pip install pytm-web
```

Install with the web UI:

```
pip install "pytm-web[web]"
```

For local development (editable):

```
git clone https://github.com/torial/PyTM.git
cd PyTM
pip install -e ".[web]"
```

Check the version:

```
pytm --version
```


## Basic commands

To see all available commands:

```
pytm --help
```


## Commands related to projects

- Start a new project with a default name: `pytm project start`
- Start a new project with the given name or resume an existing one: `pytm project start PROJECT_NAME`
- Rename a project: `pytm project rename OLD_PROJECT_NAME NEW_NAME`
- Archive (soft-delete) a project: `pytm project remove PROJECT_NAME`
- Restore an archived project: `pytm project recover PROJECT_NAME`
- List all archived projects: `pytm project archived`
- Check the status of a project: `pytm project status PROJECT_NAME`
- Check the list of tasks and duration of a project: `pytm project summary PROJECT_NAME`
- Finish active project: `pytm project finish`
- Pause active project: `pytm project pause`
- Abort active project: `pytm project abort`

> **Note:** `pytm project remove` performs a **soft delete** — the project is archived
> to `~/.pytm/archive.json` and can be recovered with `pytm project recover PROJECT_NAME`.
> No data is permanently lost.


## Commands related to tasks

- Start a new task with a default name in the active project: `pytm task start`
- Start a new task or resume an existing one: `pytm task start TASK_NAME`
- Rename a task of the active project: `pytm task rename OLD_TASK_NAME NEW_NAME`
- Remove a task: `pytm task remove PROJECT_NAME TASK_NAME`
- Current task status: `pytm task status`
- Finish active task: `pytm task finish`
- Pause active task: `pytm task pause`
- Abort active task: `pytm task abort`
- Backfill a completed task with a past date and duration: `pytm task backfill PROJECT_NAME TASK_NAME --date YYYY-MM-DD --hours N`

Backfill options:

```
pytm task backfill PROJECT_NAME TASK_NAME \
    --date 2026-01-15 \
    --hours 2.5 \
    --time 09:00 \
    --description "Meeting notes"
```


## Invoice commands

Configure invoice defaults (title, logo, footnote, starting invoice number):

```
pytm config invoice
```

Generate an invoice interactively using a tracked project:

```
pytm invoice auto PROJECT_NAME
```

Generate an invoice interactively without a tracked project (enter tasks manually):

```
pytm invoice auto
```

Generate a non-interactive multi-project invoice with optional date filtering:

```
pytm invoice generate
pytm invoice generate --projects alpha --projects beta
pytm invoice generate --from 2026-01-01 --to 2026-03-31
pytm invoice generate --invoice-number 7 --discount 50 --title "March Invoice"
pytm invoice generate --list    # show available projects with hours and exit
```

Track invoice payment status:

```
pytm invoice mark-paid INVOICE_NUMBER
pytm invoice mark-paid INVOICE_NUMBER --date 2026-03-15
pytm invoice write-off INVOICE_NUMBER
pytm invoice status    # summary table of all invoices with totals by status
```

Invoice records are stored in `~/.pytm/invoices.json`.
Generated HTML files are written to `~/.pytm/invoices/`.


## Web UI

Launch the local web interface:

```
pytm web
```

Options:

```
pytm web --host 0.0.0.0 --port 8080 --no-browser
```

Built with FastAPI, HTMX, Alpine.js, and Tailwind CSS. Static assets are
vendored (no CDN required after install).

### Dashboard (Projects)

The left sidebar lists all active projects. From here you can:

- **Sort** by name (A–Z), total hours, or last-updated date.
- **Filter** projects by typing in the filter input — matches on both the project key and its display title.
- **Create** a new project by typing a name and pressing Enter or `+`. The input clears automatically after creation.
- **See totals** in a pinned summary bar at the bottom of the list — total hours across all projects and billable hours only.

Each project row shows the display title (or key if untitled), current status badge, total duration, and last-updated date. Action buttons appear inline:

- **Pause / Finish** when a project is running.
- **Resume** when paused, finished, or aborted — targets just that row.
- **⚙ gear** opens an inline metadata edit form for Title, Client name, Hourly rate, and Billable flag. Changes take effect immediately.
- **✕ archive** with an inline "Archive? Yes / No" confirmation (no browser dialog).

The active timer bar appears at the top of the main area when a task is running, showing the project's display title and task name with a live HH:MM:SS counter. Press **Space** to pause the active task from anywhere in the dashboard (when not focused in a text field).

### Task Panel

Clicking a project loads its task list into the right panel, which auto-focuses the new-task input so you can start typing immediately. The panel header shows the project's display title with the key slug below it.

From the task panel you can:

- **Start a new task** by typing a name and pressing Enter (or clicking Start). Any currently running task is paused automatically.
- **Backfill a past entry** — expand the collapsible backfill form to log historical work with a date (defaults to today), hours, optional start time, and description.
- **Resume, Pause, or Finish** any existing task inline.
- **Abort** a task with an inline "Abort? Yes / No" confirmation.
- **Delete** a task permanently with an inline "Delete? Yes / No" confirmation.

All task actions produce a toast notification in the nav bar that auto-dismisses after 3 seconds.

### Invoices

The invoice page shows the generation form on the left and the invoice history table on the right.

Generation form:

- **Invoice number** defaults to the next sequential number (max existing + 1).
- **Mode toggle** switches between project-based (select one or more projects from a multi-select list) and manual entry (add arbitrary line items with name, hours, and description).
- **Date range** filters tasks to the specified period when in project mode.
- **Discount** and **Footnote** fields round out the invoice.
- Clicking **Generate** writes an HTML invoice to `~/.pytm/invoices/` and records the metadata in `invoices.json`.

Invoice history table:

- **Sort** by invoice number or billing period using the clickable column headers.
- **View** opens the generated HTML invoice in a new tab.
- **Edit** pre-fills the generation form with the invoice's existing values (number, title, dates, discount, footnote) so you can regenerate it. Payment status and paid date are preserved on regenerate.
- **Paid** reveals a date picker (defaulting to today) and records the payment date.
- **Write off** marks an invoice as written off, with an inline confirmation.
- Totals for paid, unpaid, and written-off amounts appear below the table.


## Other commands

Configure project, user, and invoice info:

```
pytm config project PROJECT_NAME
pytm config user
pytm config invoice
```

Summary of all projects:

```
pytm summary
```


## Running the tests

```
git clone https://github.com/torial/PyTM.git
cd PyTM
pip install -e ".[web]"
pip install pytest
pytest
```


## Attribution

**Original project:** [python-pytm](https://github.com/wasi0013/PyTM) by
[Wasi (wasi0013)](https://github.com/wasi0013). The original CLI, core data
layer, project/task management, and invoice generation were written by Wasi and
are the foundation this fork builds on.

**Fork maintained by:** [Sean (torial)](https://github.com/torial) — added
CLI extensions (backfill, invoice generate/mark-paid/write-off/status, project
archive/recover), schema versioning, the full web UI (FastAPI + HTMX +
Alpine.js), expanded test coverage, and this package (`pytm-web`).

**AI assistance:** [Claude (Anthropic)](https://anthropic.com) — pair
programming on the CLI extensions, web UI architecture and implementation,
test suite, and documentation for this fork.

**License:** MIT — see [LICENSE](LICENSE).
