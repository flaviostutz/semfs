from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from .config import SearchConfig, config_to_dict
from .models import IndexRow


def metadata_path(directory: Path, config: SearchConfig) -> Path:
    return directory / ".semfs" / f"{config.name}.json"


def database_path(directory: Path, config: SearchConfig) -> Path:
    return directory / ".semfs" / f"{config.name}.db"


def load_metadata(directory: Path, config: SearchConfig) -> dict[str, Any] | None:
    path = metadata_path(directory, config)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def save_index(
    directory: Path,
    config: SearchConfig,
    fingerprint: str,
    file_count: int,
    chunk_count: int,
    idf: dict[str, float],
    rows: list[IndexRow],
) -> dict[str, Any]:
    semfs_dir = directory / ".semfs"
    semfs_dir.mkdir(parents=True, exist_ok=True)

    db_path = database_path(directory, config)
    connection = sqlite3.connect(db_path)
    try:
        cursor = connection.cursor()
        cursor.execute("DROP TABLE IF EXISTS chunks")
        cursor.execute(
            "CREATE TABLE chunks ("
            "file TEXT, "
            "start_line INTEGER, "
            "end_line INTEGER, "
            "text TEXT, "
            "weights_json TEXT, "
            "norm REAL"
            ")"
        )
        cursor.executemany(
            "INSERT INTO chunks ("
            "file, start_line, end_line, text, weights_json, norm"
            ") VALUES (?, ?, ?, ?, ?, ?)",
            [
                (
                    str(row["file"]),
                    int(row["start_line"]),
                    int(row["end_line"]),
                    str(row["text"]),
                    json.dumps(row["weights"], sort_keys=True),
                    float(row["norm"]),
                )
                for row in rows
            ],
        )
        connection.commit()
    finally:
        connection.close()

    metadata = {
        "schema_version": 1,
        "name": config.name,
        "config": config_to_dict(config),
        "file_count": file_count,
        "chunk_count": chunk_count,
        "fingerprint": fingerprint,
        "idf": idf,
        "database": db_path.name,
    }
    metadata_path(directory, config).write_text(
        json.dumps(metadata, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return metadata


def load_chunk_rows(directory: Path, config: SearchConfig) -> list[IndexRow]:
    connection = sqlite3.connect(database_path(directory, config))
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT file, start_line, end_line, text, weights_json, norm FROM chunks")
        rows = cursor.fetchall()
    finally:
        connection.close()
    return [
        {
            "file": file_name,
            "start_line": start_line,
            "end_line": end_line,
            "text": text,
            "weights": json.loads(weights_json),
            "norm": norm,
        }
        for file_name, start_line, end_line, text, weights_json, norm in rows
    ]
