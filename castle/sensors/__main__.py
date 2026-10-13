"""Command-line entry point for the Castle sensor trio."""

from __future__ import annotations

import argparse
import json
import sys

from .registry import SensorError, TEMPLATES, execute_sensor, public_catalog


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m castle.sensors",
        description="Run bounded local text sensors. Sensors estimate; gates decide.",
    )
    parser.add_argument(
        "--allow-download", action="store_true",
        help="allow fetching the catalog-pinned checkpoint; default is cache-only/offline",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("list", help="print the fixed sensor catalog")

    fill = commands.add_parser("fill-mask", help="rank replacements for one [MASK]")
    fill.add_argument("--text", required=True)
    fill.add_argument("--top-k", type=int, default=5)

    compare = commands.add_parser("compare", help="estimate semantic similarity")
    compare.add_argument("--left", required=True)
    compare.add_argument("--right", required=True)

    classify = commands.add_parser("classify", help="rank candidate labels with NLI")
    classify.add_argument("--text", required=True)
    classify.add_argument("--label", action="append", dest="labels", required=True)
    classify.add_argument("--template", choices=tuple(TEMPLATES), default="topic")
    return parser


def main(argv=None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "list":
        print(json.dumps(public_catalog(), indent=2, sort_keys=True))
        return 0
    if args.command == "fill-mask":
        call = {"sensor": "bert_fill_mask", "arguments": {
            "text": args.text, "top_k": args.top_k,
        }}
    elif args.command == "compare":
        call = {"sensor": "minilm_similarity", "arguments": {
            "left": args.left, "right": args.right,
        }}
    else:
        call = {"sensor": "deberta_nli", "arguments": {
            "text": args.text, "labels": args.labels, "template": args.template,
        }}
    try:
        result = execute_sensor(call, allow_download=args.allow_download)
    except SensorError as exc:
        print(json.dumps({"status": "error", "error": str(exc)}), file=sys.stderr)
        return 2
    print(json.dumps({"status": "ok", **result}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
