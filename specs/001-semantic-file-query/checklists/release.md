# Release Gate Checklist: Semantic File Query Library and CLI

**Purpose**: Validate that the feature requirements are complete, measurable, and unambiguous enough for release-gate review across spec, plan, contracts, data model, and quickstart.
**Created**: 2026-04-18
**Feature**: [spec.md](../spec.md)

**Note**: This checklist reviews the quality of the written requirements, not whether an implementation already works.

## Requirement Completeness

- [x] CHK001 Are all index lifecycle behaviors defined for every mode, including how `inmemory` and `transient` differ from reusable modes? [Completeness, Spec §FR-006, Spec §FR-010]
- [x] CHK002 Are named-index persistence requirements complete enough to determine where metadata, database state, and coexistence boundaries must live? [Completeness, Spec §FR-002, Spec §FR-003, Data Model §IndexState]
- [x] CHK003 Are chunking configuration requirements complete, including what `chunking.edges` means and how its allowed values affect chunk construction? [Completeness, Spec §FR-005, Data Model §IndexConfig]
- [x] CHK004 Are supported file classes explicitly defined, or are binary files, unreadable files, and non-text files intentionally excluded? [Gap, Spec §FR-004, Spec §Edge Cases]
- [x] CHK005 Are benchmark recording requirements complete enough to determine what must be captured beyond elapsed time, such as output format, storage location, and retention expectations? [Gap, Spec §FR-026, Spec §SC-007]

## Requirement Clarity

- [x] CHK006 Is the term "usable index" defined objectively enough to distinguish missing, stale, invalid, and schema-incompatible index states? [Ambiguity, Spec §Edge Cases, Spec §FR-008, Spec §FR-009]
- [x] CHK007 Is the requirement for "concise human-readable results" specific enough to judge acceptable CLI output without relying on implementation preference? [Clarity, Spec §FR-023, Contract §Command Contracts]
- [x] CHK008 Is the config-file format explicitly stated and consistent across the spec and supporting artifacts, rather than inferred from examples? [Clarity, Spec §FR-021, Spec §FR-022, Quickstart §2, Research §3]
- [x] CHK009 Are file path expectations for returned results clear enough to determine whether outputs must be relative, absolute, or caller-selectable? [Ambiguity, Data Model §ChunkFinding, Data Model §FileFinding]
- [x] CHK010 Is the benchmark-performance goal clear enough to distinguish mandatory acceptance criteria from advisory planning guidance? [Ambiguity, Plan §Technical Context, Spec §SC-007]

## Requirement Consistency

- [x] CHK011 Do configuration field names align across the spec, data model, quickstart, and contracts, especially the distinction between top-level `mode` and `chunking.edges`? [Consistency, Spec §FR-005, Data Model §IndexConfig, Quickstart §2]
- [x] CHK012 Do chunk result field names and range semantics align between the feature spec, data model, and library contract? [Consistency, Spec §Key Entities, Data Model §ChunkFinding, Contract §Function Contracts]
- [x] CHK013 Are chunk-merging requirements consistent between the spec, the library contract, and the data model's line-range representation? [Consistency, Spec §FR-015, Contract §semfs.chunks(query, dir, fetch_contents, config), Data Model §ChunkFinding]
- [x] CHK014 Are CLI configuration-discovery rules consistent between the clarifications, functional requirements, contract, and quickstart examples? [Consistency, Spec §Clarifications, Spec §FR-021, Spec §FR-022, Contract §Configuration Rules, Quickstart §2]
- [x] CHK015 Are benchmark expectations consistent between the specification's "record timings" language and the plan/research language about stored artifacts? [Consistency, Spec §FR-026, Research §6, Plan §Summary]

## Acceptance Criteria Quality

- [x] CHK016 Can file-ordering requirements be objectively evaluated without a defined tie-break rule for equal semantic relevance scores? [Measurability, Spec §FR-019, Spec §SC-003]
- [x] CHK017 Can the "up to requested number of results" rule be objectively verified for both filtered and unfiltered queries, including omitted `max_distance`? [Acceptance Criteria, Spec §FR-012, Spec §FR-013, Spec §SC-005, Spec §SC-006]
- [x] CHK018 Can "named indexes can coexist without overwriting each other unintentionally" be objectively evaluated without a more explicit storage-layout or collision rule? [Measurability, Spec §FR-002]
- [x] CHK019 Are benchmark success criteria measurable enough to distinguish mandatory release readiness from informational performance logging? [Measurability, Spec §SC-007, Plan §Technical Context]

## Scenario Coverage

- [x] CHK020 Are requirements defined for directories that match the filter but produce zero chunks, or is that scenario intentionally excluded? [Coverage, Gap, Spec §FR-004, Spec §Edge Cases]
- [x] CHK021 Are requirements defined for ranking ties, near-ties, or identical best scores across multiple files? [Coverage, Gap, Spec §FR-019, Spec §SC-003]
- [x] CHK022 Are requirements defined for unavailable models both before index creation and when an existing index references a missing model? [Coverage, Spec §FR-024, Data Model §IndexState]
- [x] CHK023 Are requirements defined for interrupted rebuilds or partial index-write failures, including what state should remain on disk afterward? [Coverage, Exception Flow, Gap, Spec §FR-003, Spec §FR-024]

## Edge Case Coverage

- [x] CHK024 Is fallback behavior defined when markdown-aware chunking cannot detect useful structure inside a markdown file? [Edge Case, Gap, Spec §Assumptions, Research §5]
- [x] CHK025 Are edge-case expectations defined for invalid `chunking.edges`, overlap equal to size, or negative query parameters beyond the generic invalid-input error requirement? [Edge Case, Ambiguity, Data Model §IndexConfig, Data Model §QueryRequest, Spec §FR-024]
- [x] CHK026 Are edge-case expectations defined for stale indexes when files are deleted, renamed, or moved rather than merely modified? [Edge Case, Spec §FR-008, Spec §FR-009, Data Model §FileSnapshot]

## Non-Functional Requirements

- [x] CHK027 Are offline and local-execution expectations explicitly specified in the feature requirements, rather than only implied in planning artifacts? [Gap, Plan §Technical Context, Research §1]
- [x] CHK028 Are memory, disk-growth, and corpus-size expectations specified well enough for the large benchmark dataset to be judged acceptable? [Gap, Spec §FR-025, Plan §Technical Context]
- [x] CHK029 Are error-message quality requirements specific enough to define what makes an error "actionable" for CLI and library consumers? [Clarity, Spec §FR-024, Contract §Error Contract, Contract §Exit Codes]

## Dependencies & Assumptions

- [x] CHK030 Are model-installation and local-availability assumptions documented as requirements where users can discover them before indexing? [Assumption, Data Model §IndexConfig, Spec §FR-024, Quickstart §2]
- [x] CHK031 Are deterministic synthetic-corpus generation rules treated as requirements where reproducibility matters, rather than only as a planning choice? [Dependency, Gap, Spec §FR-025, Research §6]
- [x] CHK032 Are README or end-user documentation expectations for benchmarks and config usage explicitly required, or only implied by quickstart examples and CLI standards? [Gap, Quickstart §2, Quickstart §7, Contract §Configuration Rules]

## Ambiguities & Conflicts

- [x] CHK033 Does the spec clearly distinguish index lifecycle `mode` from chunking `edges`, or could readers still confuse the two configuration concepts? [Ambiguity, Spec §FR-005, Spec §FR-006, Data Model §IndexConfig]
- [x] CHK034 Are the public contracts consistent about whether query functions require a prebuilt index versus allowing query-time rebuilds under `refresh`, `auto`, and `stale`? [Conflict, Spec §Clarifications, Contract §semfs.index(dir, config), Contract §semfs.chunks(query, dir, fetch_contents, config)]
- [x] CHK035 Are success criteria and release-gate expectations aligned, or do they leave room for a release that records benchmarks without defining what constitutes acceptable benchmark quality? [Ambiguity, Spec §SC-007, Plan §Technical Context]

## Notes

- Focus areas selected: full feature scope, release-gate rigor, mandatory non-functional benchmark coverage.
- Intended actor/timing: reviewer during release or pre-release PR review.
- Existing checklist content in [requirements.md](requirements.md) was preserved; this file is a separate release-gate checklist.

## Storage Design Update

- [x] CHK036 Are requirements complete enough to justify collapsing chunk metadata and embeddings into one `chunk_index` table, or should the single-table design remain an implementation choice rather than a required storage contract? [Completeness, Plan §Storage And Query Design, Research §1]
- [x] CHK037 Are the allowed and disallowed uses of `chunk_index` auxiliary columns explicitly documented, including which fields are guaranteed retrievable versus never filterable in KNN queries? [Clarity, Plan §Storage And Query Design, Data Model §ChunkRecord]
- [x] CHK038 Is the minimal `chunk_index` retrieval schema explicit enough to show that only `file_path`, `start_line`, and `end_line` are required alongside embeddings for MVP queries? [Clarity, Data Model §ChunkRecord, Plan §Storage And Query Design]
- [x] CHK039 Are chunk identity and stability requirements defined well enough to determine whether `chunk_id` must survive rebuilds, config changes, or only remain unique within one materialized index? [Gap, Data Model §ChunkRecord, Data Model §IndexState]

## Contents Consistency Update

- [x] CHK040 Are the requirements explicit that `contents` may be returned only when the live file matches the indexed snapshot digest, rather than implied only by the plan? [Gap, Spec §FR-017, Plan §Storage And Query Design, Data Model §FileSnapshot]
- [x] CHK041 Is the failure behavior specified when `fetch_contents=True` but the file digest mismatches, the file is unreadable, or the file was removed after indexing? [Coverage, Exception Flow, Spec §FR-017, Spec §FR-024, Plan §Storage And Query Design]
- [x] CHK042 Is the digest algorithm or compatibility requirement defined tightly enough to ensure consistent snapshot verification across platforms and future versions? [Clarity, Data Model §FileSnapshot, Plan §Storage And Query Design, Plan §index_meta]
- [x] CHK043 Are `stale`-mode requirements consistent with digest-gated contents retrieval, or do the current requirements leave ambiguity about whether stale rankings with failed contents retrieval are acceptable? [Consistency, Spec §FR-009, Spec §FR-017, Plan §Storage And Query Design]

## Search Behavior Update

- [x] CHK044 Is the `candidate_k = max(max_results * 5, 25)` rule intended as a hard requirement, a default heuristic, or merely planning guidance? [Ambiguity, Plan §Storage And Query Design, Spec §FR-013, Spec §FR-019]
- [x] CHK045 Are the ordering rules complete enough to determine which sort key wins when semantic distance, file path, and line range disagree or tie? [Completeness, Spec §FR-014, Spec §FR-019, Plan §Storage And Query Design]
- [x] CHK046 Are merge requirements specific enough to determine whether chunks that are directly contiguous in line numbers from the same file always merge, regardless of how chunk construction originally grouped the file? [Clarity, Spec §FR-015, Data Model §ChunkRecord, Plan §Storage And Query Design]
- [x] CHK047 Are the non-functional requirements explicit about index-size expectations after the single-table sqlite-vec design, or is “small index” still only a planning preference rather than a measurable requirement? [Gap, Plan §Storage And Query Design, Spec §FR-003, Spec §FR-025]