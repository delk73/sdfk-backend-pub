# Error Handling & Structured Logging

This document describes the structured logging and error handling system implemented in the SDFK Backend API.

## Overview

The system provides:
- **Request ID correlation** - Every HTTP request gets a unique UUID that appears in all log messages during that request
- **Structured logging** - Consistent log format with request context
- **Comprehensive exception logging** - All errors include full stack traces via `exc_info=True`
- **Centralized logger management** - Single point of configuration for all loggers

## Usage

### Basic Logging

```python
from app.logging import get_logger

logger = get_logger(__name__)

# Standard logging
logger.info("Processing user request")
logger.warning("Deprecated API endpoint used")

# Error logging with stack trace
try:
    risky_operation()
except ValueError:
    logger.error("Bad payload", exc_info=True)
    raise HTTPException(422, "Bad payload")
```

### Request ID Correlation

Every HTTP request automatically gets:
- A unique UUID4 request ID
- `X-Request-ID` header in the response
- Request ID included in all log messages during that request

```python
# Example log output:
# 2024-01-15 10:30:45,123 - ERROR - app.routers.tones - 550e8400-e29b-41d4-a716-446655440000 - Failed to create tone: Invalid synth type
```

### Error Handling Best Practices

1. **Always use `exc_info=True` for error logs**:
   ```python
   try:
       dangerous_operation()
   except Exception as e:
       logger.error(f"Operation failed: {str(e)}", exc_info=True)
       raise HTTPException(500, "Internal server error")
   ```

2. **Include context in error messages**:
   ```python
   logger.error(f"Failed to process file {filename}: {str(e)}", exc_info=True)
   ```

3. **Use appropriate log levels**:
   - `logger.error()` - Errors that need investigation
   - `logger.warning()` - Potential issues that don't break functionality
   - `logger.info()` - Normal operation information
   - `logger.debug()` - Detailed debugging information

## Architecture

### Request ID Middleware

The `RequestIDMiddleware` automatically:
1. Generates a UUID4 for each request
2. Stores it in `request.state.request_id`
3. Sets it in a context variable for logging
4. Adds `X-Request-ID` header to responses
5. Cleans up context after request completion

### Logger Adapter

The `RequestIDLoggerAdapter` automatically injects the current request ID into all log records:

```python
class RequestIDLoggerAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        extra = kwargs.get('extra', {})
        extra['request_id'] = get_current_request_id()
        kwargs['extra'] = extra
        return msg, kwargs
```

### Log Format

Standard format: `%(asctime)s - %(levelname)s - %(name)s - %(request_id)s - %(message)s`

Example:
```
2024-01-15 10:30:45,123 - INFO - app.main - 550e8400-e29b-41d4-a716-446655440000 - Starting request processing
2024-01-15 10:30:45,124 - ERROR - app.routers.tones - 550e8400-e29b-41d4-a716-446655440000 - Database connection failed
```

## Testing

### Health Check Endpoint

The `/ping` endpoint returns request ID for testing correlation:

```bash
curl -X GET http://localhost:8000/ping
```

Response:
```json
{
  "status": "ok",
  "message": "pong",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Log Verification

Tests verify that:
- All `logger.error()` calls include `exc_info=True`
- Request IDs appear in response headers
- Request IDs are properly correlated in logs

## Migration Guide

### Converting Existing Code

1. **Replace logger imports**:
   ```python
   # Old
   import logging
   logger = logging.getLogger(__name__)
   
   # New
   from app.logging import get_logger
   logger = get_logger(__name__)
   ```

2. **Add exc_info=True to error logs**:
   ```python
   # Old
   logger.error("Something went wrong")
   
   # New
   logger.error("Something went wrong", exc_info=True)
   ```

3. **Remove print statements**:
   ```python
   # Old
   print("Debug info")
   
   # New
   logger.info("Debug info")
   ```

## Troubleshooting

### Common Issues

1. **Missing request ID in logs**: Ensure the `RequestIDMiddleware` is added to the FastAPI app before other middleware.

2. **No stack traces in error logs**: Verify all `logger.error()` calls include `exc_info=True`.

3. **Context variable errors**: The request ID context is automatically managed by the middleware. Manual context manipulation is not recommended.

### Debugging

To debug logging issues:

1. Check middleware order in `app/main.py`
2. Verify logger configuration in `app/logging.py`
3. Use the `/ping` endpoint to test request ID generation
4. Check log output format and content

## Global 500 Exception Handler

The system includes a global exception handler that catches all unhandled exceptions and returns a uniform, safe 500 response while preserving detailed logging for debugging.

### Flow Diagram

```
Request → Middleware → Route Handler
                           ↓
                    Exception Raised
                           ↓
              Global Exception Handler
                           ↓
                    Log with exc_info=True
                           ↓
                Return Uniform 500 Response
                {
                  "detail": "Internal server error",
                  "request_id": "uuid"
                }
```

### Implementation

The global exception handler:
1. **Logs the full exception** with `exc_info=True` for debugging
2. **Returns a uniform response** that doesn't leak internal details
3. **Includes request ID** for correlation between logs and responses
4. **Sets X-Request-ID header** for client-side correlation

```python
async def global_exception_handler(request: Request, exc: Exception):
    logger = get_logger(__name__)
    logger.error("Unhandled exception", exc_info=True)
    
    rid = get_current_request_id()
    if rid == "no-request-id":
        rid = str(uuid4())
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error", "request_id": rid},
        headers={"X-Request-ID": rid},
    )
```

### Security Benefits

- **No information leakage**: Internal error details are never exposed to clients
- **Consistent responses**: All unhandled exceptions return the same format
- **Full logging**: Complete stack traces are preserved in logs for debugging
- **Request correlation**: Every error can be traced back to specific requests

## Performance Considerations

- Request ID generation uses `uuid.uuid4()` which is fast and cryptographically secure
- Context variables have minimal overhead
- Log formatting is done lazily by the logging system
- No significant performance impact on request processing 
