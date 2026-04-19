# semfs

Semantic file queries for local folders via a Python library and CLI.

## Getting Started

```sh
make setup
make test
```

```sh
make run
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

From a source checkout, prepare the shared environment once and then use the root Makefile targets:

```sh
make setup
make run
```

## Benchmark Example

Run the benchmark consumer project against the built wheel when you want fresh artifacts under `benchmarks/`:

```sh
make setup
make build
make -C examples/benchmark-corpora run
```
