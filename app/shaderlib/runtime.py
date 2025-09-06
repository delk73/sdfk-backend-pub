from __future__ import annotations

"""Runtime helpers for ShaderLib v1."""

from typing import List, Dict
import re

from fastapi import HTTPException
from pydantic import ValidationError

from .schema import ShaderLib, InputParam, verror


_COMMENT_RE = re.compile(r'//.*?$|/\*.*?\*/|"(?:\\.|[^"\\])*"', re.DOTALL | re.MULTILINE)


def validate_input_spec(spec: List[InputParam], path: List[object]) -> List[InputParam]:
    """Validate a list of InputParam items with path prefix."""
    items: List[InputParam] = []
    errors: List[dict] = []
    for i, ip in enumerate(spec):
        try:
            data = ip.model_dump() if isinstance(ip, InputParam) else ip
            items.append(InputParam.model_validate(data))
        except ValidationError as e:  # pragma: no cover - aggregated below
            for err in e.errors():
                loc = list(path) + [i] + list(err["loc"])
                errors.append(verror(loc, err["msg"], code=err["type"]))
    if errors:
        raise HTTPException(status_code=422, detail=errors)
    return items


def collect_effective_inputs(lib: ShaderLib, helper_name: str) -> Dict[str, list]:
    """Merge base and helper requirements into effective spec."""
    helper = lib.helpers.get(helper_name)
    if helper is None:
        raise HTTPException(status_code=404, detail="helper not found")

    uniforms = list(dict.fromkeys(lib.reservedUniforms))
    req_uniforms = helper.requires.uniforms if helper.requires and helper.requires.uniforms else []
    for u in sorted(set(req_uniforms)):
        if u not in uniforms:
            uniforms.append(u)

    base_params = validate_input_spec(lib.baseInputParametersSpec, ["baseInputParametersSpec"])
    helper_params: List[InputParam] = []
    if helper.requires and helper.requires.inputParametersSpec:
        helper_params = validate_input_spec(
            helper.requires.inputParametersSpec,
            ["helpers", helper_name, "requires", "inputParametersSpec"],
        )

    existing = {p.parameter for p in base_params}
    for idx, ip in enumerate(helper_params):
        if ip.parameter in existing:
            raise HTTPException(
                status_code=422,
                detail=[
                    verror(
                        [
                            "helpers",
                            helper_name,
                            "requires",
                            "inputParametersSpec",
                            idx,
                            "parameter",
                        ],
                        f"duplicates base parameter '{ip.parameter}'",
                        code="COLLISION_BASE_PARAMETER",
                    )
                ],
            )
        existing.add(ip.parameter)

    merged = base_params + helper_params
    return {
        "uniforms": uniforms,
        "inputParametersSpec": [p.model_dump(by_alias=True) for p in merged],
    }


def check_template_demonstrates_helper(lib: ShaderLib, helper_name: str) -> Dict[str, object]:
    """Analyse template usage of helper; warn on missing references."""
    tpl = lib.templates.fragment_shader if lib.templates else None
    if not tpl:
        return {"valid": False, "warnings": ["no fragment_shader template"]}
    stripped = _COMMENT_RE.sub("", tpl)
    valid = helper_name in stripped
    warnings: List[str] = []
    helper = lib.helpers.get(helper_name)
    req_uniforms = helper.requires.uniforms if helper and helper.requires and helper.requires.uniforms else []
    extras = [u for u in req_uniforms if u not in lib.reservedUniforms]
    for u in extras:
        if u not in stripped:
            warnings.append(f"uniform '{u}' not referenced")
    return {"valid": valid, "warnings": warnings}
