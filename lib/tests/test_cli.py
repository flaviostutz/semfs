import json
from pathlib import Path

from typer.testing import CliRunner

from semfs.cli import app


def _config_payload(mode: str = "auto") -> dict[str, object]:
    return {
        "name": "index0",
        "filter": "**/*.md",
        "mode": mode,
        "chunking": {"size": 80, "overlap": 20, "edges": "auto"},
    }


def test_chunks_cli_outputs_ranked_headers(sample_docs: Path, fake_model: object, tmp_path: Path) -> None:
    _ = fake_model
    runner = CliRunner()
    config_path = tmp_path / ".semfsrc"
    config_path.write_text(json.dumps(_config_payload()), encoding="utf-8")

    result = runner.invoke(
        app,
        ["chunks", str(sample_docs), "alpha", "--config", str(config_path), "--top", "5", "--contents"],
    )

    assert result.exit_code == 0
    assert "alpha.md[1:" in result.output
    assert "alpha concept" in result.output


def test_index_cli_uses_default_config_when_semfsrc_is_missing(sample_docs: Path, fake_model: object) -> None:
    _ = fake_model
    runner = CliRunner()

    result = runner.invoke(app, ["index", str(sample_docs), "--verbose"])

    assert result.exit_code == 0
    assert "Starting index 'index0'" in result.output
    assert ".semfs/index0" in result.output


def test_index_cli_verbose_logs_announce_work_before_reporting_timing(sample_docs: Path, fake_model: object) -> None:
    _ = fake_model
    runner = CliRunner()

    result = runner.invoke(app, ["index", str(sample_docs), "--verbose"])

    assert result.exit_code == 0
    lines = result.output.splitlines()
    prepare_before = next(index for index, line in enumerate(lines) if "Preparing index 'index0'" in line)
    prepare_after = next(index for index, line in enumerate(lines) if "Prepared index 'index0'" in line)
    open_before = next(index for index, line in enumerate(lines) if "Opening Chroma store at" in line)
    open_after = next(index for index, line in enumerate(lines) if "Opened Chroma store at" in line)

    assert prepare_before < prepare_after
    assert open_before < open_after
    assert " in " in lines[prepare_after]
    assert " in " in lines[open_after]


def test_files_cli_uses_default_config_when_semfsrc_is_missing(sample_docs: Path, fake_model: object) -> None:
    _ = fake_model
    runner = CliRunner()

    result = runner.invoke(app, ["files", str(sample_docs), "alpha", "--top", "5"])

    assert result.exit_code == 0
    assert result.output.splitlines() == ["alpha.md", "beta.md"]


def test_chunks_cli_reports_actionable_digest_errors(sample_docs: Path, fake_model: object, tmp_path: Path) -> None:
    _ = fake_model
    runner = CliRunner()
    config_path = tmp_path / ".semfsrc"
    config_path.write_text(json.dumps(_config_payload(mode="stale")), encoding="utf-8")

    index_result = runner.invoke(app, ["index", str(sample_docs), "--config", str(config_path)])
    assert index_result.exit_code == 0

    (sample_docs / "alpha.md").write_text("# Intro\nchanged\n", encoding="utf-8")

    result = runner.invoke(
        app,
        ["chunks", str(sample_docs), "alpha", "--config", str(config_path), "--top", "5", "--contents"],
    )

    assert result.exit_code == 1
    assert "live file no longer matches the indexed snapshot" in result.output


def test_files_cli_outputs_ranked_deduplicated_paths(sample_docs: Path, fake_model: object, tmp_path: Path) -> None:
    _ = fake_model
    runner = CliRunner()
    config_path = tmp_path / ".semfsrc"
    config_path.write_text(json.dumps(_config_payload()), encoding="utf-8")

    result = runner.invoke(app, ["files", str(sample_docs), "alpha", "--config", str(config_path), "--top", "5"])

    assert result.exit_code == 0
    assert result.output.splitlines() == ["alpha.md", "beta.md"]


def test_files_cli_breaks_ties_by_path(sample_docs: Path, fake_model: object, tmp_path: Path) -> None:
    _ = fake_model
    runner = CliRunner()
    config_path = tmp_path / ".semfsrc"
    config_path.write_text(json.dumps(_config_payload()), encoding="utf-8")
    (sample_docs / "aardvark.md").write_text("# Aardvark\nalpha\n", encoding="utf-8")
    (sample_docs / "zebra.md").write_text("# Zebra\nalpha\n", encoding="utf-8")

    result = runner.invoke(app, ["files", str(sample_docs), "alpha", "--config", str(config_path), "--top", "2"])

    assert result.exit_code == 0
    assert result.output.splitlines() == ["aardvark.md", "zebra.md"]
