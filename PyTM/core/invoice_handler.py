import datetime
import re

from PyTM import settings
from PyTM.commands.project import get_duration_str


# ── Multi-project invoice helpers ─────────────────────────────────────────────


def _fix_acronyms(label):
    return " ".join(w.upper() if w.upper() in settings.ACRONYMS else w for w in label.split())


def format_task_name(task_name):
    """Convert '2026-03-16-initial-doc-and-review' to '3/16/2026 - Initial Doc And Review'."""
    match = re.match(r"^(\d{4})-(\d{2})-(\d{2})-(.+)$", task_name)
    if match:
        year, month, day, rest = match.groups()
        label = _fix_acronyms(rest.replace("-", " ").replace("_", " ").title())
        return f"{int(month)}/{int(day)}/{year} - {label}"
    return _fix_acronyms(task_name.replace("-", " ").replace("_", " ").title())


def generate_multi(projects_data, invoice_number, user, discount, title, date_from=None, date_to=None, logo=None, foot_note="Thank you for your business."):
    """Generate a multi-project invoice HTML string.

    Args:
        projects_data: dict of {project_key: project_dict} from data.json
        invoice_number: invoice number string
        user: user config dict (name, address, email, phone, website, hourly_rate)
        discount: float discount amount in USD
        title: invoice title string
        date_from: optional datetime.date lower bound (inclusive) filtering by task created_at
        date_to: optional datetime.date upper bound (inclusive) filtering by task created_at
        logo: optional absolute path to a logo image file
        foot_note: optional footnote text shown at the bottom of the invoice
    Returns:
        (html_string, total_float), or (None, 0.0) if no tasks matched.
    """
    hourly_rate = float(user.get("hourly_rate", 0))
    total_seconds = 0
    subtotal = 0.0
    task_rows = []

    for project_key, project in projects_data.items():
        if project.get("meta", {}).get("billable") is False:
            continue
        project_title = project.get("meta", {}).get("title") or project_key
        for task_name, task in project.get("tasks", {}).items():
            if task.get("status") == settings.ABORTED:
                continue
            task_created = task.get("created_at", "")[:10]
            try:
                task_date = datetime.date.fromisoformat(task_created)
            except ValueError:
                task_date = None
            if date_from and task_date and task_date < date_from:
                continue
            if date_to and task_date and task_date > date_to:
                continue
            duration_sec = task.get("duration", 0)
            hours = duration_sec / 3600.0
            fee = hours * hourly_rate
            total_seconds += duration_sec
            subtotal += fee
            task_rows.append({
                "project": project_title,
                "task": format_task_name(task_name),
                "description": task.get("description", ""),
                "hours": hours,
                "fee": fee,
            })

    if not task_rows:
        return None, 0.0

    discount_amt = float(discount) if discount else 0.0
    total = subtotal - discount_amt

    # Client info: use first selected project's meta as fallback
    first_project = next(iter(projects_data.values()))
    meta = first_project.get("meta", {}) or {}
    client_name = meta.get("client_name") or "Client"
    client_address = meta.get("client_address") or ""
    client_email = meta.get("client_email") or ""

    def opt(value):
        return f"<p>{value}</p>" if value else ""

    def fmt_hours(seconds):
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        return f"{h}h {m:02d}m"

    period_line = ""
    if date_from or date_to:
        period_line = f'<p class="text-gray-500 text-sm">Period: {date_from or "start"} &ndash; {date_to or "today"}</p>'

    rows_html = "\n".join(
        f"""        <tr>
            <td class="p-2 border border-gray-300 text-sm text-gray-600">{r["project"]}</td>
            <td class="p-2 border border-gray-300">{r["task"]}</td>
            <td class="p-2 border border-gray-300 text-sm">{r["description"]}</td>
            <td class="p-2 border border-gray-300 text-right">{r["hours"]:,.2f}</td>
            <td class="p-2 border border-gray-300 text-right">${hourly_rate:,.2f}</td>
            <td class="p-2 border border-gray-300 text-right">${r["fee"]:,.2f}</td>
        </tr>"""
        for r in task_rows
    )

    logo_tag = f'<img src="{logo}" width="150" alt="{user.get("name", "")}" class="mr-4" style="height:auto;">' if logo else ""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.15/dist/tailwind.min.css" rel="stylesheet">
</head>
<body class="font-sans">
    <div class="container mx-auto py-8">
        <div class="p-8">
            <div class="flex justify-between mb-8">
                <div class="flex items-center">
                    {logo_tag}
                    <div>
                    <h1 class="text-2xl font-semibold">{user.get("name", "")}</h1>
                    {opt(user.get("address", ""))}
                    {opt(user.get("email", ""))}
                    {opt(user.get("phone", ""))}
                    {opt(user.get("website", ""))}
                    </div>
                </div>
                <div class="text-right">
                    <p class="text-lg font-semibold">Invoice #{invoice_number}</p>
                    <p class="text-sm text-gray-600">Date: {datetime.datetime.now().date()}</p>
                    <div class="mt-2">
                        <p class="font-semibold">Bill To</p>
                        <p>{client_name}</p>
                        {opt(client_address)}
                        {opt(client_email)}
                    </div>
                </div>
            </div>
            <div class="mb-4">
                <h2 class="text-xl font-semibold">{title}</h2>
                <p class="text-gray-600">Total hours: {fmt_hours(total_seconds)}</p>
                {period_line}
            </div>
            <table class="w-full border-collapse border border-gray-300 mb-6">
                <thead class="bg-gray-50">
                    <tr>
                        <th class="p-2 border border-gray-300 text-left">Project</th>
                        <th class="p-2 border border-gray-300 text-left">Task</th>
                        <th class="p-2 border border-gray-300 text-left">Description</th>
                        <th class="p-2 border border-gray-300 text-right">Hours</th>
                        <th class="p-2 border border-gray-300 text-right">Rate</th>
                        <th class="p-2 border border-gray-300 text-right">Fee</th>
                    </tr>
                </thead>
                <tbody>
{rows_html}
                </tbody>
            </table>
            <div class="flex justify-end">
                <div class="w-64">
                    <table class="w-full">
                        <tr>
                            <td class="py-1">Subtotal:</td>
                            <td class="text-right py-1">${subtotal:,.2f}</td>
                        </tr>
                        <tr>
                            <td class="py-1">Discount:</td>
                            <td class="text-right py-1">${discount_amt:,.2f}</td>
                        </tr>
                        <tr class="font-semibold border-t border-gray-300">
                            <td class="py-1">Total:</td>
                            <td class="text-right py-1">${total:,.2f}</td>
                        </tr>
                    </table>
                </div>
            </div>
            {f'<p class="mt-8 text-sm text-gray-500">{foot_note}</p>' if foot_note else ""}
        </div>
    </div>
</body>
</html>""", total
