# CLI Contract

## Command Surface

The CLI exposes a root command named `semfs` with subcommands:

- `semfs index DIR`
- `semfs chunks DIR QUERY`
- `semfs files DIR QUERY`

The root command must also expose:

- `--help`
- `--version`
- `--verbose`

## Configuration Rules

- By default, the CLI loads `.semfsrc` from the current working directory.
- `--config PATH` overrides default discovery for all commands.
- Config-file parsing belongs to the CLI layer; library calls receive validated configuration objects.

## Command Contracts

### `semfs index DIR`

- **Required arguments**: `DIR`
- **Options**: `--config PATH`, `--verbose`
- **Success output**:
  - Start message indicating which named index is being built
  - Completion message with indexed file and chunk counts
- **Failure output**: actionable error on stderr; exit code `1`. The error must identify the failed command, the relevant directory or index when known, the reason for failure, and the next corrective step.

### `semfs chunks DIR QUERY`

- **Required arguments**: `DIR`, `QUERY`
- **Options**: `--config PATH`, `--top N`, `--distance FLOAT`, `--contents`, `--verbose`
- **Success output**:
  - One result header per line in the form `path[start:end]`, where `path` is relative to the indexed directory
  - When `--contents` is set, the header is followed by the merged excerpt body
- **Failure output**: actionable error on stderr; exit code `1`, including when `--contents` is set and any selected file no longer matches the indexed snapshot or cannot be read. The error must identify the failed command, the relevant directory, index, or file when known, the reason for failure, and the next corrective step.

### `semfs files DIR QUERY`

- **Required arguments**: `DIR`, `QUERY`
- **Options**: `--config PATH`, `--top N`, `--distance FLOAT`, `--verbose`
- **Success output**:
  - One relative file path per line in descending semantic relevance order, with ties broken by path ascending
- **Failure output**: actionable error on stderr; exit code `1`. The error must identify the failed command, the relevant directory or index when known, the reason for failure, and the next corrective step.

## Exit Codes

- `0`: requested action completed successfully
- `1`: requested action failed or input/config/index state was invalid