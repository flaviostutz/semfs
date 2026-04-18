# Research: Semantic File Query Library and CLI

## 1. Semantic retrieval stack

**Decision**: Use `sentence-transformers` with a local default model (`all-MiniLM-L6-v2`) and persist file metadata in regular SQLite tables plus chunk embeddings and result fields in a single `sqlite-vec` `vec0` table inside a named SQLite index under `{dir}/.semfs/<index-name>/index.db`.

**Rationale**: This keeps the index as a single local portable artifact while avoiding the query-time cost of scanning every stored embedding in Python. Collapsing chunk metadata and vectors into one `vec0` table removes an unnecessary join from the MVP design and keeps query logic simpler, while `file_snapshots` remains a regular table for freshness and digest checks. It also preserves offline execution and keeps `refresh`, `auto`, `stale`, `inmemory`, and `transient` modes implementable without a separate service.

**Alternatives considered**:
- SQLite plus in-process cosine similarity: simpler to prototype, but it pushes nearest-neighbor work into Python and scales worse for repeated top-k local queries over the planned benchmark corpora.
- ChromaDB: higher-level vector database API, but it does not fit the desired single-file per-index storage model as cleanly and adds more database/product surface than the CLI needs.
- FAISS or a dedicated vector database: useful at larger scales, but unnecessary for the current benchmark scope and more complex to distribute with `uvx`.
- Remote embedding APIs: rejected because the feature must work locally and offline.

## 2. CLI and packaging stack

**Decision**: Use Typer for the CLI, `pyproject.toml` plus uv for packaging, and a console entry point exposed as `semfs` for `uvx` execution.

**Rationale**: Typer naturally supports `index`, `chunks`, and `files` subcommands, generates help/version handling with little boilerplate, and keeps the CLI as a thin adapter over library functions. uv-managed packaging aligns with the repository standards and gives a direct `uvx semfs ...` distribution path.

**Alternatives considered**:
- `argparse`: lower dependency count but more verbose and slower to evolve for a multi-command CLI.
- Click directly: viable, but Typer gives the same runtime model with better type-driven ergonomics.
- Poetry or setuptools-first packaging: heavier or noisier than the uv + `pyproject.toml` baseline required by the repo standards.

## 3. Config format and discovery

**Decision**: Treat `.semfsrc` as a JSON configuration file discovered from the current working directory by default, with `--config` as the explicit override.

**Rationale**: The spec already fixes the filename and `--config` behavior. JSON keeps discovery aligned with the CLI standard, maps directly to the configuration object in the feature spec, and avoids introducing another serialization format before the project has even been scaffolded.

**Alternatives considered**:
- TOML: attractive for Python tooling, but it diverges from the CLI standard's default JSON expectation for `.[cli-name]rc` files.
- YAML: more flexible but adds parser overhead and looser validation than needed for the current config shape.

## 4. Auto-mode freshness detection

**Decision**: Record file path, size, and modification time for every indexed file, and in `auto` mode rebuild the full index whenever any tracked file is added, removed, or changed.

**Rationale**: This keeps freshness checks deterministic and portable across local filesystems, avoids long content hashing during every query, and fits the current scale better than implementing incremental re-indexing first.

**Alternatives considered**:
- Content hashing every file on every query: more accurate, but unnecessarily expensive for the MVP.
- Filesystem watchers: useful for live syncing, but much more operationally complex than the spec requires.

## 5. Chunking and chunk merge policy

**Decision**: Implement fixed chunking as overlapping character windows with recorded line ranges, and treat `chunking.edges="auto"` as heading/block-aware chunking for markdown files plus fixed chunking for all other files, while `chunking.edges="fixed"` always uses fixed chunking. Persist no file contents in the index, store a per-file content digest in snapshot metadata, store only the retrieval fields `file_path`, `start_line`, and `end_line` alongside embeddings in one `vec0` table, and merge only directly contiguous chunk results from the same file.

**Rationale**: The spec's `size` and `overlap` fields map naturally to character windows, while markdown-aware grouping preserves human-readable sections. Recording only the line-range retrieval fields at chunk-creation time keeps result merging deterministic and allows the index to stay small, because excerpt text can be read from the live file only when requested and only if its digest still matches the indexed snapshot.

**Alternatives considered**:
- Token-based chunking: more model-aware, but introduces tokenization dependencies and ambiguity around cross-model sizing.
- Paragraph-only chunking: simpler for markdown, but too inconsistent for non-markdown files and large flat text documents.

## 6. Benchmark and integration-test strategy

**Decision**: Generate deterministic synthetic markdown corpora from seeded templates inside pytest fixtures, run real indexing and query flows in integration tests, and record elapsed times as artifacts under the repository-level `benchmarks/` directory without using strict timing assertions.

**Rationale**: This satisfies the requirement to benchmark both small and large corpora while avoiding flaky tests. Deterministic generation keeps the repo small and makes the corpora reproducible across machines and CI.

**Alternatives considered**:
- Commit static large fixtures: makes the repository heavy and harder to evolve.
- Assert hard timing thresholds in tests: likely to cause flaky failures across machines and CI environments.