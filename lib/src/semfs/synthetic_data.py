"""Deterministic synthetic corpora for semfs benchmarks and integration tests."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class DatasetSpec:
    """Shape metadata for one deterministic benchmark dataset."""

    name: str
    folder_count: int
    file_count: int
    max_depth: int


def dataset_spec(name: str) -> DatasetSpec:
    """Return the fixed dataset shape for one named benchmark corpus."""
    specs = {
        "small": DatasetSpec(name="small", folder_count=5, file_count=30, max_depth=3),
        "large": DatasetSpec(name="large", folder_count=300, file_count=5000, max_depth=7),
    }
    try:
        return specs[name]
    except KeyError as exc:
        message = f"Unknown dataset: {name}"
        raise ValueError(message) from exc


def planned_dataset_sizes() -> dict[str, int]:
    """Return the planned corpus sizes from the feature spec."""
    return {"small_files": dataset_spec("small").file_count, "large_files": dataset_spec("large").file_count}


def _folder_paths(spec: DatasetSpec) -> list[Path]:
    folders: list[Path] = []
    for index in range(spec.folder_count):
        depth = 1 + (index % spec.max_depth)
        parts = [f"level-{level:02d}" for level in range(1, depth)] + [f"group-{index:03d}"]
        folders.append(Path(*parts))
    return folders


def _document_text(dataset_name: str, file_index: int) -> str:
    topics = ("alpha", "beta", "gamma")
    primary = topics[file_index % len(topics)]
    secondary = topics[(file_index + 1) % len(topics)]
    tertiary = topics[(file_index + 2) % len(topics)]
    return (
        f"# {dataset_name.title()} Document {file_index}\n"
        f"{primary} topic overview for document {file_index}.\n\n"
        f"## Details\n"
        f"{primary} and {secondary} appear together in this deterministic corpus entry.\n"
        f"{tertiary} is mentioned for ranking contrast.\n"
    )


def create_dataset(root: Path, name: str) -> DatasetSpec:
    """Create one deterministic markdown corpus on disk and return its shape metadata."""
    spec = dataset_spec(name)
    root.mkdir(parents=True, exist_ok=True)
    folders = _folder_paths(spec)
    for folder in folders:
        (root / folder).mkdir(parents=True, exist_ok=True)

    for file_index in range(spec.file_count):
        folder = folders[file_index % len(folders)]
        file_path = root / folder / f"doc-{file_index:04d}.md"
        file_path.write_text(_document_text(spec.name, file_index), encoding="utf-8")

    return spec
