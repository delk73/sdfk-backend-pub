#!/usr/bin/env python3
# ruff: noqa
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
import warnings
from typing import Any, Dict, List, Tuple


ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH_DEFAULT = ROOT / "meta" / "prompts" / "ssot.audit.json"
OUT_PATH_DEFAULT = ROOT / "meta" / "output" / "SSOT_AUDIT.md"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text())


def is_pascal_case(name: str) -> bool:
    return bool(re.fullmatch(r"[A-Z][A-Za-z0-9]*", name))


def section(title: str) -> str:
    return f"## {title}\n\n"


def bullet(key: str, val: str) -> str:
    return f"- {key}: {val}\n"


def rel(p: Path) -> str:
    try:
        return str(p.relative_to(ROOT))
    except Exception:
        return str(p)


def c1_version(single_report: List[str]) -> Tuple[bool, List[str]]:
    ok = True
    details: List[str] = []

    # version.json must contain schemaVersion
    vfile = ROOT / "version.json"
    try:
        vdata = load_json(vfile)
        v = vdata.get("schemaVersion")
        if isinstance(v, str) and v:
            details.append(f"Found schemaVersion in {rel(vfile)}: {v}")
        else:
            ok = False
            details.append(f"Missing or invalid schemaVersion in {rel(vfile)}")
    except Exception as e:
        ok = False
        details.append(f"Failed to read {rel(vfile)}: {e}")

    # Python helper reads version.json
    p_helper = ROOT / "scripts" / "lib" / "version.py"
    if p_helper.exists() and "version.json" in p_helper.read_text():
        details.append(f"Python helper references version.json: {rel(p_helper)}")
    else:
        ok = False
        details.append("Python helper missing or does not reference version.json")

    # TS helper reads version.json
    t_helper = ROOT / "codegen" / "lib" / "version.mjs"
    if t_helper.exists() and "version.json" in t_helper.read_text():
        details.append(f"TS helper references version.json: {rel(t_helper)}")
    else:
        ok = False
        details.append("TS helper missing or does not reference version.json")

    return ok, details


def c2_pytyped() -> Tuple[bool, List[str]]:
    p = ROOT / "python" / "src" / "synesthetic_schemas" / "py.typed"
    ok = p.exists()
    return ok, [f"{'Present' if ok else 'Missing'}: {rel(p)}"]


def c3_schema_integrity() -> Tuple[bool, List[str]]:
    details: List[str] = []
    ids: Dict[str, str] = {}
    ok = True
    draft = "https://json-schema.org/draft/2020-12/schema"
    schema_dir = ROOT / "jsonschema"
    files = sorted(schema_dir.glob("*.schema.json"))
    if not files:
        return False, [f"No schemas found in {rel(schema_dir)}"]

    for f in files:
        try:
            data = load_json(f)
        except Exception as e:
            ok = False
            details.append(f"{rel(f)}: failed to parse: {e}")
            continue
        sid = data.get("$id")
        sch = data.get("$schema")
        if not isinstance(sid, str) or not sid:
            ok = False
            details.append(f"{rel(f)}: missing/empty $id")
        else:
            if sid in ids:
                ok = False
                details.append(f"{rel(f)}: duplicate $id also in {ids[sid]}")
            ids[sid] = rel(f)
        if sch != draft:
            ok = False
            details.append(f"{rel(f)}: $schema is '{sch}', expected '{draft}'")

    if ok:
        details.append(f"{len(files)} schemas OK; all unique $id and correct draft")
    return ok, details


def c4_examples_validate(verbose: bool = False) -> Tuple[bool, List[str]]:
    details: List[str] = []
    ok = True
    has_jsonschema = True
    jsonschema = None  # type: ignore
    jsonschema_err: str | None = None
    try:
        import jsonschema  # type: ignore
    except Exception as e:
        has_jsonschema = False
        jsonschema_err = str(e)

    # Load all schemas for resolver store (by both path and $id)
    store: Dict[str, Any] = {}
    schema_dir = ROOT / "jsonschema"
    for f in sorted(schema_dir.glob("*.schema.json")):
        try:
            data = load_json(f)
            store[rel(f)] = data
            if isinstance(data.get("$id"), str):
                store[data["$id"]] = data
        except Exception:
            pass

    # Prefer modern referencing.Registry for resolution; fall back silently
    # to RefResolver (without emitting deprecation warnings) when needed.
    registry = None
    if has_jsonschema:
        try:
            from referencing import Registry, Resource  # type: ignore

            reg = Registry()
            # Add both path and $id variants to the registry
            for k, v in store.items():
                try:
                    reg = reg.with_resource(k, Resource.from_contents(v))
                except Exception:
                    # non-URI keys may raise; best-effort only
                    pass
            registry = reg
        except Exception:
            registry = None

    def load_schema(ref: str) -> Any:
        # prefer path relative to repo root
        p = ROOT / ref
        if p.exists():
            return load_json(p)
        # try store by $id
        if ref in store:
            return store[ref]
        raise FileNotFoundError(ref)

    # Expand and de-duplicate example globs (avoid double-including top-level files)
    examples_root = ROOT / "examples"
    example_set = set()
    for p in examples_root.glob("**/*.json"):
        # Skip any files under folders prefixed with '_' (e.g., examples/_skip/...)
        relp = p.relative_to(examples_root)
        if any(part.startswith("_") for part in relp.parts[:-1]):
            continue
        example_set.add(p.resolve())
    example_paths = sorted(example_set)

    if not example_paths:
        return False, [f"No examples found under {rel(examples_root)}"]

    ok_count = 0
    fail_count = 0
    failures: List[str] = []

    for p in example_paths:
        try:
            data = load_json(p)
        except Exception as e:
            ok = False
            fail_count += 1
            failures.append(f"{rel(p)}: parse error: {e}")
            continue
        ref = data.get("$schemaRef")
        if not isinstance(ref, str) or not ref:
            ok = False
            fail_count += 1
            failures.append(f"{rel(p)}: missing top-level '$schemaRef'")
            continue
        try:
            schema_obj = load_schema(ref)
        except Exception as e:
            ok = False
            fail_count += 1
            failures.append(f"{rel(p)}: schema not found: {ref} ({e})")
            continue

        if has_jsonschema:
            try:
                if registry is not None:
                    validator = jsonschema.Draft202012Validator(schema_obj, registry=registry)  # type: ignore
                    data_to_validate = dict(data) if isinstance(data, dict) else data
                    if isinstance(data_to_validate, dict) and "$schemaRef" in data_to_validate:
                        data_to_validate.pop("$schemaRef", None)
                    validator.validate(data_to_validate)
                else:
                    with warnings.catch_warnings():
                        warnings.filterwarnings("ignore", category=DeprecationWarning, module="jsonschema")
                        resolver = jsonschema.RefResolver.from_schema(schema_obj, store=store)  # type: ignore
                        validator = jsonschema.Draft202012Validator(schema_obj, resolver=resolver)  # type: ignore
                        data_to_validate = dict(data) if isinstance(data, dict) else data
                        if isinstance(data_to_validate, dict) and "$schemaRef" in data_to_validate:
                            data_to_validate.pop("$schemaRef", None)
                        validator.validate(data_to_validate)
                ok_count += 1
                if verbose:
                    details.append(f"{rel(p)}: OK against {ref}")
            except Exception as e:
                ok = False
                fail_count += 1
                msg = getattr(e, "message", str(e))
                instance_path = "/".join([str(x) for x in getattr(e, "path", [])])
                schema_path = "/".join([str(x) for x in getattr(e, "schema_path", [])])
                where = []
                if instance_path:
                    where.append(f"instance: /{instance_path}")
                if schema_path:
                    where.append(f"schema: /{schema_path}")
                where_str = f" ({'; '.join(where)})" if where else ""
                failures.append(f"{rel(p)}: validation failed: {msg}{where_str}")
        else:
            # Presence-only: schemaRef exists and resolves
            ok_count += 1
            if verbose:
                details.append(f"{rel(p)}: schemaRef OK → {ref} (presence-only)")

    # Summarize results compactly by default
    if not verbose:
        if has_jsonschema:
            if ok_count:
                details.append(f"{ok_count} examples OK")
        else:
            suffix = f" (presence-only; jsonschema missing: {jsonschema_err})" if jsonschema_err else " (presence-only)"
            details.append(f"{ok_count} examples OK{suffix}")
        for fmsg in failures:
            details.append(f"- {fmsg}")
    else:
        for fmsg in failures:
            details.append(f"- {fmsg}")

    # Overall status is True only if no failures
    ok = ok and fail_count == 0
    return ok, details


def c5_codegen_ci() -> Tuple[bool, List[str]]:
    details: List[str] = []
    ok = True

    gen_ts = (ROOT / "codegen" / "gen_ts.sh").read_text()
    if "node_modules/.bin" in gen_ts and "json2ts" in gen_ts:
        details.append("TS codegen uses repo-local json2ts (node_modules/.bin)")
    else:
        ok = False
        details.append("TS codegen does not use repo-local tooling")

    gen_py = (ROOT / "codegen" / "gen_py.sh").read_text()
    if "datamodel-codegen" in gen_py or "datamodel_code_generator" in gen_py:
        details.append("Python codegen uses datamodel-code-generator (CLI or module)")
    else:
        ok = False
        details.append("Python codegen missing datamodel-code-generator invocation")

    ensure = (ROOT / "scripts" / "ensure_codegen_clean.sh").read_text()
    if "git diff --exit-code" in ensure:
        details.append("ensure_codegen_clean.sh fails on real diffs")
    else:
        ok = False
        details.append("ensure_codegen_clean.sh does not enforce failure on diffs")

    wf = (ROOT / ".github" / "workflows" / "ci.yml").read_text()
    if "bash ./preflight.sh" in wf:
        details.append("CI executes the same preflight.sh as local")
    else:
        ok = False
        details.append("CI workflow does not call preflight.sh")

    return ok, details


def c6_naming_docs() -> Tuple[bool, List[str]]:
    details: List[str] = []
    ok = True
    schema_dir = ROOT / "jsonschema"
    files = sorted(schema_dir.glob("*.schema.json"))

    # Check: $defs keys PascalCase; top-level title matches kebab-case file stem; $id ends with filename
    for f in files:
        data = load_json(f)
        title = data.get("title")
        stem = f.stem
        if stem.endswith(".schema"):
            stem = stem[: -len(".schema")]
        expected_title = stem  # kebab-case of base name is written by normalizer
        if isinstance(title, str) and title == expected_title:
            pass
        else:
            ok = False
            details.append(f"{rel(f)}: top-level title should equal '{expected_title}', found: {title!r}")
        sid = data.get("$id")
        if isinstance(sid, str) and sid.endswith("/" + f.name):
            pass
        else:
            ok = False
            details.append(f"{rel(f)}: $id should end with '/{f.name}', found: {sid!r}")
        defs = data.get("$defs")
        if isinstance(defs, dict) and defs:
            bad = [k for k in defs.keys() if not is_pascal_case(k)]
            if bad:
                ok = False
                details.append(f"{rel(f)}: non-PascalCase $defs: {', '.join(bad)}")
        # It's okay if a schema has no $defs

    # Docs mention preflight and versioning
    readme = (ROOT / "README.md").read_text()
    contrib = (ROOT / "CONTRIBUTING.md").read_text()
    if "preflight" in readme.lower() and "version" in readme.lower():
        details.append("README describes preflight and versioning workflows")
    else:
        ok = False
        details.append("README missing preflight/versioning guidance")
    if "preflight" in contrib.lower() or "contribut" in contrib.lower():
        details.append("CONTRIBUTING mentions contributor workflows")
    else:
        ok = False
        details.append("CONTRIBUTING missing contributor workflow notes")

    return ok, details


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser(description="SSOT repo auditor (deterministic Markdown)")
    ap.add_argument("--spec", type=Path, default=SPEC_PATH_DEFAULT)
    ap.add_argument("--out", type=Path, default=OUT_PATH_DEFAULT)
    ap.add_argument("--verbose", "-v", action="store_true", help="emit per-file OK lines and full details")
    args = ap.parse_args(argv)

    spec = load_json(args.spec)

    # If caller did not override --out, honor the path requested in spec.constraints.output
    # Expect strings like: "Markdown only; write to meta/output/SSOT_AUDIT.md; do not print to stdout"
    def _extract_out_path(text: str | None) -> Path | None:
        if not isinstance(text, str):
            return None
        m = re.search(r"write to\s+([^;]+)", text, flags=re.IGNORECASE)
        if m:
            raw = m.group(1).strip()
            try:
                return (ROOT / raw).resolve()
            except Exception:
                return None
        # If it looks like a plain relative path, accept it
        if text.endswith(".md") and "/" in text:
            try:
                return (ROOT / text).resolve()
            except Exception:
                return None
        return None

    if args.out == OUT_PATH_DEFAULT:
        constraints = spec.get("constraints", {}) if isinstance(spec, dict) else {}
        out_decl: str | None = constraints.get("output") if isinstance(constraints, dict) else None
        derived = _extract_out_path(out_decl)
        if derived is not None:
            args.out = derived

    # Collect results
    results: Dict[str, Tuple[bool, List[str]]] = {}
    results["C1"] = c1_version([])
    results["C2"] = c2_pytyped()
    results["C3"] = c3_schema_integrity()
    results["C4"] = c4_examples_validate(verbose=args.verbose)
    results["C5"] = c5_codegen_ci()
    results["C6"] = c6_naming_docs()

    # Build deterministic Markdown output (no timestamps)
    out: List[str] = []
    out.append(f"# SSOT Audit Report\n\n")
    out.append(bullet("Objective", spec.get("objective", "")))
    cons = spec.get("constraints", {})
    if isinstance(cons, dict):
        out.append("- Constraints:\n")
        for k in sorted(cons.keys()):
            out.append(f"  - {k}: {cons[k]}\n")
    out.append("\n")

    # Phases mapping
    phase_names = {p["id"]: p["name"] for p in spec.get("phases", [])}
    # Group work items by phase
    items = spec.get("work_items", [])
    phase_to_items: Dict[str, List[Dict[str, Any]]] = {}
    for it in items:
        phase_to_items.setdefault(it.get("phase", ""), []).append(it)
    for k in phase_to_items:
        phase_to_items[k].sort(key=lambda x: x.get("id", ""))

    # Emit sections per phase / item
    for phase_id in sorted(phase_to_items.keys()):
        out.append(section(f"{phase_id} — {phase_names.get(phase_id, '')}".strip()))
        for it in phase_to_items[phase_id]:
            iid = it.get("id")
            name = it.get("summary", "")
            ok, det = results.get(iid, (False, ["No result"]))
            status = "PASS" if ok else "FAIL"
            out.append(f"### {iid}: {name} — {status}\n\n")
            for line in det:
                out.append(f"- {line}\n")
            if it.get("audit"):
                out.append("- Checks: " + "; ".join(it.get("audit")) + "\n")
            if it.get("acceptance"):
                out.append("- Acceptance: " + "; ".join(it.get("acceptance")) + "\n")
            out.append("\n")

    # Done definition
    done_def = spec.get("done_definition", [])
    if done_def:
        out.append(section("Done Definition"))
        for d in done_def:
            out.append(f"- {d}\n")

    # Ensure output directory exists
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("".join(out))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
