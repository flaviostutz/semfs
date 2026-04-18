import semfs


def main() -> None:
    config = {
        "name": "example",
        "filter": "**/*.md",
        "mode": "auto",
        "chunking": {"size": 120, "overlap": 30, "edges": "auto"},
        "model": "sentence-transformers/all-MiniLM-L6-v2",
    }
    state = semfs.index(".", config)
    print(state.status)
    print(semfs.chunks({"text": "what is x?"}, ".", fetch_contents=False, config=config))
    print(semfs.files({"text": "what is x?"}, ".", config))


if __name__ == "__main__":
    main()
