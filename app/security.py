from fastapi import Header, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from os import getenv

from app.env import load_env

load_env()

security = HTTPBearer(auto_error=False)  # Make authentication optional
JWT_SECRET = getenv("JWT_SECRET")

# Stubbed verify_jwt for development: always returns a fixed payload.


def verify_jwt(credentials: HTTPAuthorizationCredentials = Security(security)) -> dict:
    """Temporarily bypassed for development"""
    return {"sub": "development", "disabled_auth": True}


SECRET_KEY = "your-secret-key"  # Replace with secure key in production
ALGORITHM = "HS256"

REQUIRE_AUTH = getenv("REQUIRE_AUTH", "0") in ("1", "true", "True")


def require_auth(authorization: str | None = Header(default=None)) -> None:
    """Enforce presence of a bearer token when auth is required."""
    if not REQUIRE_AUTH:
        return
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing auth token")
