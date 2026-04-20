"""Shared test fixtures for the semfs scaffold."""

from pathlib import Path

import pytest

from semfs.synthetic_data import create_dataset


class FakeEmbeddingModel:
    """Deterministic embedding model used by tests."""

    def __init__(self, *_args: object, **_kwargs: object) -> None:
        pass

    def encode(
        self,
        input: list[str],
        *_args: object,
        **_kwargs: object,
    ) -> list[list[float]]:
        return [self._embed(text) for text in input]

    def get_sentence_embedding_dimension(self) -> int:
        return 3

    def _embed(self, text: str) -> list[float]:
        lowered = text.lower()
        return [
            1.0 + lowered.count("alpha") * 10.0,
            1.0 + lowered.count("beta") * 10.0,
            1.0 + lowered.count("gamma") * 10.0,
        ]


@pytest.fixture
def fake_model(monkeypatch: pytest.MonkeyPatch) -> FakeEmbeddingModel:
    embedding_model = FakeEmbeddingModel()
    monkeypatch.setattr("semfs.storage.load_embedding_model", lambda *_args, **_kwargs: embedding_model)
    return embedding_model


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
