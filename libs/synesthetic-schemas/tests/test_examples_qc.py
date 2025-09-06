import os
import sys
import json
from pathlib import Path
from tempfile import TemporaryDirectory


# Import module from repo root regardless of cwd
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
import scripts.examples_qc as qc  # noqa: E402


def test_allows_top_level_schema_ref_only():
    schema = {
        "$schema": qc.SCHEMA_META_202012,
        "type": "object",
        "additionalProperties": False,
        "properties": {"name": {"type": "string"}},
        "required": ["name"],
    }
    resolver = qc.jsonschema.RefResolver.from_schema(schema)
    inst = {"$schemaRef": "X", "name": "ok"}
    errors = qc._validate_instance(inst, schema, resolver)
    assert len(errors) == 0


def test_rejects_unknown_top_level_keys_and_envelope_forbidden():
    issues = qc._check_envelope_keys({"id": 1, "schemaVersion": 2, "$foo": 3, "$schemaRef": 4})
    # $schemaRef allowed; others flagged
    pointers = [p for p, _ in issues]
    assert "/id" in pointers
    assert "/schemaVersion" in pointers
    assert "/$foo" in pointers


def test_detects_duplicate_asset_names():
    blessed = [
        ("a.json", {"name": "N"}),
        ("b.json", {"name": "N"}),
        ("c.json", {"name": "M"}),
    ]
    dups = qc._detect_duplicates(blessed)
    assert set(dups.keys()) == {"N"}
    assert dups["N"] == ["a.json", "b.json"]


def test_emits_draft_when_missing_schema(tmp_path: Path):
    # Create minimal workspace
    exdir = tmp_path / "examples"
    exdir.mkdir(parents=True)
    (exdir / "SynestheticAsset_ExampleX.json").write_text(json.dumps({"name": "A"}))

    # Run main from tmp cwd (no canonical schema present)
    cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        code = qc.main(["--print"])  # should succeed with report emission
        assert code in (0, 2)  # duplicates/validation may vary with single file
        assert (tmp_path / qc.DRAFT_SCHEMA_PATH).exists()
        assert (tmp_path / qc.DRAFT_SPEC_MD).exists()
        assert (tmp_path / qc.REPORT_JSON).exists()
    finally:
        os.chdir(cwd)

