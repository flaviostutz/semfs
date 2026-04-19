"""Shared test fixtures for the semfs scaffold."""

import math
from pathlib import Path

import pytest

from semfs.synthetic_data import create_dataset


class FakeEmbeddingModel:
    """Deterministic embedding model used by tests."""

    def get_sentence_embedding_dimension(self) -> int:
        return 3

    def encode(self, texts: list[str], *, normalize_embeddings: bool = False) -> list[list[float]]:
        vectors = [self._embed(text) for text in texts]
        if not normalize_embeddings:
            return vectors

        normalized: list[list[float]] = []
        for vector in vectors:
            norm = math.sqrt(sum(value * value for value in vector))
            normalized.append([value / norm for value in vector])
        return normalized

    def _embed(self, text: str) -> list[float]:
        lowered = text.lower()
        return [
            1.0 + lowered.count("alpha") * 10.0,
            1.0 + lowered.count("beta") * 10.0,
            1.0 + lowered.count("gamma") * 10.0,
        ]


@pytest.fixture
def fake_model(monkeypatch: pytest.MonkeyPatch) -> FakeEmbeddingModel:
    model = FakeEmbeddingModel()
    monkeypatch.setattr("semfs.indexer.load_embedding_model", lambda _model_name: model)
    monkeypatch.setattr("semfs.search.load_embedding_model", lambda _model_name: model)
    return model


@pytest.fixture
def sample_docs(tmp_path: Path) -> Path:
    root = tmp_path / "docs"
    root.mkdir()
    (root / "alpha.md").write_text(
        "# Intro\nalpha concept\nalpha details\n\n## More\nalpha again\nalpha wrap\n",
        encoding="utf-8",
    )
    (root / "beta.md").write_text("# Beta\nbeta material\n", encoding="utf-8")
    (root / "binary.bin").write_bytes(b"\xff\xfe\x00\x00")
    return root


@pytest.fixture
def small_corpus(tmp_path: Path) -> Path:
    root = tmp_path / "small-corpus"
    create_dataset(root, "small")
    return root


@pytest.fixture
def large_corpus(tmp_path: Path) -> Path:
    root = tmp_path / "large-corpus"
    create_dataset(root, "large")
    return root
