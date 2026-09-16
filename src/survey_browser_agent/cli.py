import asyncio
from pathlib import Path
from typing import Annotated

import typer

from survey_browser_agent.browser_agent import read_news
from survey_browser_agent.config import Settings
from survey_browser_agent.ollama import check_ollama
from survey_browser_agent.storage import RunStore

app = typer.Typer(
    name="survey-browser-agent",
    help="Read-only Browser Use + Ollama learning MVP.",
    no_args_is_help=True,
)


def _context(model: str | None = None) -> tuple[Settings, RunStore]:
    settings = Settings(ollama_model=model) if model else Settings()
    return settings, RunStore(settings.resolved_database_path)


def _run_news_read(
    url: Annotated[str, typer.Argument(help="Public HTTP(S) news article URL")],
    model: Annotated[
        str | None,
        typer.Option(
            "--model",
            "-m",
            help="Ollama model for this run, for example qwen3.5:9b or llama3.1:8b",
        ),
    ] = None,
) -> None:
    settings, store = _context(model)
    health = check_ollama(settings.ollama_base_url, settings.ollama_model)
    if not health.reachable or not health.model_available:
        typer.echo(health.message, err=True)
        raise typer.Exit(code=2)
    try:
        run_id, article = asyncio.run(read_news(url, settings, store, typer.echo))
    except Exception as exc:
        typer.echo(f"Run failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"\nRun {run_id} result:")
    typer.echo(article.model_dump_json(indent=2))


@app.command("news-read")
def news_read(
    url: Annotated[str, typer.Argument(help="Public HTTP(S) news article URL")],
    model: Annotated[
        str | None,
        typer.Option(
            "--model",
            "-m",
            help="Ollama model for this run, for example qwen3.5:9b or llama3.1:8b",
        ),
    ] = None,
) -> None:
    """Open one article in visible Chrome and save structured data."""

    _run_news_read(url, model)


@app.command("check")
def check(
    model: Annotated[
        str | None,
        typer.Option(
            "--model",
            "-m",
            help="Ollama model to check; otherwise use the configured default",
        ),
    ] = None,
) -> None:
    """Check Ollama, the selected model, Chrome configuration, and Browser Use."""

    settings, _ = _context(model)
    health = check_ollama(settings.ollama_base_url, settings.ollama_model)
    typer.echo(health.message)
    try:
        import browser_use  # noqa: F401

        typer.echo("Browser Use is installed.")
    except ImportError:
        typer.echo("Browser Use is not installed. Run: uv sync --extra dev")

    if settings.chrome_executable_path:
        chrome_path = Path(settings.chrome_executable_path)
        state = "found" if chrome_path.exists() else "missing"
        typer.echo(f"Configured Chrome: {chrome_path} ({state})")
    else:
        typer.echo("Chrome path: automatic system Chrome detection")
    try:
        directory = settings.resolve_chrome_profile_directory()
        typer.echo(f"Chrome profile: {settings.chrome_profile_name} ({directory})")
    except ValueError as exc:
        typer.echo(f"Chrome profile error: {exc}")


@app.command("runs")
def runs(
    limit: Annotated[int, typer.Option(min=1, max=200, help="Maximum rows to show")] = 20,
) -> None:
    """List saved browser runs."""

    _, store = _context()
    saved = store.list(limit)
    if not saved:
        typer.echo("No saved runs yet.")
        return
    typer.echo("ID  STATUS                       STEPS  STARTED (UTC)              URL")
    for run in saved:
        typer.echo(
            f"{run.id:<3} {run.status:<28} {run.steps:<6} "
            f"{run.started_at.isoformat(timespec='seconds'):<26} {run.url}"
        )


@app.command("show")
def show(
    run_id: Annotated[int, typer.Argument(min=1, help="Saved run ID")],
) -> None:
    """Display one saved run as JSON."""

    _, store = _context()
    run = store.get(run_id)
    if run is None:
        typer.echo(f"Run {run_id} was not found.", err=True)
        raise typer.Exit(code=1)
    typer.echo(run.model_dump_json(indent=2))


def news_read_entry() -> None:
    """Entry point for the convenient `news-read URL` executable."""

    typer.run(_run_news_read)


def main() -> None:
    app()
