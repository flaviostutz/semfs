from pathlib import Path

import semfs
from semfs.errors import SemfsError


def _sample_corpus_dir() -> Path:
    return Path(__file__).parent / "sample-corpus"


def main() -> None:
    print('Starting basic usage example')
    docs_dir = _sample_corpus_dir()
    config = {
        "name": "example",
        "filter": "**/*",
        "mode": "transient",
        "chunking": {"size": 120, "overlap": 30, "edges": "auto"},
        "model": {
            "name": "all-MiniLM-L6-v2",
        },
    }
    try:
        print(f'Using committed sample corpus at {docs_dir}')

        print('Creating semfs index')
        state = semfs.index(str(docs_dir), config, verbose=True)
        print(state.status)
        assert state.indexed_files > 0, f"Expected indexed files, got {state.indexed_files}"
        assert state.indexed_chunks > 0, f"Expected indexed chunks, got {state.indexed_chunks}"
        print(f'Assertions passed: {state.indexed_files} files, {state.indexed_chunks} chunks indexed')

        print('Performing chunk search: water leak sensor calibration steps')
        chunk_results = semfs.chunks(
            {"text": "how to calibrate a water leak sensor after battery replacement?", "max_results": 5},
            str(docs_dir),
            fetch_contents=True,
            config=config,
            verbose=True,
        )
        print(chunk_results)
        chunk_files = [r.file for r in chunk_results]
        assert any('water-leak-sensor-calibration' in f for f in chunk_files), \
            f"Expected water-leak-sensor-calibration in chunk results, got: {chunk_files}"
        assert any(r.contents and 'Calibrat' in r.contents for r in chunk_results), \
            "Expected calibration content in chunk text"
        print('Chunk search assertions passed')

        print('Performing file search: dispatch rules for same-day visits')
        file_results = semfs.files(
            {"text": "rules for coordinating same-day technician dispatch to customer homes", "max_results": 5},
            str(docs_dir),
            config,
            verbose=True,
        )
        print(file_results)
        assert len(file_results) > 0, "Expected at least one file result"
        file_paths = [r.file for r in file_results]
        assert any('dispatch-playbook' in f for f in file_paths), \
            f"Expected dispatch-playbook in file results, got: {file_paths}"
        print('File search assertions passed')

    except SemfsError as exc:
        print(exc)
        raise


if __name__ == "__main__":
    main()
