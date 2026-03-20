#!/usr/bin/python
# -*- coding: utf-8 -*-
import datetime
import os
import shutil
import webbrowser

import click
from rich.prompt import Confirm, Prompt
from rich.table import Table
from rich.tree import Tree
from rich.panel import Panel
from rich.layout import Layout

from PyTM import __version__, settings
from PyTM.commands.project import project, get_duration_str
from PyTM.commands.task import task
from PyTM.console import console
from PyTM.core import data_handler, invoice_handler


def _prompt_hourly_rate(current_value=""):
    """Prompt for hourly rate with validation.

    Re-prompts on non-numeric input. If the user clears the field (empty input),
    the existing value is preserved unchanged.
    """
    while True:
        rate_input = Prompt.ask("Hourly rate in USD", default=current_value or "")
        if not rate_input:
            return current_value  # preserve existing; don't stomp with empty
        try:
            float(rate_input)
            return rate_input
        except ValueError:
            console.print("[red]Hourly rate must be a valid number (e.g. 105 or 105.50).")


def init_data_store(show_messages=False):
    """
    - initializes the pytm data store.
    """
    messages = []
    messages.append("[green on white]Initializing pytm-data.\n")
    try:
        os.makedirs(settings.data_folder)
        messages.append(f"Created data folder: {settings.data_folder}")
    except Exception as _:
        messages.append(f"Data folder already exists: {settings.data_folder}")
    if not os.path.exists(settings.data_filepath):
        data_handler.init_data(settings.data_filepath)
        messages.append(f"Created data file: {settings.data_filepath}")
    else:
        messages.append(f"Data file already exists: {settings.data_filepath}")

    if not os.path.exists(settings.state_filepath):
        data_handler.init_data(
            settings.state_filepath,
            {settings.CURRENT_PROJECT: "", settings.CURRENT_TASK: ""},
        )
        messages.append(f"Created state file: {settings.state_filepath}")
    else:
        messages.append(f"State file already exists: {settings.state_filepath}")

    if show_messages:
        for message in messages:
            console.print(message)


def print_version(ctx, param, value):
    """
    shows version and exits the CLI
    :param ctx:
    :param param:
    :param value:
    :return: None
    """
    if not value:
        return
    console.print("\n[bold green]✨ PyTM ✨")
    console.print(f"version {__version__}")
    console.print("docs: https://pytm.rtfd.org")
    ctx.exit()


@click.group()
@click.option(
    "--version",
    "-v",
    "--v",
    is_flag=True,
    callback=print_version,
    expose_value=False,
    is_eager=True,
    help="Shows version",
)
def cli():
    """
    docs: https://pytm.rtfd.org\n
    Config:\n
       default user data (optional): `pytm config user`\n
       default invoice texts & logo (optional): `pytm config invoice`
    """
    init_data_store()


@click.command(hidden=True)
def init():
    """
    - initializes & prints data files & folder.
    """
    console.print("[green on white]\nDone.")
    console.print(f"PyTM Data is stored in: {settings.data_folder}")
    console.print(f"Data file: {settings.data_filepath}")
    console.print(f"State file: {settings.state_filepath}")
    console.print(
        "\n[bold blue i on white]You also might want to run: `pytm config user` to configure default user data.[/bold blue i on white]"
    )


@click.command()
def show():
    """
    - shows list of projects and status
    """
    data = data_handler.load_data()
    state = data_handler.load_data(settings.state_filepath)
    table = Table()
    table.add_column("Project Name", style="blue bold")
    table.add_column("Created at")
    table.add_column("Status")
    for key, value in data.items():
        created_at = value.get("created_at", "")
        date_str = datetime.datetime.fromisoformat(created_at).strftime("%Y, %B, %d, %H:%M:%S %p") if created_at else ""
        table.add_row(key, date_str, value.get("status", ""))
    message = ""
    if state[settings.CURRENT_PROJECT]:
        message += f"Active Project: [bold blue]{state[settings.CURRENT_PROJECT]}[/bold blue]\n"
    if state[settings.CURRENT_TASK]:
        message += f"Active Task: [bold green]{state[settings.CURRENT_TASK]}"
    if message:
        console.print(message)
    console.print(table)


@click.group()
def config():
    """
    - pytm sub-commands for configuration.
    """
    ...


@config.command()
def user():
    """
    - config default user.
    """
    state = data_handler.load_data(settings.state_filepath)
    current_user = {}
    if state.get("config"):
        current_user = state.get("config").get("user", {})
    else:
        state["config"] = dict()
    current_user["name"] = Prompt.ask("Name", default=current_user.get("name", ""))
    current_user["email"] = Prompt.ask("Email", default=current_user.get("email", ""))
    current_user["phone"] = Prompt.ask("Phone", default=current_user.get("phone", ""))
    current_user["address"] = Prompt.ask(
        "Address", default=current_user.get("address", "")
    )
    current_user["website"] = Prompt.ask(
        "Website", default=current_user.get("website", "")
    )
    current_user["hourly_rate"] = _prompt_hourly_rate(current_user.get("hourly_rate", ""))
    state["config"]["user"] = current_user
    data_handler.save_data(state, settings.state_filepath)
    console.print("\n[green]Default user info updated.")


@config.command("invoice")
def config_invoice():
    """
    - configure invoice texts and logo.
    """
    state = data_handler.load_data(settings.state_filepath)
    invoice = {}
    if state.get("config"):
        invoice = state.get("config").get("invoice", {})
    else:
        state["config"] = dict()
    invoice["title"] = Prompt.ask(
        "Invoice Title", default=invoice.get("title", "Invoice")
    )
    invoice["logo"] = Prompt.ask(
        "Absolute path of a logo in .png format", default=invoice.get("logo", "")
    )
    if invoice["logo"]:
        try:
            shutil.copy2(
                invoice["logo"], os.path.join(settings.data_folder, "invoice-logo.png")
            )
            invoice["logo"] = os.path.join(settings.data_folder, "invoice-logo.png")
        except Exception as _:
            console.print("[bold red] Error occured while saving the logo.")
            console.print_exception()

    invoice["foot_note"] = Prompt.ask(
        "Foot Note?", default=invoice.get("foot_note", "Thank you for your business.")
    )
    invoice["invoice_number"] = Prompt.ask(
        "Default invoice number to start from? (integer)", default="13"
    )
    state["config"]["invoice"] = invoice
    data_handler.save_data(state, settings.state_filepath)
    console.print("\n[green]invoice texts are updated.")


@config.command(name="project")
@click.argument("project_name")
def config_project(project_name):
    """
    - config project meta data.
    """
    data = data_handler.load_data()
    if data.get(project_name):
        data[project_name]["meta"] = data.get(project_name).get("meta", {})
        data[project_name]["meta"]["title"] = Prompt.ask(
            "Project Title", default=data[project_name]["meta"].get("title", "")
        )
        data[project_name]["meta"]["billable"] = Confirm.ask(
            "Billable?", default=data[project_name]["meta"].get("billable", True)
        )
        data[project_name]["meta"]["client_name"] = Prompt.ask(
            "Client Name", default=data[project_name]["meta"].get("client_name", "")
        )
        data[project_name]["meta"]["client_email"] = Prompt.ask(
            "Client Email", default=data[project_name]["meta"].get("client_email", "")
        )
        data[project_name]["meta"]["client_phone"] = Prompt.ask(
            "Client Phone", default=data[project_name]["meta"].get("client_phone", "")
        )
        data[project_name]["meta"]["client_address"] = Prompt.ask(
            "Client Address",
            default=data[project_name]["meta"].get("client_address", ""),
        )
        data[project_name]["meta"]["client_website"] = Prompt.ask(
            "Client Website",
            default=data[project_name]["meta"].get("client_website", ""),
        )
    else:
        console.print(f"[bold red] Project {project_name} doesn't exist.")
    data_handler.save_data(data)
    console.print("\n[green]Project Meta data updated.")


@click.group()
def invoice():
    """
    - pytm sub-commands for invoice.
    """
    ...


@invoice.command()
@click.argument("project_name", required=False)
def auto(project_name):
    """
    - interactively generate an invoice.

    If PROJECT_NAME is given, loads tasks from that tracked project.
    Otherwise, prompts to enter tasks manually.
    """
    state = data_handler.load_data(settings.state_filepath)
    config = state.get("config", {})
    invoice_texts = config.get("invoice", {})

    # ── invoice header ──────────────────────────────────────────────────────
    invoice_number = Prompt.ask("Invoice Number", default=invoice_texts.get("invoice_number", "13"))
    if state.get("config", {}).get("invoice", {}).get("invoice_number") == invoice_number:
        try:
            state["config"]["invoice"]["invoice_number"] = str(int(invoice_number) + 1)
            data_handler.save_data(state, settings.state_filepath)
        except ValueError:
            console.print("[yellow]Could not auto-increment invoice number — value is not an integer.")

    invoice_texts["title"] = Prompt.ask("Invoice Title", default=invoice_texts.get("title", ""))
    invoice_texts["foot_note"] = Prompt.ask("Foot note", default=invoice_texts.get("foot_note", ""))
    invoice_texts["logo"] = Prompt.ask("Logo Absolute path", default=invoice_texts.get("logo", ""))

    # ── project / tasks ─────────────────────────────────────────────────────
    if project_name:
        data = data_handler.load_data()
        if not data.get(project_name):
            console.print(f"[bold red]{project_name} doesn't exist.")
            return
        project = data[project_name]
        if not project.get("meta"):
            project["meta"] = {}
        project_key = project_name
    else:
        project = {"meta": {}, "tasks": {}}
        project_key = "manual"

    project["meta"]["title"] = Prompt.ask("Project Name", default=project["meta"].get("title", project_name or ""))

    # ── biller info ─────────────────────────────────────────────────────────
    user = config.get("user", {})
    user["name"] = Prompt.ask("Your Name", default=user.get("name", ""))
    user["email"] = Prompt.ask("Email", default=user.get("email", ""))
    user["phone"] = Prompt.ask("Phone", default=user.get("phone", ""))
    user["address"] = Prompt.ask("Address", default=user.get("address", ""))
    user["website"] = Prompt.ask("Website", default=user.get("website", ""))
    user["hourly_rate"] = _prompt_hourly_rate(user.get("hourly_rate", ""))

    # ── client info ─────────────────────────────────────────────────────────
    project["meta"]["client_name"] = Prompt.ask("Bill To Name", default=project["meta"].get("client_name", "Anonymous Client"))
    project["meta"]["client_address"] = Prompt.ask("Address(street, state, zip, country)", default=project["meta"].get("client_address", ""))
    project["meta"]["client_phone"] = Prompt.ask("Phone", default=project["meta"].get("client_phone", ""))
    project["meta"]["client_email"] = Prompt.ask("Email", default=project["meta"].get("client_email", ""))
    project["meta"]["client_website"] = Prompt.ask("Website", default=project["meta"].get("client_website", ""))

    # ── manual task entry (only when no tracked project provided) ───────────
    if not project_name:
        number = 1
        while Confirm.ask("Add a task?", default=True):
            task_name = Prompt.ask("Task name?", default=f"Task {number}")
            if task_name.startswith("Task"):
                number += 1
            description = Prompt.ask("Task description?", default="-")
            hours_input = Prompt.ask("How many hours of work? (float)", default="0")
            project["tasks"][task_name] = {
                "description": description,
                "duration": float(hours_input) * 3600,
                "status": settings.FINISHED,
            }

    # ── generate ────────────────────────────────────────────────────────────
    discount = Prompt.ask("Discount?", default="")
    html, _total = invoice_handler.generate_multi(
        {project_key: project},
        invoice_number,
        user,
        discount,
        invoice_texts["title"],
        logo=invoice_texts.get("logo", ""),
        foot_note=invoice_texts.get("foot_note", "Thank you for your business."),
    )
    if html is None:
        console.print("[bold yellow]No tasks found. Nothing to invoice.")
        return
    os.makedirs(os.path.join(settings.data_folder, "invoices"), exist_ok=True)
    html_file = os.path.join(settings.data_folder, "invoices", f"{invoice_texts['title']}.html")
    with open(html_file, "w") as f:
        f.write(html)

    data_handler.save_invoice_record({
        "invoice_number": invoice_number,
        "title": invoice_texts["title"],
        "date_from": None,
        "date_to": None,
        "total": _total,
        "status": "unpaid",
        "paid_date": None,
        "created_at": str(datetime.date.today()),
    })

    console.print(f"The invoice is available in {html_file}")
    webbrowser.open(f"file:///{html_file}", autoraise=True)


@invoice.command(name="generate")
@click.option("--projects", "-p", multiple=True, metavar="KEY", help="Project keys to include (default: all).")
@click.option("--from", "date_from", default=None, metavar="YYYY-MM-DD", help="Include tasks on or after this date.")
@click.option("--to", "date_to", default=None, metavar="YYYY-MM-DD", help="Include tasks on or before this date.")
@click.option("--invoice-number", default="1", show_default=True, help="Invoice number.")
@click.option("--discount", default=0.0, type=float, show_default=True, help="Discount amount in USD.")
@click.option("--title", default="Invoice", show_default=True, help="Invoice title and output filename.")
@click.option("--list", "list_projects", is_flag=True, help="List available projects with hours and exit.")
def invoice_generate(projects, date_from, date_to, invoice_number, discount, title, list_projects):
    """
    - generates a multi-project invoice with optional date filtering.
    """
    data = data_handler.load_data()
    state = data_handler.load_data(settings.state_filepath)
    user = state.get("config", {}).get("user", {})

    try:
        df = datetime.date.fromisoformat(date_from) if date_from else None
        dt = datetime.date.fromisoformat(date_to) if date_to else None
    except ValueError as e:
        console.print(f"[bold red]Invalid date: {e}")
        return

    if list_projects:
        table = Table()
        table.add_column("Key", style="blue bold")
        table.add_column("Title")
        table.add_column("Hours")
        for key, proj in data.items():
            tasks = proj.get("tasks", {}).values()
            filtered = []
            for t in tasks:
                if t.get("status") == settings.ABORTED:
                    continue
                task_created = t.get("created_at", "")[:10]
                try:
                    td = datetime.date.fromisoformat(task_created)
                except ValueError:
                    td = None
                if df and td and td < df:
                    continue
                if dt and td and td > dt:
                    continue
                filtered.append(t)
            total_sec = sum(t["duration"] for t in filtered)
            h = int(total_sec // 3600)
            m = int((total_sec % 3600) // 60)
            meta_title = proj.get("meta", {}).get("title", "") if proj.get("meta") else ""
            table.add_row(key, meta_title or "-", f"{h}h {m:02d}m")
        console.print(table)
        return

    if projects:
        missing = [p for p in projects if p not in data]
        if missing:
            console.print(f"[bold red]Unknown project(s): {', '.join(missing)}")
            console.print("Run with --list to see available projects.")
            return
        selected = {k: data[k] for k in projects}
    else:
        selected = data

    html, total = invoice_handler.generate_multi(selected, invoice_number, user, discount, title, df, dt)

    if html is None:
        console.print("[bold yellow]No tasks found for the given filters. Nothing to invoice.")
        return

    os.makedirs(os.path.join(settings.data_folder, "invoices"), exist_ok=True)

    html_file = os.path.join(settings.data_folder, "invoices", f"{title}.html")
    with open(html_file, "w") as f:
        f.write(html)

    data_handler.save_invoice_record({
        "invoice_number": invoice_number,
        "title": title,
        "date_from": str(df) if df else None,
        "date_to": str(dt) if dt else None,
        "total": total,
        "status": "unpaid",
        "paid_date": None,
        "created_at": str(datetime.date.today()),
    })

    console.print(f"Invoice written to: {html_file}")
    webbrowser.open(f"file:///{html_file}", autoraise=True)


@invoice.command(name="mark-paid")
@click.argument("invoice_number")
@click.option("--date", "paid_date", default=None, metavar="YYYY-MM-DD", help="Payment date (defaults to today).")
def invoice_mark_paid(invoice_number, paid_date):
    """
    - mark an invoice as paid.
    """
    paid = paid_date or str(datetime.date.today())
    record = data_handler.update_invoice_status(invoice_number, "paid", paid)
    console.print(f"[green]Invoice #{invoice_number} ({record.get('title') or 'untitled'}) marked as paid on {paid}.")


@invoice.command(name="write-off")
@click.argument("invoice_number")
def invoice_write_off(invoice_number):
    """
    - mark an invoice as written off (not collectible).
    """
    record = data_handler.update_invoice_status(invoice_number, "written_off")
    console.print(f"[yellow]Invoice #{invoice_number} ({record.get('title') or 'untitled'}) marked as written off.")


@invoice.command(name="status")
def invoice_status():
    """
    - show a status report of all invoices with totals by status.
    """
    from rich.table import Table as RichTable
    invoices = data_handler.load_invoices()
    if not invoices:
        console.print("[yellow]No invoices recorded.")
        return

    table = RichTable(title="Invoice Status")
    table.add_column("#", style="bold")
    table.add_column("Title")
    table.add_column("Period")
    table.add_column("Total", justify="right")
    table.add_column("Status")
    table.add_column("Paid Date")

    status_styles = {"unpaid": "yellow", "paid": "green", "written_off": "dim"}
    totals = {"unpaid": 0.0, "paid": 0.0, "written_off": 0.0}

    for inv_num, inv in sorted(invoices.items()):
        st = inv.get("status", "unpaid")
        totals[st] = totals.get(st, 0.0) + inv.get("total", 0.0)
        period = f"{inv.get('date_from') or '?'} – {inv.get('date_to') or '?'}"
        table.add_row(
            inv_num,
            inv.get("title") or "",
            period,
            f"${inv.get('total', 0.0):,.2f}",
            f"[{status_styles.get(st, 'white')}]{st}[/]",
            inv.get("paid_date") or "-",
        )

    console.print(table)
    console.print()

    summary = RichTable(show_header=True)
    summary.add_column("Status")
    summary.add_column("Total", justify="right")
    summary.add_row("[green]Paid[/]", f"${totals['paid']:,.2f}")
    summary.add_row("[yellow]Unpaid[/]", f"${totals['unpaid']:,.2f}")
    summary.add_row("[dim]Written Off[/]", f"${totals.get('written_off', 0.0):,.2f}")
    console.print(summary)




@click.command()
def summary():
    """
    - shows summary of all projects.
    """
    data = data_handler.load_data()
    layout = Layout()

    count = 0
    left, right = [], []
    for project_name in data:
        project_data = data.get(project_name, {}).get("tasks", {})
        tree = Tree(
            f'[bold blue]{project_name}[/bold blue] ([i]{data.get(project_name, {})["status"]}[/i])'
        )
        if project_data == {}:
            tree.add("[red] No tasks yet. [/red]")
            right.append(Panel(tree, title=f"{project_name}"))
            continue
        duration = 0
        for task_name, t in project_data.items():
            task_duration = int(round(t["duration"]))
            duration += task_duration
            tree.add(
                f"[green]{task_name}[/green]: {get_duration_str(task_duration)} ([i]{t['status']}[/i])"
            )
        left.append(
            Panel(
                tree,
                title=f"{project_name}",
                subtitle=f"[blue bold]Total time[/blue bold]: {get_duration_str(duration)}",
                expand=False,
            )
        )
        count += 1
    layout.split_row(  # *p)
        Layout(name="left", size=45),
        Layout(name="right", size=55),
    )
    layout["left"].split_column(*left)
    layout["right"].split_column(*right)
    console.print(layout)


cli.add_command(init)
cli.add_command(project)
cli.add_command(task)
cli.add_command(show)
cli.add_command(config)
cli.add_command(invoice)
cli.add_command(summary)

if __name__ == "__main__":
    cli()
