"""Shared test fixtures for the semfs scaffold."""

from pathlib import Path

import pytest

from semfs.synthetic_data import create_dataset


class FakeChromaEmbeddingFunction:
    """Deterministic embedding function used by tests."""

    def __init__(self, *_args: object, **_kwargs: object) -> None:
        pass

    def __call__(self, input: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in input]

    def embed_query(self, input: list[str]) -> list[list[float]]:
        return self.__call__(input)

    def name(self) -> str:
        return "default"

    @staticmethod
    def build_from_config(_config: dict[str, object]) -> "FakeChromaEmbeddingFunction":
        return FakeChromaEmbeddingFunction()

    def get_config(self) -> dict[str, object]:
        return {}

    def _embed(self, text: str) -> list[float]:
        lowered = text.lower()
        return [
            1.0 + lowered.count("alpha") * 10.0,
            1.0 + lowered.count("beta") * 10.0,
            1.0 + lowered.count("gamma") * 10.0,
        ]


@pytest.fixture
def fake_model(monkeypatch: pytest.MonkeyPatch) -> FakeChromaEmbeddingFunction:
    embedding_function = FakeChromaEmbeddingFunction()
    monkeypatch.setattr("semfs.storage.default_embedding_function", lambda: embedding_function)
    return embedding_function


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
