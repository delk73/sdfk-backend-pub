## SSOT Candidates
Current state: Mixed/None. 77 schemas vs 15 models; 26 entities used in routes.

## Entity Map (Parity Matrix)
Entity | ORM Model (file:Class) | API Schema(s) (file:Class) | Used in Routes (paths) | Proto? | Status
---|---|---|---|---|---
ActionType | – | app/schemas/control.py:ActionType | – | no | Unused/Orphaned
ApplyModulationRequest | – | app/schemas/mcp/asset.py:ApplyModulationRequest | /mcp/asset/modulate | no | Missing ORM
ApplyModulationResponse | – | app/schemas/mcp/asset.py:ApplyModulationResponse | /mcp/asset/modulate | no | Missing ORM
ApplyModulationResult | – | app/schemas/mcp/asset.py:ApplyModulationResult | – | no | Unused/Orphaned
Asset | – | – | – | yes | Unused/Orphaned
AssetEmbedding | app/models/asset_embedding.py:AssetEmbedding | – | – | no | Unused/Orphaned
ComboType | – | app/schemas/control.py:ComboType | – | no | Unused/Orphaned
ComputeShader | – | app/schemas/compute_shader.py:ComputeShader | – | no | Unused/Orphaned
ComputeShaderBase | – | app/schemas/compute_shader.py:ComputeShaderBase | – | no | Unused/Orphaned
ComputeShaderCreate | – | app/schemas/compute_shader.py:ComputeShaderCreate | – | no | Unused/Orphaned
ComputeShaderUpdate | – | app/schemas/compute_shader.py:ComputeShaderUpdate | – | no | Unused/Orphaned
Control | app/models/control.py:Control | app/schemas/control.py:Control; app/schemas/control.py:ControlBase; app/schemas/control.py:ControlCreate; app/schemas/control.py:ControlCreate; app/schemas/control.py:ControlResponse | /controls/, /controls/{item_id} | no | OK (1:1)
CreateAssetRequest | – | app/schemas/mcp/asset.py:CreateAssetRequest | /mcp/asset/create | no | Missing ORM
CreateAssetResponse | – | app/schemas/mcp/asset.py:CreateAssetResponse | /mcp/asset/create | no | Missing ORM
CreateAssetResult | – | app/schemas/mcp/asset.py:CreateAssetResult | – | no | Unused/Orphaned
DeviceConfig | – | app/schemas/haptic.py:DeviceConfig | – | no | Unused/Orphaned
DeviceOptionValue | – | app/schemas/haptic.py:DeviceOptionValue | – | no | Unused/Orphaned
EmbeddingDeleteResponse | – | app/schemas/embedding.py:EmbeddingDeleteResponse | /embeddings/{patch_id} | no | Missing ORM
EmbeddingQuery | – | app/schemas/embedding.py:EmbeddingQuery | /embeddings/query, /search/assets | no | Missing ORM
Envelope | – | – | – | yes | Unused/Orphaned
ErrorDetail | – | app/schemas/error.py:ErrorDetail | – | no | Unused/Orphaned
ErrorResponse | – | app/schemas/error.py:ErrorResponse | – | no | Unused/Orphaned
GenerateDebugResponse | – | app/schemas/generative.py:GenerateDebugResponse | – | no | Unused/Orphaned
Haptic | app/models/haptic.py:Haptic | app/schemas/haptic.py:Haptic; app/schemas/haptic.py:HapticBase; app/schemas/haptic.py:HapticCreate; app/schemas/haptic.py:HapticCreate; app/schemas/haptic.py:HapticParameter; app/schemas/haptic.py:HapticUpdate | /haptics/, /haptics/{item_id}, /synesthetic-assets/{asset_id}/haptic | no | OK (1:1)
InputParameter | – | app/schemas/shader.py:InputParameter; app/schemas/shader.py:InputParameter | – | no | Unused/Orphaned
Item | app/models/item.py:Item | app/schemas/base_schema.py:Item; app/schemas/base_schema.py:ItemBase | – | no | Missing Router
LabAuditRequest | – | app/schemas/lab.py:LabAuditRequest | – | no | Unused/Orphaned
LabAuditResponse | – | app/schemas/lab.py:LabAuditResponse | – | no | Unused/Orphaned
LabCombinedRequest | – | app/schemas/lab.py:LabCombinedRequest | – | no | Unused/Orphaned
LabCombinedResponse | – | app/schemas/lab.py:LabCombinedResponse | – | no | Unused/Orphaned
LabGenerateAndAuditResponse | – | app/schemas/lab.py:LabGenerateAndAuditResponse | – | no | Unused/Orphaned
LabGenerateRequest | – | app/schemas/lab.py:LabGenerateRequest | – | no | Unused/Orphaned
LabGenerateResponse | – | app/schemas/lab.py:LabGenerateResponse | – | no | Unused/Orphaned
MCPBaseResponse | – | app/schemas/mcp/asset.py:MCPBaseResponse | – | no | Unused/Orphaned
MCPCommandLog | app/models/mcp_command.py:MCPCommandLog | app/schemas/mcp/command.py:MCPCommandLog; app/schemas/mcp/command.py:MCPCommandLogBase; app/schemas/mcp/command.py:MCPCommandLogCreate; app/schemas/mcp/command.py:MCPCommandLogResponse; app/schemas/mcp/command.py:MCPCommandLogUpdate | – | no | Missing Router
Mapping | – | app/schemas/control.py:Mapping | – | no | Unused/Orphaned
Modulation | app/models/modulation.py:Modulation | app/schemas/modulation.py:Modulation; app/schemas/modulation.py:Modulation; app/schemas/modulation.py:ModulationBase; app/schemas/modulation.py:ModulationCreate; app/schemas/modulation.py:ModulationCreate; app/schemas/modulation.py:ModulationItem; app/schemas/modulation.py:ModulationUpdate | /modulations/, /modulations/{item_id} | no | OK (1:1)
NestedControlResponse | – | app/schemas/synesthetic_asset.py:NestedControlResponse | – | no | Unused/Orphaned
NestedHapticResponse | – | app/schemas/synesthetic_asset.py:NestedHapticResponse | – | no | Unused/Orphaned
NestedShaderResponse | – | app/schemas/synesthetic_asset.py:NestedShaderResponse | – | no | Unused/Orphaned
NestedSynestheticAsset | – | app/schemas/synesthetic_asset.py:NestedSynestheticAsset | – | no | Unused/Orphaned
NestedSynestheticAssetCreate | – | app/schemas/synesthetic_asset.py:NestedSynestheticAssetCreate; app/schemas/synesthetic_asset.py:NestedSynestheticAssetCreate | /synesthetic-assets/nested | no | Missing ORM
NestedSynestheticAssetResponse | – | app/schemas/synesthetic_asset.py:NestedSynestheticAssetResponse; app/schemas/synesthetic_asset.py:NestedSynestheticAssetResponse | /synesthetic-assets/apply/{asset_id}/{patch_id}, /synesthetic-assets/nested, /synesthetic-assets/{asset_id}/haptic, /synesthetic-assets/{asset_id}/shader, /synesthetic-assets/{asset_id}/tone | no | Missing ORM
NestedToneResponse | – | app/schemas/synesthetic_asset.py:NestedToneResponse | – | no | Unused/Orphaned
Oscillator | – | – | – | yes | Unused/Orphaned
PatchEmbedding | app/models/patch_embedding.py:PatchEmbedding | app/schemas/embedding.py:PatchEmbedding; app/schemas/embedding.py:PatchEmbeddingBase; app/schemas/embedding.py:PatchEmbeddingCreate | /embeddings/, /embeddings/{patch_id} | no | OK (1:1)
PatchIndex | app/models/patch_index.py:PatchIndex | app/schemas/patch_index.py:PatchIndex | – | no | Missing Router
PatchRating | app/models/patch_rating.py:PatchRating | app/schemas/patch.py:PatchRating; app/schemas/patch.py:PatchRatingBase; app/schemas/patch.py:PatchRatingCreate; app/schemas/patch.py:PatchRatingScore | /patch_ratings | no | OK (1:1)
PingResponse | – | app/schemas/mcp/asset.py:PingResponse | /mcp/asset/ping | no | Missing ORM
PreviewNestedAssetResponse | – | app/schemas/synesthetic_asset.py:PreviewNestedAssetResponse | /synesthetic-assets/nested/{asset_id} | no | Missing ORM
ProtoAsset | app/models/proto_asset.py:ProtoAsset | – | – | no | Unused/Orphaned
RuleBundle | app/models/rule_bundle.py:RuleBundle | app/schemas/rule_bundle.py:RuleBundleSchema; app/schemas/rule_bundle.py:RuleBundleSchema | /rule-bundles/, /rule-bundles/import, /rule-bundles/{bundle_id} | no | OK (1:1)
RuleSchema | – | app/schemas/rule_bundle.py:RuleSchema | – | no | Unused/Orphaned
SchemaBase | – | app/schemas/base_schema.py:SchemaBase; app/schemas/base_schema.py:SchemaBase; app/schemas/base_schema.py:SchemaBase; app/schemas/base_schema.py:SchemaBase; app/schemas/base_schema.py:SchemaBase; app/schemas/base_schema.py:SchemaBase; app/schemas/base_schema.py:SchemaBase; app/schemas/base_schema.py:SchemaBase; app/schemas/base_schema.py:SchemaBase; app/schemas/base_schema.py:SchemaBase; app/schemas/base_schema.py:SchemaBase | – | no | Unused/Orphaned
Shader | app/models/shader.py:Shader | app/schemas/lab.py:ShaderCandidate; app/schemas/shader.py:Shader; app/schemas/shader.py:ShaderBase; app/schemas/shader.py:ShaderCreate; app/schemas/shader.py:ShaderCreate; app/schemas/shader.py:ShaderLib; app/schemas/shader.py:ShaderLibCreate; app/schemas/shader.py:ShaderUpdate | /shader_libs/, /shader_libs/{item_id}, /shaders/, /shaders/{item_id}, /synesthetic-assets/{asset_id}/shader | yes | OK (1:1)
ShaderLib | app/models/shader_lib.py:ShaderLib | – | – | no | Unused/Orphaned
SynestheticAsset | app/models/synesthetic_asset.py:SynestheticAsset | app/schemas/synesthetic_asset.py:SynestheticAsset; app/schemas/synesthetic_asset.py:SynestheticAssetBase; app/schemas/synesthetic_asset.py:SynestheticAssetCreate; app/schemas/synesthetic_asset.py:SynestheticAssetNestedPatched; app/schemas/synesthetic_asset.py:SynestheticAssetResponse; app/schemas/synesthetic_asset.py:SynestheticAssetUpdate | /synesthetic-assets/, /synesthetic-assets/{asset_id} | no | OK (1:1)
Tone | app/models/tone.py:Tone | app/schemas/tone.py:Tone; app/schemas/tone.py:ToneBase; app/schemas/tone.py:ToneCreate; app/schemas/tone.py:ToneCreate; app/schemas/tone.py:ToneEffect; app/schemas/tone.py:ToneMapping; app/schemas/tone.py:ToneMetaInfo; app/schemas/tone.py:ToneParameter; app/schemas/tone.py:TonePart; app/schemas/tone.py:TonePattern; app/schemas/tone.py:ToneSynth; app/schemas/tone.py:ToneSynthOptions; app/schemas/tone.py:ToneTarget; app/schemas/tone.py:ToneUpdate | /synesthetic-assets/{asset_id}/tone, /tones/, /tones/{tone_id} | yes | OK (1:1)
ToneSynth | – | – | – | yes | Unused/Orphaned
Uniform | – | app/schemas/vectors.py:Uniform | – | yes | Unused/Orphaned
UniformBase | – | app/schemas/vectors.py:UniformBase | – | no | Unused/Orphaned
UniformDef | – | app/schemas/shader.py:UniformDef; app/schemas/shader.py:UniformDef | – | no | Unused/Orphaned
UpdateParamRequest | – | app/schemas/mcp/asset.py:UpdateParamRequest | /mcp/asset/update | no | Missing ORM
UpdateParamResponse | – | app/schemas/mcp/asset.py:UpdateParamResponse | /mcp/asset/update | no | Missing ORM
UpdateParamResult | – | app/schemas/mcp/asset.py:UpdateParamResult | – | no | Unused/Orphaned
UpdateQueueStatusRequest | – | app/schemas/generative.py:UpdateQueueStatusRequest | – | no | Unused/Orphaned
ValidateAssetRequest | – | app/schemas/mcp/asset.py:ValidateAssetRequest | /mcp/asset/validate | no | Missing ORM
ValidateAssetResponse | – | app/schemas/mcp/asset.py:ValidateAssetResponse | /mcp/asset/validate | no | Missing ORM
ValidateAssetResult | – | app/schemas/mcp/asset.py:ValidateAssetResult | – | no | Unused/Orphaned
Vec2 | – | app/schemas/vectors.py:Vec2 | – | no | Unused/Orphaned
Vec3 | – | app/schemas/vectors.py:Vec3 | – | no | Unused/Orphaned
Vec4 | – | app/schemas/vectors.py:Vec4 | – | no | Unused/Orphaned

## Field Drift Report
- Control:
  - parameter: missing in model
  - label: missing in model
  - type: missing in model
  - unit: missing in model
  - default: missing in model
  - min: missing in model
  - max: missing in model
  - step: missing in model
  - smoothingTime: missing in model
  - options: missing in model
  - mappings: missing in model
  - control_id: missing in schema
  - name: missing in schema
  - description: missing in schema
  - meta_info: missing in schema
  - control_parameters: missing in schema
- Haptic:
  - meta_info: model non-nullable but schema optional
  - input_parameters: schema requires but model nullable
- Item:
  - name: schema requires but model nullable
  - createdAt: missing in schema
- MCPCommandLog:
  - status: model non-nullable but schema optional
- Modulation:
  - meta_info: model non-nullable but schema optional
- PatchRating:
  - created_at: schema requires but model nullable
- RuleBundle:
  - id: model non-nullable but schema optional
  - meta_info: model non-nullable but schema optional
  - created_at: model non-nullable but schema optional
  - updated_at: model non-nullable but schema optional
- Shader:
  - glsl: missing in model
  - notes: missing in model
  - shader_id: missing in schema
  - name: missing in schema
  - description: missing in schema
  - meta_info: missing in schema
  - vertex_shader: missing in schema
  - fragment_shader: missing in schema
  - shader_lib_id: missing in schema
  - uniforms: missing in schema
- SynestheticAsset:
  - meta_info: model non-nullable but schema optional
  - modulations: missing in model
  - created_at: schema requires but model nullable
  - updated_at: schema requires but model nullable
  - shader: missing in model
  - control: missing in model
  - tone: missing in model
  - haptic: missing in model
  - modulation: missing in model
  - control_parameters: missing in model
  - is_canonical: missing in schema
  - quality_tags: missing in schema
- Tone:
  - synth: schema requires but model nullable
  - tone_id: missing in schema

## Route Reality Check
Method(s) | Path | Handler (module:function) | Response Model
---|---|---|---
GET | / | app.main:root | –
GET | /cache | app.routers.cache_toggle:get_cache_status | CacheStatus
POST | /cache | app.routers.cache_toggle:set_cache_status | CacheStatus
GET | /controls/ | app.utils.crud_router:read_items | List
POST | /controls/ | app.utils.crud_router:create_item | ControlResponse
DELETE | /controls/{item_id} | app.utils.crud_router:delete_item | ControlResponse
GET | /controls/{item_id} | app.utils.crud_router:read_item | ControlResponse
PUT | /controls/{item_id} | app.utils.crud_router:update_item | ControlResponse
GET | /docs | app.main:custom_swagger_ui_html | –
POST | /embeddings/ | app.routers.embeddings:create_embedding | PatchEmbedding
POST | /embeddings/query | app.routers.embeddings:query_embeddings | list
DELETE | /embeddings/{patch_id} | app.routers.embeddings:delete_embedding | EmbeddingDeleteResponse
GET | /embeddings/{patch_id} | app.routers.embeddings:read_embedding | PatchEmbedding
PUT | /embeddings/{patch_id} | app.routers.embeddings:update_embedding | PatchEmbedding
GET | /haptics/ | app.utils.crud_router:read_items | List
POST | /haptics/ | app.utils.crud_router:create_item | Haptic
DELETE | /haptics/{item_id} | app.utils.crud_router:delete_item | Haptic
GET | /haptics/{item_id} | app.utils.crud_router:read_item | Haptic
PUT | /haptics/{item_id} | app.utils.crud_router:update_item | Haptic
GET | /health | app.main:health_check | –
POST | /mcp/asset/create | app.routers.mcp.asset:create_asset | CreateAssetResponse
POST | /mcp/asset/modulate | app.routers.mcp.asset:apply_modulation | ApplyModulationResponse
GET | /mcp/asset/ping | app.routers.mcp.asset:ping_asset | PingResponse
POST | /mcp/asset/update | app.routers.mcp.asset:update_param | UpdateParamResponse
POST | /mcp/asset/validate | app.routers.mcp.asset:validate_asset | ValidateAssetResponse
GET | /modulations/ | app.utils.crud_router:read_items | List
POST | /modulations/ | app.utils.crud_router:create_item | Modulation
DELETE | /modulations/{item_id} | app.utils.crud_router:delete_item | Modulation
GET | /modulations/{item_id} | app.utils.crud_router:read_item | Modulation
PUT | /modulations/{item_id} | app.utils.crud_router:update_item | Modulation
POST | /patch_ratings | app.routers.patches:submit_rating | PatchRating
GET | /ping | app.main:ping | –
POST | /protobuf-assets/ | app.routers.pb_assets:create_asset_proto | –
POST | /protobuf-assets/from-synesthetic/{syn_asset_id} | app.routers.pb_assets:create_from_synesthetic | –
DELETE | /protobuf-assets/{asset_id} | app.routers.pb_assets:delete_asset_proto | –
GET | /protobuf-assets/{asset_id} | app.routers.pb_assets:get_asset_proto | –
PUT | /protobuf-assets/{asset_id} | app.routers.pb_assets:update_asset_proto | –
GET | /redoc | app.main:redoc_html | –
POST | /rule-bundles/ | app.routers.rule_bundles:create_bundle | RuleBundleSchema
POST | /rule-bundles/import | app.routers.rule_bundles:import_bundle | RuleBundleSchema
GET | /rule-bundles/{bundle_id} | app.routers.rule_bundles:get_bundle | RuleBundleSchema
POST | /search/assets | app.routers.search:search_assets | list
GET | /shader_libs/ | app.utils.crud_router:read_items | List
POST | /shader_libs/ | app.utils.crud_router:create_item | ShaderLib
GET | /shader_libs/{id}/helpers/{name}/effective | app.routers.shader_libs:get_effective_helper | –
DELETE | /shader_libs/{item_id} | app.utils.crud_router:delete_item | ShaderLib
GET | /shader_libs/{item_id} | app.utils.crud_router:read_item | ShaderLib
PUT | /shader_libs/{item_id} | app.utils.crud_router:update_item | ShaderLib
GET | /shaders/ | app.utils.crud_router:read_items | List
POST | /shaders/ | app.utils.crud_router:create_item | Shader
DELETE | /shaders/{item_id} | app.utils.crud_router:delete_item | Shader
GET | /shaders/{item_id} | app.utils.crud_router:read_item | Shader
PUT | /shaders/{item_id} | app.utils.crud_router:update_item | Shader
GET | /synesthetic-assets/ | app.routers.synesthetic_assets:get_synesthetic_assets | List
POST | /synesthetic-assets/ | app.routers.synesthetic_assets:create_synesthetic_asset | SynestheticAssetResponse
PUT | /synesthetic-assets/apply/{asset_id}/{patch_id} | app.routers.synesthetic_assets:apply_stored_patch | NestedSynestheticAssetResponse
POST | /synesthetic-assets/nested | app.routers.synesthetic_assets:create_nested_synesthetic_asset | NestedSynestheticAssetResponse
GET | /synesthetic-assets/nested/{asset_id} | app.routers.synesthetic_assets:get_nested_synesthetic_asset | PreviewNestedAssetResponse
GET | /synesthetic-assets/offset/ | app.routers.synesthetic_assets:get_synesthetic_assets_offset | List
DELETE | /synesthetic-assets/{asset_id} | app.routers.synesthetic_assets:delete_synesthetic_asset | SynestheticAssetResponse
GET | /synesthetic-assets/{asset_id} | app.routers.synesthetic_assets:get_synesthetic_asset | SynestheticAssetResponse
PUT | /synesthetic-assets/{asset_id} | app.routers.synesthetic_assets:update_synesthetic_asset | SynestheticAssetResponse
PUT | /synesthetic-assets/{asset_id}/haptic | app.routers.synesthetic_assets:update_asset_haptic | NestedSynestheticAssetResponse
PUT | /synesthetic-assets/{asset_id}/shader | app.routers.synesthetic_assets:update_asset_shader | NestedSynestheticAssetResponse
PUT | /synesthetic-assets/{asset_id}/tone | app.routers.synesthetic_assets:update_asset_tone | NestedSynestheticAssetResponse
GET | /tones/ | app.routers.tones:get_tones | List
POST | /tones/ | app.routers.tones:create_tone | Tone
DELETE | /tones/{tone_id} | app.routers.tones:delete_tone | Tone
GET | /tones/{tone_id} | app.routers.tones:get_tone | Tone
PUT | /tones/{tone_id} | app.routers.tones:update_tone | Tone

## Config Lineage Sanity
ENV Key | Purpose | Used In (files) | Status
---|---|---|---
CACHE_ENABLED | – | app/cache.py, app/main.py, app/routers/cache_toggle.py, tests/unit/test_cache_shutdown.py | OK
DATABASE_URL | – | alembic/env.py, app/main.py, app/models/db.py, scripts/route_audit.py, tests/conftest.py | OK
JWT_SECRET | – | app/security.py | OK
REDIS_URL | – | app/cache.py | OK
RLHF_DATASET_PATH | – | – | Declared-not-used
RLHF_TRAIN_CMD | – | – | Declared-not-used
TESTING | – | app/main.py, tests/conftest.py | OK

## Orphans & Dead Code
Models without schema/router: ProtoAsset, ShaderLib
Schemas without model/router: ActionType, ApplyModulationResult, ComboType, ComputeShader, ComputeShaderBase, ComputeShaderCreate, ComputeShaderUpdate, CreateAssetResult, DeviceConfig, DeviceOptionValue, ErrorDetail, ErrorResponse, InputParameter, LabAuditRequest, LabAuditResponse, LabCombinedRequest, LabCombinedResponse, LabGenerateAndAuditResponse, LabGenerateRequest, LabGenerateResponse, MCPBaseResponse, NestedControlResponse, NestedHapticResponse, NestedShaderResponse, NestedSynestheticAsset, NestedToneResponse, RuleSchema, SchemaBase, UniformBase, UpdateParamResult, UpdateQueueStatusRequest, ValidateAssetResult, Vec2, Vec3, Vec4
Routers with zero routes: app/routers/factory.py

## Drift Risk Score
5 – Mixed SSOT, 51 field drifts, 1 used-not-declared env keys

## Decision & Rationale
Decision: Unified (no clear SSOT). The mix of schema-only endpoints and unused models prevents a single source of truth.

## Cleanup Plan (Task/Validation Pairs)
1. **Task:** Remove or implement ORM models for schema-only endpoints. **Validation:** `rg "Missing ORM" docs/SSOT_AUDIT.md` returns empty.
2. **Task:** Align schema required flags with ORM nullability for listed drifts. **Validation:** parity script shows zero field drift entries.
3. **Task:** Add missing env keys to `Settings` or purge unused ones. **Validation:** rerun audit; all env keys status become OK.
4. **Task:** Wire unused routers or delete them. **Validation:** `python scripts/route_audit.py` shows no routers with zero routes.