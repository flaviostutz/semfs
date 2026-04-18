from __future__ import annotations

import argparse
import json
import sys
import traceback
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

from . import api


def run(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "command") or args.command is None:
        parser.print_help()
        return 0

    try:
        config = _load_config(args)
        if args.command == "index":
            print(f"Starting to create {config.get('name', 'index0')}...")
            metadata = api.index(args.directory, config)
            print(
                "Index created successfully: "
                f"{metadata['chunk_count']} chunks across {metadata['file_count']} files"
            )
            return 0
        if args.command == "files":
            print("Searching files...")
            file_results = api.files(_query_dict(args), args.directory, config)
            for file_name in file_results:
                print(Path(file_name).as_posix())
            print(f"Found {len(file_results)} files")
            return 0
        if args.command == "chunks":
            print("Searching chunks...")
            chunk_results = api.chunks(_query_dict(args), args.directory, True, config)
            for finding in chunk_results:
                print(f"{Path(str(finding['file'])).as_posix()}[{finding['from']}:{finding['to']}]")
            print(f"Found {len(chunk_results)} chunk ranges")
            return 0
        parser.print_help()
        return 1
    except Exception as error:  # noqa: BLE001
        print(f"Error: {error}", file=sys.stderr)
        if getattr(args, "verbose", False):
            traceback.print_exc()
        return 1


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="semfs",
        description="Build and query local semantic file indexes.",
        epilog=(
            "Examples:\n"
            "  semfs index docs/\n"
            "  semfs files docs/ 'index refresh'\n"
            "  semfs chunks docs/ 'chunk overlap' --top 5 --distance 0.7"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", action="version", version=_package_version())
    parser.add_argument("--verbose", action="store_true", help="Show detailed failures")
    subparsers = parser.add_subparsers(dest="command")

    index_parser = subparsers.add_parser("index", help="Create or refresh an index")
    _add_config_flags(index_parser)
    _add_index_flags(index_parser)
    index_parser.add_argument("directory", help="Directory to index")

    files_parser = subparsers.add_parser("files", help="Search matching files")
    _add_config_flags(files_parser)
    _add_index_flags(files_parser)
    _add_query_flags(files_parser)
    files_parser.add_argument("directory", help="Directory to search")
    files_parser.add_argument("query", help="Search text")

    chunks_parser = subparsers.add_parser("chunks", help="Search matching chunk ranges")
    _add_config_flags(chunks_parser)
    _add_index_flags(chunks_parser)
    _add_query_flags(chunks_parser)
    chunks_parser.add_argument("directory", help="Directory to search")
    chunks_parser.add_argument("query", help="Search text")

    return parser


def _add_config_flags(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--config", help="Explicit config file path")


def _add_index_flags(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--name", help="Index name")
    parser.add_argument("--mode", choices=["refresh", "auto", "stale", "inmemory", "transient"])
    parser.add_argument("--filter", dest="filter_pattern", help="Glob used when indexing")
    parser.add_argument("--model", help="Search model name")
    parser.add_argument("--chunk-size", type=int, help="Chunk size in approximate characters")
    parser.add_argument("--chunk-overlap", type=int, help="Chunk overlap in approximate characters")
    parser.add_argument("--chunk-mode", choices=["auto", "fixed"], help="Chunking mode")


def _add_query_flags(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--top", type=int, default=10, help="Maximum number of results")
    parser.add_argument("--distance", type=float, help="Maximum cosine distance")


def _load_config(args: argparse.Namespace) -> dict[str, Any]:
    config_path = Path(args.config) if args.config else Path.cwd() / ".semfsrc"
    config: dict[str, Any] = {}
    if config_path.exists():
        config = json.loads(config_path.read_text(encoding="utf-8"))
    if args.name:
        config["name"] = args.name
    if args.mode:
        config["mode"] = args.mode
    if args.filter_pattern:
        config["filter"] = args.filter_pattern
    if args.model:
        config["model"] = args.model

    chunking = dict(config.get("chunking", {}))
    if args.chunk_size is not None:
        chunking["size"] = args.chunk_size
    if args.chunk_overlap is not None:
        chunking["overlap"] = args.chunk_overlap
    if args.chunk_mode is not None:
        chunking["mode"] = args.chunk_mode
    if chunking:
        config["chunking"] = chunking
    return config


def _query_dict(args: argparse.Namespace) -> dict[str, Any]:
    payload: dict[str, Any] = {"text": args.query, "max_results": args.top}
    if args.distance is not None:
        payload["max_distance"] = args.distance
    return payload


def _package_version() -> str:
    try:
        return version("semfs")
    except PackageNotFoundError:
        return "0.0.1"
