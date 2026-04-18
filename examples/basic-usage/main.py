import semfs


def main() -> None:
    state = semfs.index(".", {"name": "example"})
    print(state.status)
    print(semfs.chunks({"text": "what is x?"}, ".", fetch_contents=False, config={}))
    print(semfs.files({"text": "what is x?"}, ".", {}))


if __name__ == "__main__":
    main()
