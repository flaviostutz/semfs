from __future__ import annotations

from dataclasses import dataclass
from typing import TypedDict


@dataclass(frozen=True)
class ChunkDocument:
    file: str
    start_line: int
    end_line: int
    text: str


@dataclass(frozen=True)
class ChunkScore:
    file: str
    start_line: int
    end_line: int
    score: float
    text: str


class IndexRow(TypedDict):
    file: str
    start_line: int
    end_line: int
    text: str
    weights: dict[str, float]
    norm: float


ChunkFinding = TypedDict(
    "ChunkFinding",
    {"from": int, "to": int, "file": str, "contents": str | None},
)
