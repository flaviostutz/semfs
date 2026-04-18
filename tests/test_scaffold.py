from pathlib import Path
from runpy import run_module

import pytest
from typer.testing import CliRunner

import semfs
from semfs.benchmark import write_placeholder_benchmark
from semfs.chunking import chunking_description
from semfs.cli import app
from semfs.config import load_config
from semfs.errors import SemfsError
from semfs.synthetic_data import planned_dataset_sizes


def test_public_api_returns_scaffold_state(tmp_path: Path) -> None:
    state = semfs.index(str(tmp_path), {"name": "index0"})

    assert state.status == "scaffold"
    assert state.index_name == "index0"
    assert semfs.chunks({"text": "what is x?"}, str(tmp_path), fetch_contents=False, config={}) == []
    assert semfs.files({"text": "what is x?"}, str(tmp_path), {}) == []


def test_cli_commands_run(tmp_path: Path) -> None:
    runner = CliRunner()

    help_result = runner.invoke(app, ["--help"])
    version_result = runner.invoke(app, ["--version"])
    index_result = runner.invoke(app, ["index", str(tmp_path), "--verbose"])
    chunks_result = runner.invoke(app, ["chunks", str(tmp_path), "what is x?", "--top", "5", "--verbose"])
    files_result = runner.invoke(app, ["files", str(tmp_path), "what is x?", "--top", "5", "--verbose"])

    assert help_result.exit_code == 0
    assert version_result.exit_code == 0
    assert index_result.exit_code == 0
    assert chunks_result.exit_code == 0
    assert files_result.exit_code == 0


def test_supporting_helpers_work(tmp_path: Path) -> None:
    artifact = write_placeholder_benchmark(str(tmp_path / "benchmarks"))

    assert load_config() == {}
    assert chunking_description("auto") == "markdown-aware for markdown files, fixed otherwise"
    assert chunking_description("fixed") == "fixed overlapping windows"
    assert planned_dataset_sizes() == {"small_files": 30, "large_files": 5000}
    assert artifact.exists()
    assert isinstance(SemfsError("boom"), SemfsError)


def test_module_entry_point_runs(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("sys.argv", ["semfs", "--help"])

    with pytest.raises(SystemExit) as result:
        run_module("semfs", run_name="__main__")

    assert result.value.code == 0
