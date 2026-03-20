import click


@click.command()
@click.option("--host", default="127.0.0.1", show_default=True, help="Bind host.")
@click.option("--port", default=8000, show_default=True, type=int, help="Bind port.")
@click.option("--no-browser", is_flag=True, default=False, help="Don't open browser automatically.")
def web(host, port, no_browser):
    """
    - launch the PyTM web UI (FastAPI + HTMX).
    """
    try:
        import uvicorn
    except ImportError:
        click.echo(
            "[red]uvicorn is not installed. Run: pip install 'python-pytm[web]'",
            err=True,
        )
        raise SystemExit(1)

    if not no_browser:
        import threading, webbrowser, time

        def _open():
            time.sleep(1.0)
            webbrowser.open(f"http://{host}:{port}")

        threading.Thread(target=_open, daemon=True).start()

    click.echo(f"PyTM web UI → http://{host}:{port}  (Ctrl+C to stop)")
    uvicorn.run(
        "PyTM.web.app:create_app",
        factory=True,
        host=host,
        port=port,
        workers=1,       # threading.Lock inside DataStore; must be single-worker
        reload=False,
    )
