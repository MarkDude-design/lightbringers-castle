#!/usr/bin/env python3
"""Check an exact-byte work-order digest before a worker reads the packet.

This verifies integrity and JSON syntax, not truth, authorization, or build success.
No third-party packages. The trusted expected digest must come through the handoff.
"""
import argparse
import hashlib
import hmac
import json
from pathlib import Path
import re
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("packet", type=Path)
    parser.add_argument("expected_sha256")
    args = parser.parse_args()
    if not re.fullmatch(r"[0-9a-f]{64}", args.expected_sha256):
        parser.error("expected_sha256 must be 64 lowercase hex characters")
    try:
        payload = args.packet.read_bytes()
        actual = hashlib.sha256(payload).hexdigest()
        if not hmac.compare_digest(actual, args.expected_sha256):
            raise ValueError("packet SHA-256 mismatch; stop dispatch")
        value = json.loads(payload.decode("utf-8"))
        if not isinstance(value, dict) or not isinstance(value.get("task_id"), str) or not value["task_id"]:
            raise ValueError("packet must be an object with a nonempty task_id")
    except (OSError, UnicodeError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps({"task_id": value["task_id"], "sha256": actual, "bytes": len(payload), "integrity": "PASS"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
