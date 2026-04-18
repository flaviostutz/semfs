---
name: _local-bdr-001-semantic-file-query-capability
description: Defines the first public semfs capability for local semantic indexing and querying. Use when planning or implementing the semfs product surface.
applied-to: semfs library and CLI
---

# _local-bdr-001: Semantic File Query Capability

## Context and Problem Statement

The repository currently has no durable product contract beyond a minimal README. What public capability should the first semfs release provide?

## Decision Outcome

**Provide local semantic indexing plus chunk and file query workflows**

The first semfs release must let users create named local indexes for directories, query chunk-level and file-level semantic results through both the library and CLI, and benchmark the behavior on deterministic markdown corpora.

### Implementation Details

- The library contract centers on `semfs.index`, `semfs.chunks`, and `semfs.files`.
- The CLI must provide `index`, `chunks`, and `files` commands with parity to the library behaviors.
- Chunk results must default to file path plus line range, and include contents only when explicitly requested.
- File results must be deduplicated and ordered by strongest semantic match first.
- The feature must include repeatable benchmark scenarios for the required small and large corpora.

## References

- [Feature spec](../../../../specs/001-semantic-file-query/spec.md) - Source product requirements for this capability
- [Implementation plan](../../../../specs/001-semantic-file-query/plan.md) - Execution plan for delivering this capability