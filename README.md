# semfs

Semantic file queries for local folders via a Python library and CLI.

## Getting Started

```sh
make test
```

The published Python package lives in `lib/` and runnable consumer projects live in `examples/`.

## Repository Layout

- `lib/` contains the package source, tests, package metadata, lockfile, and library-specific Makefile.
- `examples/` contains independent consumer projects that exercise the package as an installed dependency.
- `benchmarks/` stores benchmark timing artifacts written by benchmark flows.
- `specs/` and `.xdrs/` capture the active feature and decision records for the repository.

## Common Commands

```sh
make install
make build
make lint-fix
make test
make run
```

`make test` runs library unit tests, integration tests, and the consumer examples. Example verification installs the wheel built into `lib/dist/` before each run so examples exercise the package as a consumer would.

## Package Usage

User-facing CLI and library examples live in `lib/README.md`.

From a source checkout, install the shared environment first and then run the package through `lib/`:

```sh
UV_PROJECT_ENVIRONMENT="$PWD/.venv" uv run --project lib semfs --help
```

## Benchmark Example

Run the benchmark consumer project against the built wheel when you want fresh artifacts under `benchmarks/`:

```sh
make build
UV_PROJECT_ENVIRONMENT="$PWD/.venv" UV_CACHE_DIR="$PWD/.cache/uv" uv sync --project examples/benchmark-corpora --frozen
UV_PROJECT_ENVIRONMENT="$PWD/.venv" UV_CACHE_DIR="$PWD/.cache/uv" uv pip install --python "$PWD/.venv/bin/python" --force-reinstall lib/dist/*.whl
UV_PROJECT_ENVIRONMENT="$PWD/.venv" UV_CACHE_DIR="$PWD/.cache/uv" uv run --project examples/benchmark-corpora python examples/benchmark-corpora/main.py
```
