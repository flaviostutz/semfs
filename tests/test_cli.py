from __future__ import annotations

import json
from pathlib import Path

from semfs.cli import run


def test_cli_files_supports_default_config_file(sample_docs: Path, capsys, monkeypatch) -> None:
    config_path = sample_docs.parent / ".semfsrc"
    config_path.write_text(json.dumps({"mode": "refresh", "filter": "**/*.md"}), encoding="utf-8")
    monkeypatch.chdir(sample_docs.parent)

    exit_code = run(["files", str(sample_docs), "configuration"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Searching files..." in captured.out
    assert "cli.md" in captured.out


def test_cli_chunks_returns_non_zero_on_invalid_model(sample_docs: Path, capsys) -> None:
    exit_code = run(["chunks", str(sample_docs), "configuration", "--model", "missing"])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "unsupported model" in captured.err


def test_cli_index_reports_success(sample_docs: Path, capsys) -> None:
    exit_code = run(["index", str(sample_docs), "--mode", "refresh"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Index created successfully" in captured.out
