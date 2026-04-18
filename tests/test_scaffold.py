import json
from pathlib import Path
from runpy import run_module

import pytest
from typer.testing import CliRunner

import semfs
from semfs.benchmark import write_placeholder_benchmark
from semfs.chunking import chunking_description
from semfs.cli import app
from semfs.config import load_config
from semfs.errors import ConfigError, SemfsError
from semfs.models import IndexStatus
from semfs.synthetic_data import planned_dataset_sizes


def _config_payload() -> dict[str, object]:
    return {
        "name": "index0",
        "filter": "**/*.md",
        "mode": "auto",
        "chunking": {"size": 80, "overlap": 20, "edges": "auto"},
        "model": "sentence-transformers/all-MiniLM-L6-v2",
    }


def test_public_api_returns_scaffold_state(tmp_path: Path) -> None:
    config = _config_payload()
    state = semfs.index(str(tmp_path), config)

    assert state.status is IndexStatus.READY
    assert state.index_name == "index0"
    assert state.database_path.endswith(".semfs/index0/index.db")
    assert semfs.chunks({"text": "what is x?"}, str(tmp_path), fetch_contents=False, config=config) == []
    assert semfs.files({"text": "what is x?"}, str(tmp_path), config) == []


def test_cli_commands_run(tmp_path: Path) -> None:
    runner = CliRunner()
    config_path = tmp_path / ".semfsrc"
    config_path.write_text(json.dumps(_config_payload()), encoding="utf-8")

    help_result = runner.invoke(app, ["--help"])
    version_result = runner.invoke(app, ["--version"])
    index_result = runner.invoke(app, ["index", str(tmp_path), "--config", str(config_path), "--verbose"])
    chunks_result = runner.invoke(
        app, ["chunks", str(tmp_path), "what is x?", "--config", str(config_path), "--top", "5", "--verbose"]
    )
    files_result = runner.invoke(
        app, ["files", str(tmp_path), "what is x?", "--config", str(config_path), "--top", "5", "--verbose"]
    )

    assert help_result.exit_code == 0
    assert version_result.exit_code == 0
    assert index_result.exit_code == 0
    assert chunks_result.exit_code == 0
    assert files_result.exit_code == 0


def test_supporting_helpers_work(tmp_path: Path) -> None:
    artifact = write_placeholder_benchmark(str(tmp_path / "benchmarks"))
    config_path = tmp_path / ".semfsrc"
    config_path.write_text(json.dumps(_config_payload()), encoding="utf-8")
    loaded_config = load_config(config_path)

    assert loaded_config is not None
    assert loaded_config.name == "index0"
    assert chunking_description("auto") == "markdown-aware for markdown files, fixed otherwise"
    assert chunking_description("fixed") == "fixed overlapping windows"
    assert planned_dataset_sizes() == {"small_files": 30, "large_files": 5000}
    assert artifact.exists()
    assert isinstance(SemfsError("boom"), SemfsError)


def test_missing_config_is_reported(tmp_path: Path) -> None:
    missing = tmp_path / ".semfsrc"

    with pytest.raises(ConfigError):
        load_config(missing)


def test_module_entry_point_runs(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("sys.argv", ["semfs", "--help"])

    with pytest.raises(SystemExit) as result:
        run_module("semfs", run_name="__main__")

    assert result.value.code == 0
