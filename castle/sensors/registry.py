"""Validation and provenance envelope for the local sensor trio.

This module has no ML dependency. Heavy imports happen only after a call has
passed the fixed registry and argument checks below.
"""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import time


CATALOG_PATH = Path(__file__).with_name("catalog.json")
MAX_TEXT_CHARS = 4_000
MAX_LABEL_CHARS = 80
MAX_LABELS = 8
TEMPLATES = {
    "topic": "This text is about {}.",
    "register": "This text is written in {}.",
    "status": "The status described by this text is {}.",
}


class SensorError(ValueError):
    """A rejected sensor request or unavailable local runtime."""


def _catalog() -> dict:
    with CATALOG_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


def public_catalog() -> dict:
    """Return catalog metadata without exposing mutable internal state."""
    return deepcopy(_catalog())


def _object(value, name: str) -> dict:
    if not isinstance(value, dict):
        raise SensorError(f"{name} must be an object")
    return value


def _exact_keys(value: dict, allowed: set[str]) -> None:
    unknown = sorted(set(value) - allowed)
    if unknown:
        raise SensorError("unknown arguments: " + ", ".join(unknown))


def _text(value, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SensorError(f"{name} must be a non-empty string")
    if len(value) > MAX_TEXT_CHARS:
        raise SensorError(f"{name} exceeds {MAX_TEXT_CHARS} characters")
    return value


def _validate(sensor: str, arguments: dict, spec: dict) -> dict:
    operation = spec["operation"]
    args = _object(arguments, "arguments")

    if operation == "fill_mask":
        _exact_keys(args, {"text", "top_k"})
        text = _text(args.get("text"), "text")
        if text.count("[MASK]") != 1:
            raise SensorError("text must contain exactly one literal [MASK]")
        top_k = args.get("top_k", 5)
        if isinstance(top_k, bool) or not isinstance(top_k, int) or not 1 <= top_k <= 10:
            raise SensorError("top_k must be an integer from 1 through 10")
        return {"text": text, "top_k": top_k}

    if operation == "compare_text":
        _exact_keys(args, {"left", "right"})
        return {
            "left": _text(args.get("left"), "left"),
            "right": _text(args.get("right"), "right"),
        }

    if operation == "classify_labels":
        _exact_keys(args, {"text", "labels", "template"})
        text = _text(args.get("text"), "text")
        labels = args.get("labels")
        if not isinstance(labels, list) or isinstance(labels, (str, bytes)):
            raise SensorError("labels must be a list")
        if not 2 <= len(labels) <= MAX_LABELS:
            raise SensorError(f"labels must contain 2 through {MAX_LABELS} entries")
        clean_labels = []
        for index, label in enumerate(labels):
            if not isinstance(label, str) or not label.strip():
                raise SensorError(f"labels[{index}] must be a non-empty string")
            label = label.strip()
            if len(label) > MAX_LABEL_CHARS:
                raise SensorError(f"labels[{index}] exceeds {MAX_LABEL_CHARS} characters")
            clean_labels.append(label)
        if len({label.casefold() for label in clean_labels}) != len(clean_labels):
            raise SensorError("labels must be distinct ignoring case")
        template = args.get("template", "topic")
        if template not in TEMPLATES:
            raise SensorError("template must be one of: " + ", ".join(TEMPLATES))
        return {"text": text, "labels": clean_labels, "template": template}

    raise SensorError(f"catalog operation is not implemented: {operation}")


def execute_sensor(call: dict, *, backend=None, allow_download: bool = False) -> dict:
    """Execute one allowlisted sensor call and wrap it in provenance metadata.

    ``backend`` is injectable for offline fixture tests. The production backend
    is loaded only after validation, and defaults to cached checkpoint files.
    """
    call = _object(call, "call")
    _exact_keys(call, {"sensor", "arguments"})
    sensor = call.get("sensor")
    if not isinstance(sensor, str):
        raise SensorError("sensor must be a string")
    catalog = _catalog()
    try:
        spec = catalog["sensors"][sensor]
    except KeyError as exc:
        raise SensorError(f"unknown sensor: {sensor}") from exc
    arguments = _validate(sensor, call.get("arguments"), spec)

    if backend is None:
        try:
            from .transformers_backend import TransformersBackend
        except (ImportError, ModuleNotFoundError) as exc:
            raise SensorError(
                "local sensor dependencies are unavailable; install requirements-sensors.txt"
            ) from exc
        backend = TransformersBackend(allow_download=allow_download)

    started = time.monotonic()
    try:
        result = backend.run(sensor, spec, arguments)
    except SensorError:
        raise
    except (ImportError, ModuleNotFoundError) as exc:
        raise SensorError(
            "local sensor dependencies are unavailable; install requirements-sensors.txt"
        ) from exc
    except Exception as exc:
        raise SensorError(f"{sensor} execution failed: {type(exc).__name__}: {exc}") from exc
    elapsed = round(time.monotonic() - started, 6)

    runtime = None
    if hasattr(backend, "runtime_metadata"):
        runtime = backend.runtime_metadata()

    envelope = {
        "catalog_version": catalog["catalog_version"],
        "sensor": sensor,
        "operation": spec["operation"],
        "source_kind": "local_checkpoint",
        "historical_model": False,
        "model": {
            "id": spec["model_id"],
            "revision": spec["revision"],
            "license": spec["license"],
        },
        "limits": {
            "max_text_chars": MAX_TEXT_CHARS,
            "max_tokens": spec["max_tokens"],
            "download_allowed": bool(allow_download),
        },
        "claim_ceiling": spec["claim_ceiling"],
        "elapsed_seconds": elapsed,
        "result": result,
    }
    if runtime is not None:
        envelope["runtime"] = runtime
    return envelope
