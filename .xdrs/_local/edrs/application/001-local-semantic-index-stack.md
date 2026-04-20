---
name: _local-edr-001-local-semantic-index-stack
description: Defines the engineering stack for semfs semantic indexing, querying, and CLI delivery. Use when implementing or reviewing the semfs MVP.
applied-to: semfs Python package
---

# _local-edr-001: Local Semantic Index Stack

## Context and Problem Statement

The feature requires a local-first semantic search library and CLI, but the repository currently has no implementation stack. Which engineering stack should implement the semfs MVP?

## Decision Outcome

**Use uv-managed Python with Typer, JSON config, sentence-transformers embeddings, and ChromaDB local indexes**

semfs must ship as a Python library plus thin CLI. The CLI owns `.semfsrc` discovery and `--config` overrides, embeddings are produced through a local sentence-transformers model, and named indexes are stored in ChromaDB under `{dir}/.semfs/<index-name>` for persisted vector storage and nearest-neighbor search.

### Implementation Details

- Scaffold the project with `pyproject.toml`, root `Makefile`, Ruff, Pyright, pytest, and examples per agentme Python tooling rules.
- Keep command handling in `cli.py` and domain behavior in library modules.
- Use JSON for `.semfsrc` so config discovery matches the shared CLI standard.
- Treat `chunking.edges="auto"` as markdown-aware chunking for markdown files and fixed chunking otherwise; `chunking.edges="fixed"` always uses fixed chunking.
- Persist file metadata and per-file content digests in ChromaDB metadata collections, and persist/query chunk embeddings with retrieval fields `file_path`, `start_line`, and `end_line` through a dedicated chunks collection while sentence-transformers computes vectors outside ChromaDB.
- Use ChromaDB ephemeral client for `inmemory` mode and a temporary on-disk ChromaDB directory deleted after use for `transient` mode so both remain non-persistent while exercising distinct runtime paths.
- Treat ChromaDB as the default local vector-search engine for the MVP because benchmark scalability issues made the SQLite plus sqlite-vec approach insufficient.
- Generate benchmark corpora deterministically during tests instead of committing large fixture trees, and persist benchmark timing artifacts under the repository-level `benchmarks/` directory.

## References

- [agentme-edr-014](../../../agentme/edrs/application/014-python-project-tooling.md) - Python packaging and workflow baseline
- [agentme-edr-015](../../../agentme/edrs/application/015-cli-tool-standards.md) - CLI structure and config ownership rules
- [agentme-edr-009](../../../agentme/edrs/principles/009-error-handling.md) - Error surfacing expectations
- [Research document](../../../../specs/001-semantic-file-query/research.md) - Evidence and tradeoffs for this stack