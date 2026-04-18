---
name: _local-edr-001-semfs-index-storage-and-query-contract
description: Defines how semfs stores local indexes, interprets index modes, and shapes public query results. Use when implementing or reviewing semfs indexing and search behavior.
applied-to: semfs library and CLI
---

# _local-edr-001: Semfs index storage and query contract

## Context and Problem Statement

Semfs needs repository-specific decisions for local index files, refresh modes, and returned search shapes that are not covered by shared Python or CLI standards.

Question: How should semfs store indexes and apply query modes?

## Decision Outcome

**Local `.semfs` artifacts with mode-driven reuse and chunk-oriented query results**

Semfs stores persistent indexes under the searched directory, keeps ephemeral modes non-persistent, and returns merged chunk findings as file-plus-line-range objects.

### Implementation Details

- Persistent index artifacts must live under `[dir]/.semfs/`.
- The metadata file must be `[dir]/.semfs/[name].json`.
- The search database must be `[dir]/.semfs/[name].db`.
- Metadata must store the normalized config used to build the index, a file-manifest fingerprint, and summary counts needed to decide whether reuse is valid.
- `refresh` mode must always rebuild the index and overwrite persistent artifacts.
- `auto` mode must reuse the persistent index only when the stored file-manifest fingerprint matches the current input set; otherwise it must rebuild.
- `stale` mode must reuse an existing persistent index even if source files changed. If no index exists, it must build one.
- `inmemory` mode must build an index without writing `.semfs` artifacts.
- `transient` mode must behave as an ephemeral one-shot build. It may use temporary storage internally but must leave no persistent `.semfs` artifacts after completion.
- The library config must keep `model` as a string field. The first implementation may support only `tfidf`, but additional backends must fit the same config shape.
- Chunk search results must use the public object shape `{ "from": int, "to": int, "file": str, "contents": str | null }`.
- `semfs.files(...)` must deduplicate file hits from chunk search and keep only the best-scoring match per file.
- `semfs.chunks(...)` must merge contiguous or overlapping chunk hits from the same file before returning results.
- The CLI may discover `.semfsrc` by default, but the library must operate only on provided config values and must not require config-file discovery.

## References

- [agentme-edr-014](../../../agentme/edrs/application/014-python-project-tooling.md) - Python project structure and build contract
- [agentme-edr-015](../../../agentme/edrs/application/015-cli-tool-standards.md) - CLI separation and config discovery contract
- [agentme-edr-009](../../../agentme/edrs/principles/009-error-handling.md) - Exit signaling and boundary error handling
