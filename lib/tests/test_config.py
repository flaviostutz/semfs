import json
from pathlib import Path

import pytest

from semfs.config import default_index_config, load_config, parse_index_config, parse_query_request, resolve_config_path
from semfs.errors import ConfigError
from semfs.models import ChunkingEdges, IndexMode


def _config_payload() -> dict[str, object]:
    return {
        "name": "index0",
        "filter": "**/*.md",
        "mode": "auto",
        "chunking": {"size": 120, "overlap": 30, "edges": "auto"},
        "model": "sentence-transformers/all-MiniLM-L6-v2",
    }


def test_load_config_validates_json_file(tmp_path: Path) -> None:
    config_path = tmp_path / ".semfsrc"
    config_path.write_text(json.dumps(_config_payload()), encoding="utf-8")

    config = load_config(config_path)

    assert config is not None
    assert config.mode is IndexMode.AUTO
    assert config.chunking.edges is ChunkingEdges.AUTO


def test_invalid_chunking_is_rejected() -> None:
    invalid = _config_payload()
    invalid["chunking"] = {"size": 50, "overlap": 50, "edges": "fixed"}

    with pytest.raises(ConfigError):
        parse_index_config(invalid)


def test_query_request_defaults() -> None:
    query = parse_query_request({"text": "  hello world  "})

    assert query.text == "hello world"
    assert query.max_results == 10
    assert query.max_distance is None


def test_resolve_config_path_uses_default_name(tmp_path: Path) -> None:
    resolved = resolve_config_path(cwd=tmp_path)

    assert resolved == tmp_path / ".semfsrc"


def test_all_index_modes_are_accepted() -> None:
    for mode in ["refresh", "auto", "stale", "inmemory", "transient"]:
        config = parse_index_config({**_config_payload(), "mode": mode})
        assert config.mode.value == mode


def test_invalid_index_mode_is_rejected() -> None:
    with pytest.raises(ConfigError):
        parse_index_config({**_config_payload(), "mode": "unsupported"})


def test_default_index_config_matches_cli_defaults() -> None:
    config = default_index_config()

    assert config.name == "index0"
    assert config.filter == "**/*"
    assert config.mode is IndexMode.AUTO
    assert config.chunking.size == 500
    assert config.chunking.overlap == 250
    assert config.chunking.edges is ChunkingEdges.AUTO
    assert config.model == "sentence-transformers/all-MiniLM-L6-v2"
