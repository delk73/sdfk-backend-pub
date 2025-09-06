#!/usr/bin/env python3
"""
Examples QC CLI for synesthetic-schemas

Phases:
- S1: Spec discovery
- S2: Draft spec emission (only if absent)
- S3: Validation sweep (tolerate only top-level $schemaRef)
- S4: Blessing & duplicate detection
- S5: Reports (JSON, Markdown, field matrix)
- S6: CLI & CI gate behavior

Deterministic, KISS, minimal deps. Python 3.11. Uses jsonschema 2020-12.

By default writes to meta/output and prints nothing. Exit code conveys status.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict
from dataclasses import dataclass
from glob import glob
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

import jsonschema
# --- NEW IMPORTS START ---
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012
# --- NEW IMPORTS END ---


# --- Constants / Config ---

EXAMPLES_GLOB = "examples/**/SynestheticAsset_Example*.json"
CANONICAL_CANDIDATES = [
    "schemas/synesthetic-asset.json",
    "schemas/synesthetic-asset.schema.json",
    "schemas/canonical/synesthetic-asset.json",
]

# Repo-local fallback used by this repo layout
FALLBACK_CANONICAL = "jsonschema/synesthetic-asset.schema.json"

ALLOW_METADATA_KEYS = {"$schemaRef"}
FORBID_ENVELOPE_KEYS = {"id", "schemaVersion"}

REPORT_JSON = Path("meta/output/SCHEMAS_EXAMPLES_QA.json")
REPORT_MD = Path("meta/output/SCHEMAS_EXAMPLES_QA.md")
BLESSED_INDEX = Path("meta/output/BLESSED_EXAMPLES.json")
FIELD_MATRIX = Path("meta/output/EXAMPLE_FIELD_MATRIX.json")

DRAFT_SCHEMA_PATH = Path("schemas/_draft/synesthetic-asset.generated.json")
DRAFT_SPEC_MD = Path("docs/specs/SynestheticAsset_SPEC.md")
DRAFT_SCHEMA_ID = "https://synesthetic.dev/schemas/_draft/synesthetic-asset.generated.json"

SCHEMA_META_202012 = "https://json-schema.org/draft/2020-12/schema"


# --- Types ---


@dataclass(frozen=True)
class FileError:
    file: str
    pointer: str
    message: str


# --- Utilities ---


def _read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # Deterministic formatting
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        f.write(text)


def _sorted_glob(pattern: str) -> List[str]:
    return sorted(glob(pattern, recursive=True))


def _json_pointer(parts: Iterable[Any]) -> str:
    # Convert an iterable of path components to a JSON Pointer
    encoded = []
    for p in parts:
        s = str(p)
        s = s.replace("~", "~0").replace("/", "~1")
        encoded.append(s)
    return "/" + "/".join(encoded) if encoded else ""


def _collect_field_matrix(instances: List[Tuple[str, Any]]) -> Dict[str, Any]:
    # Traverse JSON values to gather occurrence count and type sets per JSON Pointer
    counts: Dict[str, int] = defaultdict(int)
    types: Dict[str, set[str]] = defaultdict(set)

    def visit(value: Any, path_parts: List[Any]):
        ptr = _json_pointer(path_parts)
        counts[ptr] += 1
        t = (
            "null"
            if value is None
            else "boolean"
            if isinstance(value, bool)
            else "number"
            if isinstance(value, (int, float)) and not isinstance(value, bool)
            else "string"
            if isinstance(value, str)
            else "array"
            if isinstance(value, list)
            else "object"
        )
        types[ptr].add(t)
        if isinstance(value, dict):
            for k in sorted(value.keys()):
                visit(value[k], path_parts + [k])
        elif isinstance(value, list):
            for i, item in enumerate(value):
                visit(item, path_parts + [i])

    for _, obj in instances:
        visit(obj, [])

    total = len(instances)
    # Build deterministic structure
    out: Dict[str, Any] = {}
    for ptr in sorted(counts.keys()):
        out[ptr] = {
            "occurrences": counts[ptr],
            "presence_pct": round((counts[ptr] / total) * 100, 2) if total else 0.0,
            "types": sorted(types[ptr]),
        }
    return out


# --- MODIFIED FUNCTION START ---
def _load_schema(canonical_path: Path) -> Tuple[Dict[str, Any], Registry]:
    # Load schema and provide a registry that maps https://schemas.synesthetic.dev/... to local files
    schema = _read_json(canonical_path)

    # The new library uses a "retriever" function for custom URI handling.
    def retrieve_from_filesystem(uri: str) -> Resource:
        # Maps URIs like https://schemas.synesthetic.dev/0.7.3/tone.schema.json
        # to a local file at jsonschema/tone.schema.json
        if uri.startswith("https://schemas.synesthetic.dev/"):
            name = uri.split("/")[-1]
            local_path = Path("jsonschema") / name
            if not local_path.is_file():
                raise FileNotFoundError(f"Missing local schema for {uri} -> {local_path}")
            contents = _read_json(local_path)
            return Resource.from_contents(contents, default_specification=DRAFT202012)
        # This is an important fallback for any other URIs.
        # It lets the library handle standard metaschemas (like draft2020-12) correctly.
        from referencing.retrieval import to_cached_resource
        return to_cached_resource()(uri)

    registry = Registry(retrieve=retrieve_from_filesystem)
    return schema, registry
# --- MODIFIED FUNCTION END ---


# --- MODIFIED FUNCTION START ---
def _validate_instance(
    instance: Dict[str, Any], schema: Dict[str, Any], registry: Registry
) -> List[FileError]:
    # Validate instance after dropping ONLY top-level $schemaRef
    if isinstance(instance, dict) and "$schemaRef" in instance:
        inst = {k: v for k, v in instance.items() if k != "$schemaRef"}
    else:
        inst = instance

    # The modern validator takes a registry instead of a resolver.
    validator = jsonschema.Draft202012Validator(schema, registry=registry)
    errors: List[FileError] = []
    for err in sorted(validator.iter_errors(inst), key=lambda e: (list(e.absolute_path), e.message)):
        pointer = _json_pointer(err.absolute_path)
        errors.append(FileError(file="", pointer=pointer, message=err.message))
    return errors
# --- MODIFIED FUNCTION END ---


def _detect_duplicates(blessed: List[Tuple[str, Dict[str, Any]]]) -> Dict[str, List[str]]:
    names: Dict[str, List[str]] = defaultdict(list)
    for path, obj in blessed:
        name = obj.get("name")
        if isinstance(name, str) and name.strip():
            names[name].append(path)
    return {k: sorted(v) for k, v in names.items() if len(v) > 1}


def _check_envelope_keys(obj: Dict[str, Any]) -> List[Tuple[str, str]]:
    issues: List[Tuple[str, str]] = []
    for key in sorted(obj.keys()):
        if key in FORBID_ENVELOPE_KEYS:
            issues.append(("/" + key, f"Forbidden top-level key: {key}"))
        elif key.startswith("$") and key not in ALLOW_METADATA_KEYS:
            issues.append(("/" + key, f"Unknown top-level metadata key: {key}"))
    return issues


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(description="QC Synesthetic examples against schema")
    parser.add_argument("--print", action="store_true", dest="do_print", help="Print summary")
    parser.add_argument("--fail-fast", action="store_true", help="Stop on first failure")
    parser.add_argument("--ci", action="store_true", help="CI mode: exit 2 on any issues")
    args = parser.parse_args(argv)

    try:
        example_paths = _sorted_glob(EXAMPLES_GLOB)

        # S1: Spec discovery
        canonical_path: Path | None = None
        for c in CANONICAL_CANDIDATES:
            p = Path(c)
            if p.exists():
                canonical_path = p
                break
        if canonical_path is None and Path(FALLBACK_CANONICAL).exists():
            canonical_path = Path(FALLBACK_CANONICAL)

        spec_status = "PRESENT" if canonical_path else "ABSENT"

        draft_emitted = False
        draft_schema_used = False

        if canonical_path is None:
            # S2: Draft emission
            # Build a minimal draft schema from examples field presence
            primary_instances: List[Tuple[str, Any]] = []
            for p in example_paths:
                try:
                    primary_instances.append((p, _read_json(Path(p))))
                except Exception:
                    # Corrupt JSON still should be captured later during validation attempt
                    pass

            field_matrix = _collect_field_matrix(primary_instances)

            draft_schema = {
                "$schema": SCHEMA_META_202012,
                "$id": DRAFT_SCHEMA_ID,
                "title": "synesthetic-asset (DRAFT)",
                "type": "object",
                "additionalProperties": True,
                # Minimal: require 'name' if it appears in all examples
                "required": ["name"]
                if all(isinstance(obj.get("name"), str) and obj.get("name").strip() for _, obj in primary_instances)
                else [],
                "properties": {
                    "name": {"type": "string", "minLength": 1}
                },
                "x-generated-from": "examples",
            }

            _write_json(DRAFT_SCHEMA_PATH, draft_schema)
            draft_emitted = True

            spec_note = (
                "# SynestheticAsset Spec (DRAFT)\n\n"
                "This draft is generated deterministically from examples.\n\n"
                f"- $schema: {SCHEMA_META_202012}\n"
                f"- $id: {DRAFT_SCHEMA_ID}\n\n"
                "Required fields (heuristic):\n\n"
            )
            if "" in field_matrix:
                # Root presence is 100% by definition
                pass
            if any(k == "/name" for k in field_matrix.keys()):
                spec_note += "- name: string (required if present in all examples)\n"

            _write_text(DRAFT_SPEC_MD, spec_note)

            # Validate against draft schema
            canonical_path = DRAFT_SCHEMA_PATH
            draft_schema_used = True

        assert canonical_path is not None

        # Prepare validator
        schema, registry = _load_schema(canonical_path) # Changed from resolver to registry

        # S3/S4: Validate + Bless
        per_file_errors: Dict[str, List[FileError]] = {}
        blessed: List[Tuple[str, Dict[str, Any]]] = []

        # Preload all examples deterministically
        loaded: List[Tuple[str, Any]] = []
        load_errors: Dict[str, str] = {}
        for path in example_paths:
            p = Path(path)
            try:
                obj = _read_json(p)
                loaded.append((path, obj))
            except Exception as e:  # JSON parse error
                load_errors[path] = f"Invalid JSON: {e}"
        # Validation
        for path, obj in loaded:
            file_errors: List[FileError] = []

            # Envelope key checks (top-level only)
            if isinstance(obj, dict):
                for ptr, msg in _check_envelope_keys(obj):
                    file_errors.append(FileError(file=path, pointer=ptr, message=msg))
            else:
                file_errors.append(FileError(file=path, pointer="", message="Top-level is not an object"))

            # Schema validation
            try:
                v_errors = _validate_instance(obj if isinstance(obj, dict) else obj, schema, registry) # Changed from resolver to registry
                for e in v_errors:
                    file_errors.append(FileError(file=path, pointer=e.pointer, message=e.message))
            except Exception as e:
                file_errors.append(FileError(file=path, pointer="", message=f"Validation error: {e}"))

            # Aggregate
            if file_errors:
                # Stable ordering by pointer then message
                per_file_errors[path] = sorted(
                    file_errors, key=lambda fe: (fe.pointer, fe.message)
                )
                if args.fail_fast:
                    break
            else:
                blessed.append((path, obj))

        # Include parse errors as per-file errors with empty pointer
        for path, msg in load_errors.items():
            per_file_errors[path] = [FileError(file=path, pointer="", message=msg)]

        # Blessed index and duplicates
        duplicates = _detect_duplicates(blessed)

        blessed_index = [
            {"file": p, "name": obj.get("name")}
            for p, obj in sorted(blessed, key=lambda t: t[0])
            if isinstance(obj.get("name"), str) and obj.get("name").strip()
        ]

        # Field matrix from loaded items only (deterministic)
        field_matrix = _collect_field_matrix([(p, o) for p, o in loaded if isinstance(o, (dict, list))])

        # S5: Reports
        qa = {
            "spec_status": spec_status if not draft_emitted else "DRAFT",
            "schema_path": str(canonical_path),
            "draft_emitted": draft_emitted,
            "totals": {
                "files_total": len(example_paths),
                "valid": len(blessed_index),
                "invalid": len(per_file_errors),
                "duplicates": sum(len(v) for v in duplicates.values()),
            },
            "blessed_index_path": str(BLESSED_INDEX),
            "duplicates": duplicates,
            "files": {
                # For each file with errors, list error pointers and messages
                k: [
                    {"pointer": e.pointer, "message": e.message}
                    for e in per_file_errors[k]
                ]
                for k in sorted(per_file_errors.keys())
            },
        }

        _write_json(REPORT_JSON, qa)
        _write_json(BLESSED_INDEX, blessed_index)
        _write_json(FIELD_MATRIX, field_matrix)

        # Markdown summary
        lines: List[str] = []
        lines.append("# Schemas & Examples QA")
        lines.append("")
        lines.append("## Overview")
        lines.append("Deterministic QA for Synesthetic examples.")
        lines.append("")
        lines.append("## Spec Status")
        lines.append(("PRESENT" if spec_status == "PRESENT" and not draft_emitted else "DRAFT"))
        lines.append("")
        lines.append("## Totals")
        lines.append(f"- Files: {len(example_paths)}")
        lines.append(f"- Valid: {len(blessed_index)}")
        lines.append(f"- Invalid: {len(per_file_errors)}")
        lines.append(f"- Duplicate names: {len(duplicates)}")
        lines.append("")
        lines.append("## Blessed")
        for item in blessed_index:
            lines.append(f"- {item['name']} :: {item['file']}")
        if not blessed_index:
            lines.append("- (none)")
        lines.append("")
        lines.append("## Duplicates")
        if duplicates:
            for name in sorted(duplicates.keys()):
                files = ", ".join(duplicates[name])
                lines.append(f"- {name}: {files}")
        else:
            lines.append("- (none)")
        lines.append("")
        lines.append("## Failures")
        if qa["files"]:
            for fpath in qa["files"].keys():
                lines.append(f"- {fpath}")
                for err in qa["files"][fpath]:
                    pointer = err["pointer"] or "/"
                    lines.append(f"  - {pointer}: {err['message']}")
        else:
            lines.append("- (none)")
        lines.append("")
        lines.append("## Next Actions")
        if draft_emitted:
            lines.append("- Harden draft schema and promote to canonical.")
        else:
            lines.append("- Fix examples to conform; remove duplicates.")

        _write_text(REPORT_MD, "\n".join(lines) + "\n")

        # S6: Exit codes
        has_failures = bool(per_file_errors) or bool(duplicates)
        exit_code = 2 if has_failures else 0

        if args.do_print:
            # Concise summary only when requested
            print(json.dumps({
                "spec": qa["spec_status"],
                "valid": len(blessed_index),
                "invalid": len(per_file_errors),
                "duplicates": len(duplicates),
                "report": str(REPORT_JSON),
            }, indent=2, sort_keys=True))

        return exit_code

    except SystemExit:
        raise
    except Exception as e:
        # Script/setup error
        if getattr(args, "do_print", False):
            print(f"ERROR: {e}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))