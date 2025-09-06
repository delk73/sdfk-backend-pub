---
version: TBD
lastReviewed: 2025-07-17
---

## Overview

This document captures the **frozen state** of the SDFK Backend error handling architecture as of Mission M1.0. All patterns, conventions, and implementations documented here are considered **stable and locked** for production use. Future changes to error handling must be explicitly planned and should maintain backward compatibility with these established patterns.

## Architecture Summary

### Core Components

1. **Global Exception Handlers** (`app/error_handlers.py`)
   - HTTPException handler with request ID correlation
   - RequestValidationError handler with detailed field errors  
   - Generic Exception handler with 500 fallback
   - All handlers return standardized ErrorResponse schema

2. **Error Schemas** (`app/schemas/error.py`)
   - `ErrorResponse` - Primary error response format
   - `ErrorDetail` - Individual error detail structure
   - Request ID correlation built into all error responses

3. **Error Utilities** (`app/utils/errors.py`)
   - `json_error()` - Canonical JSON error response factory
   - Standardized error message formatting

4. **Request ID Middleware** (`app/middleware/request_id.py`)
   - Automatic request ID generation and propagation
   - Error correlation across logs and responses

## Canonical Status Code Mappings

### ✅ LOCKED - These mappings are FROZEN

| Status Code | Use Case | Exception Type | Router Implementation |
|-------------|----------|----------------|----------------------|
| **404** | Resource not found | `HTTPException(404)` | All CRUD routers |
| **409** | Resource conflicts (duplicate names, integrity violations) | `HTTPException(409)` | All creation endpoints |
| **422** | Request validation errors | `RequestValidationError` | FastAPI automatic validation |
| **500** | Internal server errors | `Exception` (generic) | Global exception handler |
| **502** | Upstream service errors (bad responses) | `HTTPException(502)` | Ollama router |
| **503** | Service unavailable (connection failures) | `HTTPException(503)` | Ollama router |

### Request Validation (422) Details
- **Automatic**: FastAPI Pydantic validation failures
- **Pattern**: Return field-level error details when possible

### Resource Conflicts (409) Details
- **Database Integrity Violations**: SQLAlchemy `IntegrityError` → 409
- **Duplicate Resource Names**: Explicit checks in routers → 409
- **Business Logic Conflicts**: Custom validation → 409

## Error Response Schema (FROZEN)

```json
{
  "detail": "Human-readable error message",
  "request_id": "uuid-correlation-id",
  "error_code": "optional-machine-readable-code", 
  "errors": [
    {
      "loc": ["field", "path"],
      "msg": "Field-specific error message",
      "type": "error_type"
    }
  ]
}
```

**Schema Rules (LOCKED)**:
- `detail` is ALWAYS present and human-readable
- `request_id` is ALWAYS present for error correlation
- `errors` array is present for validation errors (422)
- `error_code` is optional but recommended for machine processing

## Router Implementation Patterns (FROZEN)

### Standard CRUD Error Handling

```python
# GET /{resource}/{id} - 404 for not found
if not resource:
    raise HTTPException(status_code=404, detail=f"{ResourceType} with id {id} not found")

# POST /{resource}/ - 409 for conflicts
try:
    # Create resource
except IntegrityError:
    raise HTTPException(status_code=409, detail=f"{ResourceType} with this name already exists")

# PUT /{resource}/{id} - 404 for not found, 409 for conflicts  
if not existing_resource:
    raise HTTPException(status_code=404, detail=f"{ResourceType} with id {id} not found")
# Then same conflict handling as POST

# DELETE /{resource}/{id} - 404 for not found
if not resource:
    raise HTTPException(status_code=404, detail=f"{ResourceType} with id {id} not found")
```

### Ollama Router Patterns

```python
# Connection failures → 503
except (httpx.RequestError, httpx.ConnectError):
    raise HTTPException(status_code=503, detail="Failed to connect to upstream service")

# Bad upstream responses → 502  
if response.status_code >= 400:
    raise HTTPException(status_code=502, detail="Upstream service returned an error")

# Validation failures → 422
except ValueError as e:
    raise HTTPException(status_code=422, detail=f"Response validation failed: {str(e)}")
```

## Exception Hierarchy (FROZEN)

### When to Use Each Exception Type

1. **`HTTPException`** - Explicit HTTP errors with known status codes
   - Use for: 404, 409, 502, 503 scenarios  
   - Pattern: `raise HTTPException(status_code=X, detail="message")`

2. **`raise Exception`** - Unexpected errors that should become 500
   - Use for: Programming errors, unexpected system failures
   - Pattern: Let global exception handler catch and convert to 500

3. **Custom Exception Classes** - Domain-specific errors
   - Future custom exceptions should inherit from `Exception` or `HTTPException`

4. **Do NOT use**:
   - Bare `raise` without exception
   - Non-standard exception types without handlers
   - Status codes outside the canonical mapping

## Test Coverage Status (FROZEN)

**✅ Complete Coverage - 442/442 Tests Passing**

### Test Categories
- **Resource Not Found (404)**: coverage across all routers
- **Validation Errors (422)**: ensures invalid payloads are rejected
- **Resource Conflicts (409)**: tests for duplicate resources
- **Ollama Status Codes**: upstream service error handling
- **Database Errors**: integrity and SQLAlchemy exceptions
- **Authentication**: placeholder tests for future auth middleware
- **Internal Server Errors (500)**: unexpected error paths

### Router Coverage
All routers have comprehensive status code testing:
- Controls, Modulations, Grid Controls, Haptics
- Shaders, Shader Libraries, Tones, Synesthetic Assets
- Ollama

## OpenAPI Schema Compliance

**Status**: ✅ VALIDATED - ErrorResponse schema correctly reflected in OpenAPI spec

The FastAPI automatic OpenAPI generation correctly includes:
- HTTPException responses with ErrorResponse schema
- Validation error responses (422) with ErrorResponse schema  
- Status code documentation for all major error cases

**Note**: Custom 502/503 responses in Ollama router are documented in OpenAPI via FastAPI's exception handling.

## Current Gaps & TODOs (DOCUMENTED)

### Known Limitations
1. **Authentication**: Auth middleware not yet implemented
   - Tests currently allow 200/404 responses where 401/403 expected
   - Future auth implementation should use HTTPException(401/403)

2. **Error Logging**: Basic logging in place, needs enhancement
   - Request ID correlation works but needs structured logging
   - Future: Add request/response body logging for errors

3. **Shader Libraries**: Validation before existence check
   - PUT /shader_libs/{id} returns 422 before checking if resource exists
   - This is acceptable but inconsistent with other routers

### Future Enhancement Entry Points

1. **MCP/Telemetry Integration**
   - Hook into global exception handler for telemetry
   - Add structured error metrics collection
   - Entry point: `app/error_handlers.py` exception handlers

2. **ExceptionGroup Support** (Python 3.11+)
   - For handling multiple concurrent errors
   - Consider for batch operations in future

3. **Error Code Standardization**
   - Add machine-readable error codes to ErrorResponse
   - Create error code registry/enum

4. **Enhanced Validation**
   - Custom validation decorators for business logic
   - More granular 422 error details

## Development Guidelines (LOCKED)

### For Future Contributors

1. **Status Code Selection**
   - Use the canonical mapping table above
   - Do NOT introduce new status codes without architecture review
   - When in doubt, use 500 for server errors, 422 for client errors

2. **Error Message Format**
   - Always human-readable in `detail` field
   - Include resource type and identifier when possible
   - Use lowercase for consistency: "Resource with id X not found"

3. **Exception Handling Pattern**
   ```python
   # CORRECT - Explicit HTTPException
   raise HTTPException(status_code=404, detail="Control with id 123 not found")
   
   # CORRECT - Let global handler catch unexpected errors  
   result = some_risky_operation()  # May raise Exception → becomes 500
   
   # INCORRECT - Non-standard status codes
   raise HTTPException(status_code=418, detail="I'm a teapot")
   ```

4. **Testing Requirements**
   - Every new router MUST include status code tests
   - Follow the patterns in `tests/routers/test_status_codes.py`
   - Test both success and error paths

5. **Schema Changes**
   - ErrorResponse schema is FROZEN - do not modify
   - Extensions must be additive and optional
   - Maintain request_id correlation

## Architecture Freeze Declaration

**EFFECTIVE DATE**: June 4, 2025  
**FREEZE SCOPE**: All error handling patterns, status code mappings, and schemas documented above

### What is Frozen
- ✅ Status code mappings (404, 409, 422, 500, 502, 503)
- ✅ ErrorResponse schema structure  
- ✅ Global exception handler patterns
- ✅ Router error handling patterns
- ✅ Request ID correlation system

### What Can Still Change
- ⚠️ Error message text (should remain human-readable)
- ⚠️ Additional optional fields in ErrorResponse (additive only)
- ⚠️ New custom exception types (with proper handlers)
- ⚠️ Enhanced logging/telemetry (non-breaking changes)

### Change Process for Frozen Elements
Any modifications to frozen elements require:
1. Architecture review and approval
2. Backward compatibility analysis  
3. Full test suite validation
4. Documentation update
5. Version bump consideration

---

**End of M1.0 Error Handling Architecture Documentation**

This document serves as the canonical reference for error handling in the SDFK Backend. All current and future development must adhere to these established patterns to ensure system stability and consistency.
