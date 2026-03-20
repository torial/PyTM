from functools import partial

import click
from rich.panel import Panel
from rich.tree import Tree

from PyTM import settings
from PyTM.console import console
from PyTM.core import task_handler
from PyTM.core import data_handler
from PyTM.core import project_handler


def get_duration_str(sum_of_durations):
    m, s = divmod(sum_of_durations, 60)
    duration = ""
    if m >= 60:
        h, m = divmod(m, 60)
        if h > 24:
            d, h = divmod(h, 24)
            duration = f"{d:d} days {h:d} hours {m:02d} mins {s:02d} secs"
        else:
            duration = f"{h:d} hours {m:02d} mins {s:02d} secs"
    elif m < 1:
        duration = f"{s:02d} seconds"
    else:
        duration = f"{m:02d} mins {s:02d} secs"
    return duration


@click.group()
def project():
    """
    pytm sub-command for managing projects.
    """
    pass


@project.command()
def abort():
    """
    - aborts the current project and task.
    """
    state = data_handler.load_data(settings.state_filepath)
    project_name = state.get(settings.CURRENT_PROJECT)
    if project_name:
        data_handler.update(partial(project_handler.abort, project_name=project_name))
        state[settings.CURRENT_PROJECT] = ""
        if state[settings.CURRENT_TASK]:
            data_handler.update(
                partial(
                    task_handler.abort,
                    project_name=project_name,
                    task_name=state[settings.CURRENT_TASK],
                )
            )
            state[settings.CURRENT_TASK] = ""
        data_handler.save_data(state, settings.state_filepath)
        console.print(f"[bold blue]{project_name}[/bold blue] aborted.")
    else:
        console.print("[bold red]No active project.")


@project.command()
def finish():
    """
    - marks the current project as finished.
    """
    state = data_handler.load_data(settings.state_filepath)
    project_name = state.get(settings.CURRENT_PROJECT)
    if project_name:
        data_handler.update(partial(project_handler.finish, project_name=project_name))
        state[settings.CURRENT_PROJECT] = ""
        if state[settings.CURRENT_TASK]:
            data_handler.update(
                partial(
                    task_handler.finish,
                    project_name=project_name,
                    task_name=state[settings.CURRENT_TASK],
                )
            )
            state[settings.CURRENT_TASK] = ""
        data_handler.save_data(state, settings.state_filepath)
        console.print(f"[bold blue]{project_name}[/bold blue] finished.")
    else:
        console.print("[bold red]No active project.")


@project.command()
def pause():
    """
    - pauses the current project, so new tasks can't be started.
    """
    state = data_handler.load_data(settings.state_filepath)
    project_name = state.get(settings.CURRENT_PROJECT)
    if project_name:
        data_handler.update(partial(project_handler.pause, project_name=project_name))
        state[settings.CURRENT_PROJECT] = ""
        if state[settings.CURRENT_TASK]:
            data_handler.update(
                partial(
                    task_handler.pause,
                    project_name=project_name,
                    task_name=state[settings.CURRENT_TASK],
                )
            )
            state[settings.CURRENT_TASK] = ""
        data_handler.save_data(state, settings.state_filepath)
        console.print(f"[bold blue]{project_name}[/bold blue] paused.")
    else:
        console.print("[bold red]No active project.")


@project.command()
@click.argument("project_name", required=False)
def start(project_name):
    """
    - starts an existing project or creates a new project.
    """
    data = data_handler.load_data()

    if project_name is None:
        num = len(data.keys())
        while project_name is None or data.get(project_name):
            num += 1
            project_name = f"UNNAMED_{num}"

    data_handler.update(partial(project_handler.create, project_name=project_name))
    state = data_handler.load_data(settings.state_filepath)
    state[settings.CURRENT_PROJECT] = project_name
    state[settings.CURRENT_TASK] = ""
    data_handler.save_data(state, settings.state_filepath)
    console.print(f"[bold blue]{project_name}[/bold blue] started.")
    if project_name not in data.keys():
        console.print(
            f"\n[bold blue i on white]You also might want to run: `pytm config project {project_name}` to configure project meta data.[/bold blue i on white]"
        )


@project.command()
@click.argument("project_name")
def remove(project_name):
    """
    - archives a project (soft delete). Use 'recover' to restore.
    """
    data = data_handler.load_data()
    if not data.get(project_name):
        console.print(f"[bold red]{project_name} doesn't exist.")
        return
    data_handler.archive_project(project_name, data[project_name])
    data_handler.update(partial(project_handler.remove, project_name=project_name))
    state = data_handler.load_data(settings.state_filepath)
    if state.get(settings.CURRENT_PROJECT) == project_name:
        state[settings.CURRENT_PROJECT] = ""
        state[settings.CURRENT_TASK] = ""
        data_handler.save_data(state, settings.state_filepath)
    console.print(f"[bold blue]{project_name}[/bold blue] archived. Use [green]pytm project recover {project_name}[/green] to restore.")


@project.command()
def archived():
    """
    - lists all archived (soft-deleted) projects.
    """
    from rich.table import Table as RichTable
    archive = data_handler.load_archive()
    if not archive:
        console.print("[yellow]No archived projects.")
        return
    table = RichTable(title="Archived Projects")
    table.add_column("Project", style="blue bold")
    table.add_column("Snapshots", justify="right")
    table.add_column("Most Recently Archived")
    for name, entries in sorted(archive.items()):
        latest = entries[-1]["archived_at"] if entries else "-"
        table.add_row(name, str(len(entries)), latest)
    console.print(table)


@project.command()
@click.argument("project_name")
def recover(project_name):
    """
    - restores the most recently archived snapshot of a project.
    """
    data = data_handler.load_data()
    if data.get(project_name):
        console.print(f"[bold red]A project named '{project_name}' already exists. Rename or remove it first.")
        return
    snapshot = data_handler.pop_archived_project(project_name)
    if snapshot is None:
        console.print(f"[bold red]No archived snapshot found for '{project_name}'.")
        return
    data[project_name] = snapshot["data"]
    data_handler.save_data(data)
    console.print(f"[bold blue]{project_name}[/bold blue] restored from archive (snapshot: {snapshot['archived_at']}).")


@project.command()
@click.argument("project_name")
def status(project_name):
    """
    - of the project (running, paused, finished, etc).
    """
    console.print(
        f"[bold blue]{project_name}[/bold blue] status: {project_handler.status(data_handler.load_data(), project_name)}"
    )


@project.command()
@click.argument("project_name")
def summary(project_name):
    """
    - shows total time of the project with task and duration.
    """
    project_summary = project_handler.summary(data_handler.load_data(), project_name)
    project_status = project_summary.get("status", "")
    project_tasks = project_summary.get("tasks", {})
    tree = Tree(f'[bold blue]{project_name}[/bold blue] ([i]{project_status}[/i])')
    duration = 0
    for task_name, t in project_tasks.items():
        task_duration = int(round(t["duration"]))
        duration += task_duration
        tree.add(
            f"[green]{task_name}[/green]: {get_duration_str(task_duration)} ([i]{t['status']}[/i])"
        )
    console.print(Panel.fit(tree))
    console.print(f"[blue bold]Total time[/blue bold]: {get_duration_str(duration)}")


@project.command()
@click.argument("project_name")
def json(project_name):
    """
    - shows project data in json format.
    """
    console.print_json(
        data=project_handler.summary(data_handler.load_data(), project_name)
    )


@project.command()
@click.argument("project_name")
@click.argument("new_name")
def rename(project_name, new_name):
    """
    - Renames an existing project.
    """
    data = data_handler.load_data()
    state = data_handler.load_data(settings.state_filepath)

    if not data.get(project_name):
        console.print(
            f"[bold red] {project_name} doesn't exists. Make sure the spelling is correct."
        )
        return
    if data.get(new_name):
        console.print(
            f"[bold red] {new_name} already exists. Choose a different project name."
        )
        return
    data_handler.update(
        partial(project_handler.rename, project_name=project_name, new_name=new_name)
    )
    console.print(f"The project: {project_name} is renamed to {new_name}.")
    if state[settings.CURRENT_PROJECT] == project_name:
        state[settings.CURRENT_PROJECT] = new_name
        data_handler.save_data(state, settings.state_filepath)
