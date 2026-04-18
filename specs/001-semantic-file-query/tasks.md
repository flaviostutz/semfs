# Tasks: Semantic File Query Library and CLI

**Input**: Design documents from `/specs/001-semantic-file-query/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Include unit, integration, and contract-oriented verification because the specification requires mandatory validation scenarios and benchmark coverage.

**Organization**: Tasks are grouped by user story so each story can be implemented and validated independently once the shared foundation is complete.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Scaffold the Python package, tooling, and development workflow required by the plan.

- [x] T001 Create `pyproject.toml` with uv-managed package metadata, CLI entry point, and dependencies including `sentence-transformers`, `typer`, `pydantic`, `numpy`, and `sqlite-vec`
- [x] T002 Create or update root `Makefile` with `install`, `build`, `lint-fix`, and `test` targets aligned with the planned workflow
- [x] T003 [P] Create package skeleton in `src/semfs/__init__.py`, `src/semfs/__main__.py`, and placeholder modules from the plan structure
- [x] T004 [P] Create shared test scaffolding in `tests/conftest.py` and `tests_integration/__init__.py`
- [x] T005 [P] Create example scaffolding in `examples/Makefile`, `examples/basic-usage/main.py`, and `examples/benchmark-corpora/run.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Build the common configuration, storage, chunking, and error-handling layers that all user stories depend on.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [x] T006 Implement config and query models in `src/semfs/models.py` and `src/semfs/config.py` for `IndexConfig`, `QueryRequest`, `ChunkFinding`, `FileFinding`, and `IndexState`
- [x] T007 [P] Implement typed domain exceptions in `src/semfs/errors.py` for config, index-state, model, and file-processing failures
- [x] T008 [P] Implement chunking primitives in `src/semfs/chunking.py` so `chunking.edges="auto"` uses markdown-aware chunking for markdown files and fixed overlapping windows otherwise, while `chunking.edges="fixed"` always uses fixed windows, with line-range tracking and contiguous-merge helpers
- [x] T009 Implement SQLite connection management and sqlite-vec extension loading in `src/semfs/storage.py`
- [x] T010 Implement schema creation in `src/semfs/storage.py` for `index_meta`, `file_snapshots` with `content_digest`, and a single `chunk_index USING vec0(...)` table that stores embeddings plus chunk result fields without storing file contents in the index
- [x] T011 Implement index metadata and freshness helpers in `src/semfs/storage.py` for schema versioning, chunking fingerprinting, `auto` drift detection, and per-file content digest persistence
- [x] T012 Implement embedding-model loading utilities in `src/semfs/indexer.py` or `src/semfs/search.py` with one shared sentence-transformers loader per configured model

**Checkpoint**: The project can validate configuration, open SQLite databases with sqlite-vec enabled, and create empty index schemas.

---

## Phase 3: User Story 1 - Find relevant passages in a directory (Priority: P1) 🎯 MVP

**Goal**: Index a directory and return ranked passage findings with path and line ranges, optionally including merged contents.

**Independent Test**: Index a sample markdown directory and confirm `semfs.chunks()` plus `semfs chunks` return ranked merged passage results, defaulting to path plus range and only including contents when requested.

### Tests for User Story 1

- [ ] T013 [P] [US1] Add chunking and merge unit tests in `tests/test_chunking.py`
- [ ] T014 [P] [US1] Add single-table sqlite-vec schema, digest verification, live-file excerpt reconstruction, and KNN tests in `tests/test_search.py`, including whole-query failure when requested contents cannot be verified
- [ ] T015 [P] [US1] Add passage-query CLI tests in `tests/test_cli.py`

### Implementation for User Story 1

- [ ] T016 [US1] Implement directory scanning, file reads, and chunk production with stable line ranges in `src/semfs/indexer.py`
- [ ] T017 [US1] Implement rebuild flows in `src/semfs/indexer.py` and `src/semfs/storage.py` that write `file_snapshots` metadata rows with `content_digest` and `chunk_index` rows in one transaction
- [ ] T018 [US1] Implement query embedding and sqlite-vec candidate retrieval in `src/semfs/search.py` using `SELECT chunk_id, file_path, start_line, end_line, distance FROM chunk_index WHERE embedding MATCH :query_embedding AND k = :candidate_k ORDER BY distance, file_path, start_line`
- [ ] T019 [US1] Implement passage result join, optional `max_distance` filtering, contiguous merge, live-file digest verification, live-file excerpt reconstruction on demand, and final trimming in `src/semfs/search.py`
- [ ] T020 [US1] Expose `semfs.index()` and `semfs.chunks()` in `src/semfs/__init__.py`
- [ ] T021 [US1] Implement `semfs chunks DIR QUERY` in `src/semfs/cli.py` with `--top`, `--distance`, `--contents`, and actionable failure output

**Checkpoint**: Passage indexing and chunk search work end-to-end through both the library and CLI.

---

## Phase 4: User Story 2 - Identify the most relevant files (Priority: P2)

**Goal**: Return deduplicated file-level results ordered by best semantic match.

**Independent Test**: Run file search against a corpus with multiple matching passages per file and confirm each file appears once, ranked by best match.

### Tests for User Story 2

- [ ] T022 [P] [US2] Add file-ranking, tie-break, and dedup unit tests in `tests/test_search.py`
- [ ] T023 [P] [US2] Add file-query CLI tests in `tests/test_cli.py`

### Implementation for User Story 2

- [ ] T024 [US2] Implement file-level aggregation in `src/semfs/search.py` by grouping `chunk_index` matches on `file_path`, using `MIN(distance)` as `best_score`, and breaking ties by relative path ascending
- [ ] T025 [US2] Expose `semfs.files()` in `src/semfs/__init__.py`
- [ ] T026 [US2] Implement `semfs files DIR QUERY` in `src/semfs/cli.py` with deduplicated descending relevance output based on the best file match

**Checkpoint**: File search works independently on top of the same index and query pipeline.

---

## Phase 5: User Story 3 - Prepare indexes and benchmark realistic datasets (Priority: P3)

**Goal**: Support named reusable indexes, lifecycle modes, and deterministic benchmark datasets for small and large corpora.

**Independent Test**: Create named indexes in each required mode, run the small and large corpus scenarios, and record index plus query timings.

### Tests for User Story 3

- [ ] T027 [P] [US3] Add index-mode and config-validation tests in `tests/test_config.py` and `tests/test_indexer.py`
- [ ] T028 [P] [US3] Add small corpus integration coverage in `tests_integration/test_small_corpus.py`
- [ ] T029 [P] [US3] Add large corpus integration and benchmark coverage in `tests_integration/test_large_corpus.py`, including verification that benchmark artifacts are persisted under `benchmarks/`

### Implementation for User Story 3

- [ ] T030 [US3] Implement named-index path resolution and mode handling in `src/semfs/indexer.py` for `refresh`, `auto`, `stale`, `inmemory`, and `transient`
- [ ] T031 [US3] Implement deterministic corpus generation in `src/semfs/synthetic_data.py`
- [ ] T032 [US3] Implement benchmark execution and timing capture in `src/semfs/benchmark.py`, persisting artifacts under the repository-level `benchmarks/` directory
- [ ] T033 [US3] Implement `semfs index DIR` in `src/semfs/cli.py` with start/completion messaging and config discovery via `.semfsrc` and `--config`
- [ ] T034 [US3] Add runnable example flows in `examples/basic-usage/main.py` and `examples/benchmark-corpora/run.py`

**Checkpoint**: Named index lifecycle behavior and deterministic benchmark scenarios are fully covered.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Align docs, developer workflow, and verification with the delivered feature.

- [ ] T035 [P] Update public usage documentation in `README.md` and `specs/001-semantic-file-query/quickstart.md`
- [ ] T036 Verify `.github/agents/copilot-instructions.md` remains consistent with the implemented stack after code scaffolding lands
- [ ] T037 Run `make build`, `make lint-fix`, and `make test` and resolve any implementation regressions

---

## Dependencies & Execution Order

### Phase Dependencies

- Setup tasks T001-T005 must complete first.
- Foundational tasks T006-T012 block all user stories.
- User Story 1 depends on the foundational phase and delivers the MVP.
- User Story 2 depends on the shared query pipeline from User Story 1.
- User Story 3 depends on foundational storage/config pieces and completes index-mode plus benchmark behavior.
- Polish tasks run after the desired stories are complete.

### User Story Dependencies

- US1 can start once T006-T012 are complete.
- US2 depends on the KNN candidate retrieval from T018 and can follow once US1 search plumbing exists.
- US3 depends on storage/config primitives from Phase 2 and may proceed in parallel with late US1 or US2 work once those prerequisites are stable.

### Parallel Opportunities

- T003-T005 can run in parallel.
- T007-T008 and T012 can run in parallel after T006 starts.
- US1 tests T013-T015 can run in parallel.
- US2 tests T022-T023 can run in parallel.
- US3 tests T027-T029 can run in parallel.

## Implementation Strategy

### MVP First

1. Complete Setup and Foundational phases.
2. Deliver US1 through T021.
3. Validate passage indexing and search independently.

### Incremental Delivery

1. Add US2 file ranking on top of the shared sqlite-vec search pipeline.
2. Add US3 named-index lifecycle and benchmark workflows.
3. Finish with documentation and full build/lint/test verification.

## Notes

- `storage.py` is the single owner of sqlite-vec extension loading and schema creation.
- `search.py` is the single owner of direct `chunk_index` KNN query execution, candidate over-fetch, and post-query merge or dedup behavior.
- Use `candidate_k = max(max_results * 5, 25)` for both query modes unless benchmark evidence forces an update.