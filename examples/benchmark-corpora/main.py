from pathlib import Path
from tempfile import TemporaryDirectory

from semfs.benchmark import run_benchmark_suite
from semfs.errors import SemfsError


def main() -> None:
    config = {
        "name": "benchmark",
        "filter": "**/*.md",
        "mode": "auto",
        "chunking": {"size": 240, "overlap": 40, "edges": "auto"},
        "model": "sentence-transformers/all-MiniLM-L6-v2",
    }
    output_dir = Path(__file__).resolve().parents[2] / "benchmarks"
    try:
        with TemporaryDirectory(prefix="semfs-benchmark-example-") as temp_dir:
            for result in run_benchmark_suite(Path(temp_dir), config, "alpha", output_dir=output_dir, verbose=True):
                print(result.artifact_path)
    except SemfsError as exc:
        print(exc)


if __name__ == "__main__":
    main()