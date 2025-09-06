# pyright: reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownArgumentType=false, reportUnknownParameterType=false
# ruff: noqa

"""
Normalize JSON Schemas in jsonschema/:

- set $schema / $id / x-schema-version
- default additionalProperties: false (with per-file allowlist)
- strip root 'description'
- strip enum defaults for optional fields (inline and via $ref)
- optional --check mode: fail if any optional-enum defaults remain

Idempotent: safe to run repeatedly.
"""



from __future__ import annotations

import argparse
import copy
import json
import pathlib
import sys
from dataclasses import dataclass
from typing import Any

# Support version.json single source
try:
    # ensure repo root on sys.path so we can import scripts.lib.version
    ROOT = pathlib.Path(__file__).resolve().parents[1]
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from scripts.lib.version import schema_version  # type: ignore
except Exception:
    schema_version = None  # type: ignore

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "jsonschema"
BASE_URL = "https://schemas.synesthetic.dev"
VERSION = schema_version() if callable(schema_version) else "0.1.0"

# Files that may keep additionalProperties=true at root
ALLOW_ADDITIONAL_PROPS = {"tone.schema.json", "haptic.schema.json"}


# ---------------------------- helpers ----------------------------

def kebab(name: str) -> str:
    return name.lower().replace(" ", "-")


def load_json(p: pathlib.Path) -> dict[str, Any]:
    return json.loads(p.read_text())


def save_json(p: pathlib.Path, data: dict[str, Any]) -> None:
    p.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def _ref_target(root: dict[str, Any], ref: str) -> tuple[str | None, dict[str, Any] | None]:
    """Return (container_key, target_schema) for an internal $ref like '#/$defs/Name'."""
    if not ref.startswith("#/"):
        return None, None
    path = ref[2:].split("/")
    cur: Any = root
    for seg in path:
        if not isinstance(cur, dict) or seg not in cur:
            return None, None
        cur = cur[seg]
    return (path[0] if path else None), cur if isinstance(cur, dict) else None


def _strip_enum_default_in_place(schema: dict[str, Any]) -> bool:
    """
    If schema has enum+default with default ∈ enum, remove it.
    Returns True if changed.
    """
    if "enum" in schema and "default" in schema:
        try:
            if schema["default"] in schema.get("enum", []):
                schema.pop("default", None)
                return True
        except Exception:
            pass
    return False


def _recurse_strip(root: dict[str, Any], node: Any) -> None:
    """
    Walk schema tree; for optional properties remove enum defaults
    (inline or via $ref). Does not mutate shared $defs unless inlined.
    """
    if not isinstance(node, dict):
        return

    local_required = set(node.get("required", []))

    # properties
    props = node.get("properties")
    if isinstance(props, dict):
        for prop_name, prop_schema in list(props.items()):
            is_optional = prop_name not in local_required
            if not isinstance(prop_schema, dict):
                continue

            if is_optional:
                # Inline case
                _strip_enum_default_in_place(prop_schema)

                # $ref case → inline a copy WITHOUT default for THIS property
                ref = prop_schema.get("$ref")
                if isinstance(ref, str):
                    _, target = _ref_target(root, ref)
                    if isinstance(target, dict):
                        tmp = copy.deepcopy(target)
                        if _strip_enum_default_in_place(tmp):
                            props[prop_name] = tmp
                            prop_schema = tmp  # continue recursion into inlined copy

            _recurse_strip(root, prop_schema)

    # common containers
    for key in ("$defs", "definitions"):
        d = node.get(key)
        if isinstance(d, dict):
            for v in d.values():
                _recurse_strip(root, v)

    items = node.get("items")
    if isinstance(items, dict):
        _recurse_strip(root, items)
    elif isinstance(items, list):
        for it in items:
            _recurse_strip(root, it)

    addl = node.get("additionalProperties")
    if isinstance(addl, dict):
        _recurse_strip(root, addl)

    for key in ("allOf", "anyOf", "oneOf", "not", "if", "then", "else"):
        v = node.get(key)
        if isinstance(v, dict):
            _recurse_strip(root, v)
        elif isinstance(v, list):
            for it in v:
                _recurse_strip(root, it)


def _rewrite_abs_refs_to_version(node: Any, base_url: str, version: str) -> None:
    """
    Rewrite absolute $ref values pointing to any schemas.synesthetic.dev/<ver>/X.schema.json
    so that <ver> is replaced with the current VERSION.
    """
    if isinstance(node, dict):
        ref = node.get("$ref")
        if isinstance(ref, str) and ref.startswith(base_url + "/") and ref.endswith(".schema.json"):
            # normalize to current version regardless of prior version present
            name = ref.rsplit("/", 1)[-1]
            node["$ref"] = f"{base_url}/{version}/{name}"
        for v in node.values():
            _rewrite_abs_refs_to_version(v, base_url, version)
    elif isinstance(node, list):
        for v in node:
            _rewrite_abs_refs_to_version(v, base_url, version)


@dataclass
class Offense:
    file: str
    path: str
    default: Any
    enum: list[Any]


def _find_optional_enum_defaults(root: dict[str, Any], node: Any, path: list[str], out: list[Offense]) -> None:
    """Detect optional enum+default (inline and via $ref)."""
    if not isinstance(node, dict):
        return

    local_required = set(node.get("required", []))

    props = node.get("properties")
    if isinstance(props, dict):
        for prop_name, prop_schema in list(props.items()):
            is_optional = prop_name not in local_required
            if not isinstance(prop_schema, dict):
                continue

            # Inline case
            if (
                is_optional
                and "enum" in prop_schema
                and "default" in prop_schema
                and prop_schema["default"] in prop_schema["enum"]
            ):
                out.append(
                    Offense(
                        file="",
                        path="/".join(path + ["properties", prop_name]),
                        default=prop_schema["default"],
                        enum=list(prop_schema["enum"]),
                    )
                )

            # $ref case
            ref = prop_schema.get("$ref")
            if is_optional and isinstance(ref, str):
                _, target = _ref_target(root, ref)
                if (
                    isinstance(target, dict)
                    and "enum" in target
                    and "default" in target
                    and target["default"] in target["enum"]
                ):
                    out.append(
                        Offense(
                            file="",
                            path="/".join(path + ["properties", prop_name, f"$ref->{ref}"]),
                            default=target["default"],
                            enum=list(target["enum"]),
                        )
                    )

            _find_optional_enum_defaults(root, prop_schema, path + ["properties", prop_name], out)

    # descend
    for key in ("$defs", "definitions"):
        d = node.get(key)
        if isinstance(d, dict):
            for k, v in d.items():
                _find_optional_enum_defaults(root, v, path + [key, k], out)

    items = node.get("items")
    if isinstance(items, dict):
        _find_optional_enum_defaults(root, items, path + ["items"], out)
    elif isinstance(items, list):
        for i, it in enumerate(items):
            _find_optional_enum_defaults(root, it, path + ["items", str(i)], out)

    addl = node.get("additionalProperties")
    if isinstance(addl, dict):
        _find_optional_enum_defaults(root, addl, path + ["additionalProperties"], out)

    for key in ("allOf", "anyOf", "oneOf", "not", "if", "then", "else"):
        v = node.get(key)
        if isinstance(v, dict):
            _find_optional_enum_defaults(root, v, path + [key], out)
        elif isinstance(v, list):
            for i, it in enumerate(v):
                _find_optional_enum_defaults(root, it, path + [key, str(i)], out)


# ---------------------------- normalize ----------------------------

def normalize_file(fp: pathlib.Path, check_only: bool) -> tuple[dict[str, Any], list[Offense]]:
    data = load_json(fp)

    # headers
    data["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    data["$id"] = f"{BASE_URL}/{VERSION}/{fp.name}"
    data["x-schema-version"] = VERSION

    # root cosmetics/strictness
    data.pop("description", None)
    # Normalize title deterministically to kebab-case of the base name without the ".schema" suffix.
    # e.g., synesthetic-asset.schema.json -> "synesthetic-asset"
    base = fp.stem  # e.g., "synesthetic-asset.schema"
    if base.endswith(".schema"):
        base = base[: -len(".schema")]
    data["title"] = kebab(base)
    if fp.name not in ALLOW_ADDITIONAL_PROPS:
        data["additionalProperties"] = data.get("additionalProperties", False)

    # strip rule
    _recurse_strip(data, data)

    # rewrite absolute $ref URLs to current VERSION for stability
    _rewrite_abs_refs_to_version(data, BASE_URL, VERSION)

    offenses: list[Offense] = []
    if check_only:
        _find_optional_enum_defaults(data, data, [], offenses)
        for o in offenses:
            o.file = fp.name

    return data, offenses


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="Fail if optional enum defaults remain")
    args = ap.parse_args()

    total = 0
    all_offenses: list[Offense] = []

    for fp in sorted(SCHEMA_DIR.glob("*.schema.json")):
        original = load_json(fp)
        data, offenses = normalize_file(fp, check_only=args.check)

        # In --check mode, do not write; ensure normalized equals original
        if args.check:
            if original != data:
                print(f"❌ not normalized: {fp.name}")
                # optional: show a minimal hint (avoid huge diffs)
                # users should run normalize without --check to rewrite
                all_offenses.append(Offense(file=fp.name, path="<normalized>", default=None, enum=[]))
            else:
                print(f"ok: {fp.name}")
        else:
            save_json(fp, data)
            print(f"normalized: {fp.name}")
        total += 1
        all_offenses.extend(offenses)

    if args.check:
        offenses_only = [o for o in all_offenses if o.path != "<normalized>"]
        not_normalized = any(o.path == "<normalized>" for o in all_offenses)
        if offenses_only:
            print("❌ Optional enum defaults found (disallowed):")
            for v in offenses_only:
                print(f" - {v.file}: {v.path} (default={v.default}, enum={v.enum})")
        if offenses_only or not_normalized:
            return 1

    print(f"done. files: {total}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
