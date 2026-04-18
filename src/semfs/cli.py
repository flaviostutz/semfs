"""Typer CLI scaffold for semfs."""

from pathlib import Path
from typing import Annotated

import typer

import semfs
from semfs.benchmark import write_placeholder_benchmark
from semfs.config import load_config
from semfs.errors import SemfsError
from semfs.models import IndexConfig

app = typer.Typer(help="Semantic file queries for local folders.")


def _require_loaded_config(config_path: Path | None) -> IndexConfig:
    loaded_config = load_config(config_path)
    if loaded_config is None:
        raise typer.Exit(code=1)
    return loaded_config


def version_callback(value: bool | None) -> None:
    """Print the package version when requested from the root command."""
    if value:
        typer.echo(semfs.__version__)
        raise typer.Exit


@app.callback()
def root(
    version: Annotated[
        bool | None,
        typer.Option("--version", callback=version_callback, help="Show package version and exit.", is_eager=True),
    ] = None,
) -> None:
    """Handle root-level CLI flags."""
    _ = version


@app.command()
def index(
    directory: Path,
    config: Annotated[Path | None, typer.Option("--config", help="Path to a JSON config file.")] = None,
    verbose: Annotated[bool, typer.Option("--verbose", help="Show extra detail.")] = False,
) -> None:
    """Create or refresh the scaffolded index state."""
    try:
        loaded_config = _require_loaded_config(config)
        typer.echo(f"Starting index '{loaded_config.name}' for {directory}")
        state = semfs.index(str(directory), loaded_config)
        if verbose:
            typer.echo(f"Using output path: {state.database_path}")
        typer.echo(f"Indexed {state.indexed_files} files and {state.indexed_chunks} chunks")
    except SemfsError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc


@app.command()
def chunks(
    directory: Path,
    query: str,
    top: Annotated[int, typer.Option("--top", min=1, help="Maximum number of results.")] = 10,
    distance: Annotated[float | None, typer.Option("--distance", min=0.0, help="Optional distance limit.")] = None,
    contents: Annotated[bool, typer.Option("--contents", help="Include excerpt contents.")] = False,
    config: Annotated[Path | None, typer.Option("--config", help="Path to a JSON config file.")] = None,
    verbose: Annotated[bool, typer.Option("--verbose", help="Show extra detail.")] = False,
) -> None:
    """Return chunk query results."""
    try:
        loaded_config = _require_loaded_config(config)
        results = semfs.chunks(
            {"text": query, "max_results": top, "max_distance": distance}, str(directory), contents, loaded_config
        )
        for finding in results:
            typer.echo(f"{finding.file}[{finding.from_line}:{finding.to_line}]")
            if contents and finding.contents is not None:
                typer.echo(finding.contents)
        if verbose:
            typer.echo(f"Returned {len(results)} chunk results for {directory}")
    except SemfsError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc


@app.command()
def files(
    directory: Path,
    query: str,
    top: Annotated[int, typer.Option("--top", min=1, help="Maximum number of results.")] = 10,
    distance: Annotated[float | None, typer.Option("--distance", min=0.0, help="Optional distance limit.")] = None,
    config: Annotated[Path | None, typer.Option("--config", help="Path to a JSON config file.")] = None,
    verbose: Annotated[bool, typer.Option("--verbose", help="Show extra detail.")] = False,
) -> None:
    """Return scaffolded file results."""
    try:
        loaded_config = _require_loaded_config(config)
        results = semfs.files(
            {"text": query, "max_results": top, "max_distance": distance}, str(directory), loaded_config
        )
        if verbose:
            typer.echo(f"Returned {len(results)} scaffold file results for {directory}")
    except SemfsError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc


@app.command("benchmark-scaffold")
def benchmark_scaffold(
    output_dir: Annotated[Path, typer.Option("--output-dir", help="Benchmark artifact directory.")] = Path(
        "benchmarks"
    ),
) -> None:
    """Write a placeholder benchmark artifact for the scaffold."""
    artifact = write_placeholder_benchmark(str(output_dir))
    typer.echo(f"Wrote placeholder benchmark artifact to {artifact}")


def main() -> None:
    """Run the CLI application."""
    app()
