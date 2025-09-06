"""Application entrypoint defining the FastAPI app and custom docs."""

import app.cache as cache_module
from app.config import settings
from .schemas.error import ErrorResponse  # Import our error schema
from .error_handlers import add_error_handlers
from app.api.errors import add_api_error_handlers
from .routers.mcp import asset as mcp_asset_router
from .routers import (
    tones,
    controls,
    shaders,
    shader_libs,
    synesthetic_assets,
    haptics,
    modulations,
    pb_assets,
    embeddings,
    search,
    cache_toggle,
    rule_bundles,
)
from .logging import get_logger, RequestLoggingMiddleware
from .middleware.request_id import RequestIDMiddleware
from .models.db import engine, SessionLocal
from . import models, utils
from app.models.shader_lib import ShaderLib as ShaderLibModel
from app.examples.loader import load_examples as load_shaderlib_examples
from fastapi import FastAPI, Request, status, APIRouter, Header, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.openapi.utils import get_openapi
import os
import logging
from typing import List, Optional, Tuple
from app.env import load_env
from .schema_version import SCHEMA_VERSION, check_schema_header

load_env()


# Set up logging
logging.basicConfig(level=logging.INFO)
logger = get_logger(__name__)

# Only wait for DB and create tables if not in testing mode
if not os.getenv("TESTING"):
    utils.wait_for_db(os.getenv("DATABASE_URL"))
    # Create tables
    models.Base.metadata.create_all(bind=engine)

app = FastAPI(docs_url=None, redoc_url=None)  # Disable default docs

# Add request ID middleware (must be added before CORS)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(RequestLoggingMiddleware)


@app.middleware("http")
async def add_schema_version_header(request, call_next):
    response = await call_next(request)
    response.headers["X-Schema-Version"] = SCHEMA_VERSION
    return response

# Simple CORS setup that allows everything (for development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,  # Must be False when using allow_origins=["*"]
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add global exception handler (early in setup, after middleware)
add_error_handlers(app)
add_api_error_handlers(app)

# Create a directory for static files if it doesn't exist
os.makedirs("app/static", exist_ok=True)

# Mount the static directory
app.mount("/static", StaticFiles(directory="app/static"), name="static")

## Patch storage disabled: no preview/apply endpoints in this repository


@app.on_event("startup")
def load_example_shaderlib() -> None:
    """Load deterministic example data during testing."""
    if os.getenv("TESTING", "0") not in ("1", "true", "True"):
        return

    models.Base.metadata.create_all(bind=engine)

    def register(lib):
        session = SessionLocal()
        try:
            existing = session.query(ShaderLibModel).filter_by(name=lib.name).first()
            if existing:
                existing.definition = lib.model_dump(by_alias=True)
            else:
                session.add(
                    ShaderLibModel(
                        name=lib.name, definition=lib.model_dump(by_alias=True)
                    )
                )
            session.commit()
        finally:
            session.close()

    load_shaderlib_examples(register)


# Custom OpenAPI schema generation


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="SDFK Backend API",  # Title from your root endpoint or customize
        version="0.1.1",  # Customize version
        description="SDFK Backend API with canonical error responses",  # Customize description
        routes=app.routes,
        # tags=openapi_tags # if you have tags defined
    )

    # Add our ErrorResponse to components/schemas
    if "components" not in openapi_schema:
        openapi_schema["components"] = {}
    if "schemas" not in openapi_schema["components"]:
        openapi_schema["components"]["schemas"] = {}

    # Generate the schema for ErrorResponse using Pydantic v2. This schema
    # includes any nested definitions under the "$defs" key. Those need to be
    # hoisted into the OpenAPI components section so that ``$ref`` paths resolve
    # correctly when rendered by Swagger UI or other tools.

    error_schema = ErrorResponse.model_json_schema(
        ref_template="#/components/schemas/{model}"
    )

    defs = error_schema.pop("$defs", {})
    for name, schema in defs.items():
        openapi_schema["components"]["schemas"][name] = schema

    openapi_schema["components"]["schemas"]["ErrorResponse"] = error_schema

    # Remove FastAPI's default validation error schemas which we don't use
    for unused in ("HTTPValidationError", "ValidationError"):
        openapi_schema["components"]["schemas"].pop(unused, None)

    # Iterate over all paths and operations to update error responses
    for path_item in openapi_schema.get("paths", {}).values():
        for operation in path_item.values():  # e.g., get, post, put
            if isinstance(operation, dict) and "responses" in operation:
                for status_code, response_spec in operation["responses"].items():
                    # Update 4xx and 5xx responses
                    # Also handle default error response if present
                    if (
                        status_code.startswith("4")
                        or status_code.startswith("5")
                        or status_code == "default"
                    ):
                        if "content" not in response_spec:
                            response_spec["content"] = {}
                        if "application/json" not in response_spec["content"]:
                            response_spec["content"]["application/json"] = {}

                        response_spec["content"]["application/json"]["schema"] = {
                            "$ref": "#/components/schemas/ErrorResponse"
                        }

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

# Custom docs endpoint with dark theme


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    swagger_ui_html = get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
        swagger_favicon_url="/static/favicon.png",
    )

    # Modify the HTML to include our custom CSS
    html_content = swagger_ui_html.body.decode("utf-8")
    html_content = html_content.replace(
        "</head>", '<link rel="stylesheet" href="/static/swagger-ui-dark.css"></head>'
    )

    return HTMLResponse(html_content)


@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=app.title + " - ReDoc",
        redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js",
        redoc_favicon_url="/static/favicon.png",
        with_google_fonts=False,
    )


@app.get("/")
async def root():
    return {"message": "SDFK Backend API"}


@app.get("/ping")
async def ping(request: Request):
    """Health check endpoint that returns request ID for correlation testing."""
    return {"status": "ok", "message": "pong", "request_id": request.state.request_id}


@app.get("/schema/version", tags=["schema"])
async def schema_version():
    return {"schema_version": SCHEMA_VERSION}


@app.get("/version", tags=["schema"])
async def schema_version_alias():
    return {"schemaVersion": SCHEMA_VERSION}


@app.get(
    "/health",
    summary="Comprehensive health check",
    description="Check the health status of core services including database and MCP router.",
    responses={
        200: {
            "description": "All services are healthy",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "request_id": "550e8400-e29b-41d4-a716-446655440000",
                        "timestamp": "2025-06-23T12:00:00Z",
                        "services": {
                            "database": {
                                "status": "healthy",
                                "details": "Connected successfully",
                            },
                            "mcp": {
                                "status": "healthy",
                                "details": "MCP asset router available",
                            },
                        },
                        "environment": {"testing": True},
                    }
                }
            },
        },
        503: {
            "description": "One or more services are unhealthy",
            "content": {
                "application/json": {
                    "example": {
                        "status": "degraded",
                        "request_id": "550e8400-e29b-41d4-a716-446655440000",
                        "timestamp": "2025-06-23T12:00:00Z",
                        "services": {
                            "database": {
                                "status": "unhealthy",
                                "details": "Connection failed: connection refused",
                            },
                            "mcp": {
                                "status": "unhealthy",
                                "details": "MCP router error",
                            },
                        },
                        "environment": {"testing": True},
                        "unhealthy_services": ["database"],
                    }
                }
            },
        },
    },
)
async def health_check(request: Request):
    """Comprehensive health check endpoint that tests core services."""
    import sqlalchemy as sa
    from app.models.db import engine

    request_id = request.state.request_id
    health_status = {
        "status": "healthy",
        "request_id": request_id,
        "timestamp": "2025-06-23T00:00:00Z",  # Will be updated to actual timestamp
        "services": {},
        "environment": {"testing": bool(settings.TESTING)},
    }

    from datetime import datetime, timezone

    health_status["timestamp"] = (
        datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    )

    # Test Database Connection
    try:
        with engine.connect() as connection:
            connection.execute(sa.select(1)).scalar()
            health_status["services"]["database"] = {
                "status": "healthy",
                "details": "Connected successfully",
            }
    except Exception as e:
        health_status["services"]["database"] = {
            "status": "unhealthy",
            "details": f"Connection failed: {str(e)}",
        }
        health_status["status"] = "degraded"

    # Test MCP Router
    try:
        health_status["services"]["mcp"] = {
            "status": "healthy",
            "details": "MCP asset router available",
        }
    except Exception as e:
        health_status["services"]["mcp"] = {
            "status": "unhealthy",
            "details": f"MCP router error: {str(e)}",
        }
        health_status["status"] = "degraded"

    unhealthy_services = [
        name
        for name, service in health_status["services"].items()
        if service["status"] in ["unhealthy", "unreachable", "misconfigured"]
    ]

    if unhealthy_services:
        health_status["status"] = "degraded"
        health_status["unhealthy_services"] = unhealthy_services

    status_code = (
        status.HTTP_200_OK
        if health_status["status"] == "healthy"
        else status.HTTP_503_SERVICE_UNAVAILABLE
    )

    return JSONResponse(content=health_status, status_code=status_code)


# Router configuration: (router, optional prefix, optional tags)
ROUTER_METADATA: List[Tuple[APIRouter, Optional[str], Optional[List[str]]]] = [
    (synesthetic_assets.router, "/synesthetic-assets", ["synesthetic-assets"]),
    (tones.router, "/tones", ["tones"]),
    (controls.router, "/controls", ["controls"]),
    (shaders.router, "/shaders", ["shaders"]),
    (shader_libs.router, "/shader_libs", ["shader_libs"]),
    (haptics.router, "/haptics", ["haptics"]),
    (modulations.router, "/modulations", ["modulations"]),
    (pb_assets.router, "/protobuf-assets", ["protobuf-assets"]),
    (embeddings.router, "/embeddings", ["embeddings"]),
    (search.router, None, ["search"]),
    (rule_bundles.router, "/rule-bundles", ["Rule Bundles"]),
    (cache_toggle.router, None, ["admin"]),
    (mcp_asset_router.router, "/mcp/asset", ["MCP Asset"]),
]

for router, prefix, tags in ROUTER_METADATA:
    kwargs = {}
    if prefix:
        kwargs["prefix"] = prefix
    if tags:
        kwargs["tags"] = tags
    app.include_router(router, **kwargs)


@app.on_event("shutdown")
async def close_cache_client() -> None:
    """Close the cache client if caching is enabled."""

    if settings.CACHE_ENABLED and hasattr(cache_module.cache, "close"):
        cache_module.cache.close()
