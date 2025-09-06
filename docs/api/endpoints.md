---
version: v0.5.4
lastReviewed: 2025-08-24
owner: backend@generative
---
# API Endpoints (Code-Verified)
> No /lab routes detected in code.

## Other Routers (compact index)
- /synesthetic-assets — Asset CRUD & retrieval (`POST /synesthetic-assets/`, `GET /synesthetic-assets/nested/{asset_id}`)
- /tones — Tone management (`POST /tones/`, `GET /tones/{tone_id}`, `PUT /tones/{tone_id}`)
- /controls — Control CRUD (`POST /controls/`, `GET /controls/{item_id}`)
- /shaders — Shader CRUD (`POST /shaders/`, `GET /shaders/{item_id}`)
- /shader_libs — Shader library CRUD & helper introspection (`GET /shader_libs/{id}`, `GET /shader_libs/{id}/helpers/{name}/effective`)
- /haptics — Haptic CRUD (`POST /haptics/`, `GET /haptics/{item_id}`)
- /modulations — Modulation CRUD (`POST /modulations/`, `GET /modulations/{item_id}`)
- /protobuf-assets — Protobuf asset I/O (`POST /protobuf-assets/`, `GET /protobuf-assets/{asset_id}`)
- /embeddings — Embedding store & query (`POST /embeddings/`, `GET /embeddings/{patch_id}`, `POST /embeddings/query`)
- /search — Semantic asset search (`POST /search/assets`)
- /rule-bundles — Rule bundle import/export (`POST /rule-bundles/`, `GET /rule-bundles/{bundle_id}`, `POST /rule-bundles/import`)
- /cache — Runtime cache toggle (`GET /cache`, `POST /cache`)
- /mcp/asset — MCP asset operations (`GET /mcp/asset/ping`, `POST /mcp/asset/create`, `POST /mcp/asset/modulate`)

## Verification tips (local)
python scripts/dump_routes.py | head -n 20 → confirm no /lab
rg '@(get|post|put|delete)\\(' app/routers -n | head
rg 'include_router' app/main.py -n
## Schema Versioning

- Optional header: `X-Schema-Version`
  - Absent: requests proceed (backwards-compatible)
  - Mismatch: `409 Conflict` with expected version in response body
- Server schema version endpoint: `GET /schema/version`
