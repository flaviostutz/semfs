from __future__ import annotations

import math
from collections import defaultdict
from pathlib import Path

from .config import Query
from .indexer import tokenize
from .models import ChunkFinding, ChunkScore, IndexRow


def search_chunks(
    rows: list[IndexRow],
    idf: dict[str, float],
    query: Query,
) -> list[ChunkScore]:
    query_weights = _query_weights(query.text, idf)
    if not query_weights:
        return []
    query_norm = math.sqrt(sum(weight * weight for weight in query_weights.values())) or 1.0
    matches: list[ChunkScore] = []
    for row in rows:
        weights = row["weights"]
        dot_product = sum(query_weights.get(term, 0.0) * weight for term, weight in weights.items())
        if dot_product <= 0:
            continue
        score = dot_product / (query_norm * float(row["norm"]))
        distance = 1.0 - score
        if query.max_distance is not None and distance > query.max_distance:
            continue
        matches.append(
            ChunkScore(
                file=str(row["file"]),
                start_line=int(row["start_line"]),
                end_line=int(row["end_line"]),
                score=score,
                text=str(row["text"]),
            )
        )
    matches.sort(key=lambda item: item.score, reverse=True)
    return matches[: query.max_results]


def merge_chunk_scores(scores: list[ChunkScore], fetch_contents: bool) -> list[ChunkFinding]:
    grouped: dict[str, list[ChunkScore]] = defaultdict(list)
    for score in scores:
        grouped[score.file].append(score)

    merged: list[ChunkFinding] = []
    for file_name, file_scores in grouped.items():
        file_scores.sort(key=lambda item: item.start_line)
        current = file_scores[0]
        current_texts = [current.text]
        for next_score in file_scores[1:]:
            if next_score.start_line <= current.end_line + 1:
                current = ChunkScore(
                    file=file_name,
                    start_line=current.start_line,
                    end_line=max(current.end_line, next_score.end_line),
                    score=max(current.score, next_score.score),
                    text=current.text,
                )
                current_texts.append(next_score.text)
                continue
            merged.append(_finding_dict(current, current_texts, fetch_contents))
            current = next_score
            current_texts = [next_score.text]
        merged.append(_finding_dict(current, current_texts, fetch_contents))
    merged.sort(key=lambda finding: (finding["file"], finding["from"]))
    return merged


def deduplicate_files(scores: list[ChunkScore]) -> list[str]:
    best_scores: dict[str, float] = {}
    for score in scores:
        previous = best_scores.get(score.file)
        if previous is None or score.score > previous:
            best_scores[score.file] = score.score
    return [
        file_name
        for file_name, _ in sorted(best_scores.items(), key=lambda item: item[1], reverse=True)
    ]


def _query_weights(text: str, idf: dict[str, float]) -> dict[str, float]:
    counts: dict[str, int] = {}
    for token in tokenize(text):
        if token not in idf:
            continue
        counts[token] = counts.get(token, 0) + 1
    return {term: count * idf[term] for term, count in counts.items()}


def _finding_dict(score: ChunkScore, texts: list[str], fetch_contents: bool) -> ChunkFinding:
    return {
        "from": score.start_line,
        "to": score.end_line,
        "file": score.file,
        "contents": "\n".join(texts) if fetch_contents else None,
    }


def format_chunk_reference(base_dir: Path, finding: ChunkFinding) -> str:
    relative = Path(str(finding["file"]))
    if relative.is_absolute():
        relative = relative.relative_to(base_dir)
    return f"{relative.as_posix()}[{finding['from']}:{finding['to']}]"
