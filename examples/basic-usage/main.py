from pathlib import Path
from tempfile import TemporaryDirectory

import semfs
from semfs.errors import SemfsError


def _write_sample_docs(root: Path) -> None:
    (root / "alpha.md").write_text("# Intro\nalpha concept\nalpha details\n", encoding="utf-8")
    (root / "beta.md").write_text("# Beta\nbeta concept\n", encoding="utf-8")


def main() -> None:
    config = {
        "name": "example",
        "filter": "**/*.md",
        "mode": "auto",
        "chunking": {"size": 120, "overlap": 30, "edges": "auto"},
        "model": "sentence-transformers/all-MiniLM-L6-v2",
    }
    try:
        with TemporaryDirectory(prefix="semfs-basic-example-") as temp_dir:
            docs_dir = Path(temp_dir) / "docs"
            docs_dir.mkdir(parents=True, exist_ok=True)
            _write_sample_docs(docs_dir)
            state = semfs.index(str(docs_dir), config)
            print(state.status)
            print(semfs.chunks({"text": "alpha", "max_results": 5}, str(docs_dir), fetch_contents=False, config=config))
            print(semfs.files({"text": "alpha", "max_results": 5}, str(docs_dir), config))
    except SemfsError as exc:
        print(exc)


if __name__ == "__main__":
    main()
