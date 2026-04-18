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
        "model": "sentence-transformers/all-MiniLM-L6-v2",
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
