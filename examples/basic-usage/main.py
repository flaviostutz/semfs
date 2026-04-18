import semfs
from semfs.errors import SemfsError


def main() -> None:
    config = {
        "name": "example",
        "filter": "**/*.md",
        "mode": "auto",
        "chunking": {"size": 120, "overlap": 30, "edges": "auto"},
        "model": "sentence-transformers/all-MiniLM-L6-v2",
    }
    try:
        state = semfs.index(".", config)
        print(state.status)
        print(semfs.chunks({"text": "what is x?"}, ".", fetch_contents=False, config=config))
        print(semfs.files({"text": "what is x?"}, ".", config))
    except SemfsError as exc:
        print(exc)


if __name__ == "__main__":
    main()
