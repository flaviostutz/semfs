# Feature Specification: Semantic File Query Library and CLI

**Feature Branch**: `[001-semantic-file-query]`  
**Created**: 2026-04-18  
**Status**: Draft  
**Input**: User description: "Semantic file search utility for the semfs Python library and CLI, including indexing, chunk and file queries, named index configuration, and benchmarkable example datasets."

## Clarifications

### Session 2026-04-18

- Q: How should query-time index modes behave when the index is missing or stale? → A: `refresh` always rebuilds before use; `auto` rebuilds when files changed or the index is missing; `stale` reuses an existing index even if outdated and only builds when no index exists.
- Q: What should passage queries return by default? → A: Passage queries return file path and line range by default; excerpt contents are included only when explicitly requested.
- Q: How should deduplicated file query results be ordered? → A: File query results are ordered by best matching semantic relevance, highest first.
- Q: What should happen when `max_distance` is omitted? → A: If `max_distance` is omitted, the system applies no distance threshold and relies only on ranking plus result limit.
- Q: How should the CLI discover its configuration file? → A: CLI looks for `.semfsrc` in the current working directory by default, and `--config` overrides it.
- Q: What format must `.semfsrc` use? → A: `.semfsrc` is a UTF-8 JSON object whose fields match the Index Configuration schema.
- Q: Which files are supported for indexing? → A: Only UTF-8-readable text files selected by the configured filter are in scope; binary files, unreadable files, and other non-text inputs are skipped.
- Q: What should happen when contents are requested but a selected file no longer matches the indexed snapshot? → A: Fail the whole query with an actionable error.
- Q: What should happen when the configured embedding model is unavailable locally? → A: Any indexing or query action that requires that model, including use of a reusable index whose stored model is not available locally, fails with an actionable error.
- Q: What happens if matched files produce zero chunks? → A: Index creation still succeeds, records zero emitted chunks for those files, and later queries return an empty result set until matching chunkable content exists.
- Q: How should returned file paths be represented? → A: Always return paths relative to the indexed directory.
- Q: What does `chunking.edges` mean? → A: `auto` uses markdown-aware chunking for markdown files and fixed chunking for all other files; `fixed` always uses fixed chunking.
- Q: What happens when markdown-aware chunking finds no useful structure? → A: It falls back to the configured fixed chunking behavior for that file.
- Q: What are the public fields of a chunk finding? → A: Chunk findings expose `file`, `from`, `to`, `score`, and optional `contents`; `from` and `to` are inclusive merged line numbers.
- Q: How are file-query ties resolved? → A: When files have the same best semantic relevance, order them by relative path ascending.
- Q: Where are benchmark timing artifacts stored? → A: Persist them under a single repository-level `benchmarks/` directory.
- Q: How are benchmark artifacts recorded? → A: Each planned benchmark run writes a JSON artifact that records dataset identity, corpus shape, index and query elapsed seconds, and the run timestamp; previous benchmark artifacts are preserved unless the caller explicitly removes them.
- Q: Should the collapsed `chunk_index` schema keep `chunk_mode` and `ordinal`? → A: No. Keep only the chunk result fields required for retrieval.
- Q: Is the single-table `chunk_index` design a required MVP storage contract? → A: Yes. For the MVP, reusable indexes keep chunk embeddings and retrieval fields in one persisted `chunk_index` structure rather than depending on a second persisted join table.
- Q: Is `candidate_k = max(max_results * 5, 25)` part of the public contract? → A: No. It is the default internal retrieval heuristic for the MVP and may change if benchmark evidence justifies a different default.
- Q: How is digest compatibility defined? → A: Snapshot verification uses SHA-256 over the UTF-8 text contents that were indexed, and changing that compatibility rule requires a schema-version change.
- Q: How is index-size acceptability judged? → A: No fixed maximum database size is part of MVP acceptance; acceptable growth means reusable indexes do not persist raw file contents, benchmark artifacts remain small JSON metadata records, and the planned benchmark corpora complete on a single local machine.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Find relevant passages in a directory (Priority: P1)

A developer indexes a directory and asks a natural-language question to retrieve the most relevant file passages, including file path and line range, so they can quickly inspect the source material without manually opening every file.

**Why this priority**: Returning relevant passages is the core user value of the product. Without this capability, the utility does not solve the primary search problem.

**Independent Test**: Can be fully tested by indexing a sample directory, running a passage query with a natural-language question, and confirming that the returned results include ranked file ranges by default and excerpt text only when explicitly requested.

**Acceptance Scenarios**:

1. **Given** a directory that has been indexed, **When** the user submits a natural-language query for passage results, **Then** the system returns up to the requested number of relevant findings with relative file paths and line range information.
2. **Given** multiple adjacent relevant passages from the same file, **When** passage results are returned, **Then** contiguous line ranges are merged into a single finding rather than shown as separate duplicates.
3. **Given** the user requests passage contents, **When** results are returned, **Then** each finding includes the excerpt text for the returned line range.

---

### User Story 2 - Identify the most relevant files (Priority: P2)

A developer asks a natural-language question and receives a deduplicated list of matching files so they can decide which files to inspect first.

**Why this priority**: File-level results are a simpler navigation aid built on the same semantic search value, but they are secondary to detailed passage retrieval.

**Independent Test**: Can be fully tested by running a file query against a directory with several matching passages in the same file and verifying that each file appears only once and that results are ordered by strongest semantic match first.

**Acceptance Scenarios**:

1. **Given** a query whose best matches come from multiple passages in the same file, **When** the user requests file results, **Then** the matching file is listed only once.
2. **Given** a query with an explicit result limit or distance threshold, **When** file results are returned, **Then** the result set respects those query constraints.
3. **Given** multiple matching files with different semantic relevance scores, **When** file results are returned, **Then** the files are ordered from strongest match to weakest match after deduplication.
4. **Given** multiple matching files with the same best semantic relevance score, **When** file results are returned, **Then** the files are ordered by relative path in ascending order.

---

### User Story 3 - Prepare indexes and benchmark realistic datasets (Priority: P3)

A maintainer creates or refreshes indexes for named configurations and runs example scenarios on small and large synthetic corpora so the project can demonstrate expected behavior and record benchmark timings for indexing and querying.

**Why this priority**: The product needs a repeatable way to prepare indexes and validate expected behavior at realistic sizes, but this supports the core feature rather than defining it.

**Independent Test**: Can be fully tested by creating named indexes for the example datasets, running both query modes, and recording indexing and query times for each dataset size.

**Acceptance Scenarios**:

1. **Given** a directory and a named index configuration, **When** the user creates or refreshes the index, **Then** the system stores and reuses that index under the requested name for subsequent queries.
2. **Given** the provided small and large synthetic datasets, **When** the example scenarios are executed, **Then** the project records index and query timings for each dataset under the repository-level `benchmarks/` directory and preserves those results for later documentation updates.

### Edge Cases

- A usable index is one whose required on-disk metadata and storage structures are present and readable, whose schema version matches the implementation, and whose stored model and chunking fingerprint still match the requested configuration.
- When a query is run against a directory with no usable index, `refresh`, `auto`, and `stale` modes must create or refresh index state according to their defined behavior rather than silently returning empty results.
- When no results satisfy the query constraints, the system must return an empty result set without duplicate placeholders or partial malformed findings.
- When the configured filter matches files but none of those files yield chunks, indexing must still complete successfully and subsequent queries must return an empty result set.
- When `max_distance` is omitted, queries must still execute and rely on ranking plus result count rather than applying an implicit distance cutoff.
- When files change after an index is created, `auto` mode must refresh before querying while `stale` mode must continue using the existing index until the caller explicitly rebuilds it.
- When indexing or querying requires an embedding model that is not available locally, including when a reusable index references that model, the operation must fail with an actionable error rather than silently downgrading behavior.
- When passage contents are requested and any selected file no longer matches the indexed snapshot or cannot be read, the whole query must fail with an actionable error instead of returning partial contents.
- When the filter excludes some files, when a matched file is binary or unreadable, or when a file type is otherwise unsupported for chunking, those files must be skipped without corrupting the rest of the index.
- When markdown-aware chunking cannot detect useful structure in a markdown file, the system must fall back to the configured fixed chunking behavior for that file.
- When relevant passages in the same file are separated by a gap, they must remain separate findings instead of being merged incorrectly.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The library MUST provide an indexing operation that prepares a searchable semantic index for a target directory using a caller-supplied configuration.
- **FR-002**: The indexing operation MUST support named indexes so multiple index definitions can coexist for the same directory without overwriting each other unintentionally.
- **FR-003**: The system MUST persist index metadata within the indexed directory for reusable modes and MUST keep transient or in-memory modes isolated from persisted index state.
- **FR-004**: The indexing configuration MUST allow callers to scope which files are considered during indexing through a filter pattern. Supported indexed inputs are UTF-8-readable text files selected by that filter; binary files, unreadable files, and other non-text inputs are skipped rather than indexed.
- **FR-005**: The indexing configuration MUST allow callers to define chunk size, chunk overlap, and `chunking.edges`, where `auto` uses markdown-aware chunking for markdown files and fixed chunking otherwise, and `fixed` always uses fixed chunking.
- **FR-005a**: When `chunking.edges="auto"` is selected for a markdown file and no useful markdown structure can be detected, the system MUST fall back to the configured fixed chunking behavior for that file.
- **FR-006**: The system MUST support the index modes `refresh`, `auto`, `stale`, `inmemory`, and `transient`, each with distinct behavior for rebuilding, reusing, or discarding index state.
- **FR-007**: In `refresh` mode, the system MUST rebuild the index before use for each indexing or query operation.
- **FR-008**: In `auto` mode, the system MUST rebuild the index when no usable index exists or when indexed files have changed since the last usable index state.
- **FR-009**: In `stale` mode, the system MUST reuse an existing index even if source files have changed and MUST only build a new index when none exists yet.
- **FR-010**: In `inmemory` and `transient` modes, the system MUST avoid persisting reusable on-disk index state after the operation completes.
- **FR-011**: The library MUST provide a passage query operation that accepts a query object containing required text, an optional maximum result count, and an optional distance threshold.
- **FR-012**: When a query omits `max_distance`, the system MUST apply no distance-based filtering and rely on semantic ranking plus result count.
- **FR-013**: When a passage query is executed without an explicit result limit, the system MUST default to returning no more than 10 findings.
- **FR-014**: Passage query results MUST expose the public fields `file`, `from`, `to`, and `score`, where `file` is the source path relative to the indexed directory and `from` and `to` are the inclusive merged line numbers for that finding.
- **FR-015**: Passage query results MUST merge contiguous relevant chunks from the same file into a single finding.
- **FR-016**: Passage query results MUST return only the relative file path and inclusive line range by default.
- **FR-017**: Passage query results MUST include the text contents for each returned line range only when the caller explicitly requests contents, and MUST fail the whole query with an actionable error if any selected file no longer matches the indexed snapshot or cannot be read.
- **FR-018**: The library MUST provide a file query operation that returns a deduplicated list of file paths relative to the indexed directory derived from semantic search results for the same query model.
- **FR-019**: File query results MUST be ordered by highest semantic relevance after deduplication, with ties broken by relative path ascending.
- **FR-020**: The command-line interface MUST expose commands for index creation or refresh, passage queries, and file queries using the same underlying behaviors as the library.
- **FR-021**: The command-line interface MUST look for a UTF-8 JSON `.semfsrc` configuration file in the current working directory by default.
- **FR-022**: The command-line interface MUST accept `--config` to override default configuration-file discovery.
- **FR-023**: Successful command-line runs MUST report when indexing starts and completes, and query commands MUST print concise human-readable results for either passage findings or file paths.
- **FR-024**: Failed indexing or query operations MUST return actionable errors when required query text, configuration, local model availability, or index state is invalid for the requested action, including when a reusable index references a model that is not available locally. At minimum, an actionable error MUST identify the failed action, the relevant path, index, or file when known, and the next corrective step the caller can take.
- **FR-025**: The project MUST include example scenarios with integration tests for a small synthetic markdown corpus of 5 folders and 30 files and a large synthetic markdown corpus of 300 folders and 5000 files with maximum depth 7.
- **FR-026**: The example scenarios MUST measure and record elapsed time for indexing and querying on both synthetic datasets, and MUST persist one JSON benchmark artifact per planned run under a single repository-level `benchmarks/` directory. Each artifact MUST record dataset name, folder count, file count, maximum depth, index seconds, query seconds, and recording timestamp, and MUST preserve prior benchmark artifacts unless the caller explicitly removes them.
- **FR-027**: Once the configured embedding model is available locally, indexing, querying, and benchmark runs MUST execute fully on one local machine without requiring external services or network access.
- **FR-028**: Indexing and benchmark flows MUST process files incrementally and MUST not require the entire source corpus to be loaded into memory at once.
- **FR-029**: Reusable persisted index state MUST not store raw file contents and MUST persist only the metadata, digest, embeddings, and retrieval fields needed for querying and excerpt verification.
- **FR-030**: The small and large benchmark corpora MUST be generated deterministically from documented generation rules so repeated runs with the same generator inputs produce the same folder counts, file counts, and maximum depth.
- **FR-031**: User-facing documentation in the README or quickstart MUST describe the `.semfsrc` format, the requirement that the configured model be available locally before offline runs, the benchmark command flow, and the benchmark artifact location.
- **FR-032**: For the MVP, reusable indexes MUST persist chunk embeddings together with the retrieval fields required for query results in a single `chunk_index` storage structure rather than relying on a second persisted chunk-metadata join table.

### Key Entities *(include if feature involves data)*

- **Index Configuration**: User-supplied settings that define index name, file filter, lifecycle mode, chunking behavior, and semantic model selection for a directory.
- **Query Request**: A semantic search request containing the user’s text question plus optional result-count and distance constraints.
- **Chunk Finding**: A passage-level result containing the public fields `file`, `from`, `to`, `score`, and optional `contents`, where `from` and `to` are inclusive merged line numbers for a contiguous relevant range.
- **File Result**: A deduplicated file-level search result representing one file path relative to the indexed directory judged relevant to the query.
- **Benchmark Dataset**: A synthetic directory tree used to validate indexing and querying behavior and measure elapsed times under defined scale conditions.

## Assumptions

- The utility is intended for text-centric files selected by the configured filter, including markdown-aware chunking where that strategy is requested.
- The utility skips binary, unreadable, and other unsupported non-text files instead of attempting to coerce them into the index.
- The command-line interface uses `.semfsrc` as the canonical default configuration filename for all supported commands.
- A schema mismatch, unreadable index metadata, missing required tables, or a model or chunking fingerprint mismatch makes an existing persisted index unusable.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A new user can index a sample directory and retrieve relevant passage results through either the library or the CLI within 5 minutes by following the project’s Getting Started guidance.
- **SC-002**: In validation scenarios where several top passage matches come from the same file, 100% of file-query results list each matching file at most once.
- **SC-003**: In validation scenarios with multiple matching files, 100% of file-query results are ordered by strongest semantic match first after deduplication, with ties resolved by relative path ascending.
- **SC-004**: In validation scenarios with adjacent relevant passages from the same file, 100% of returned passage findings merge contiguous line ranges into a single result.
- **SC-005**: Queries without `max_distance` execute successfully and rely on ranking plus result limit rather than an implicit distance cutoff.
- **SC-006**: Query executions never return more than the requested result limit and default to no more than 10 results when no limit is supplied.
- **SC-007**: The example benchmark suite records indexing time and query time for both the small and large synthetic datasets on every planned benchmark run, writes one JSON artifact per run under the repository-level `benchmarks/` directory, and preserves prior benchmark artifacts unless they are explicitly removed. Release readiness for this criterion depends on successful artifact creation and completeness, not on meeting any fixed time threshold.
- **SC-008**: Validation of the small and large benchmark corpora completes on one local machine without network access once the configured model is available locally, and those runs do not require the entire corpus to be loaded into memory at once.
- **SC-009**: Validation of reusable indexes confirms that raw file contents are never persisted in index storage and that the MVP uses one persisted `chunk_index` structure for embeddings plus retrieval fields.
