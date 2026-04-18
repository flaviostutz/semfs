from pathlib import Path
from tempfile import TemporaryDirectory

import semfs


def main() -> None:
    with TemporaryDirectory() as temp_dir:
        docs_dir = Path(temp_dir)
        (docs_dir / "intro.md").write_text(
            "# Intro\n\nSemfs builds a local index for markdown files and queries chunks by meaning.",
            encoding="utf-8",
        )
        result = semfs.files({"text": "local index"}, str(docs_dir), {"mode": "refresh"})
        print(result)


if __name__ == "__main__":
    main()
