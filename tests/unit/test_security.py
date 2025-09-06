import jwt
from app.security import verify_jwt, SECRET_KEY, ALGORITHM
from fastapi.security import HTTPAuthorizationCredentials


def test_verify_jwt_without_token():
    result = verify_jwt(None)
    assert result.get("sub") == "development"


def test_verify_jwt_with_invalid_token():
    result = verify_jwt("invalid-token")
    assert result.get("sub") == "development"


def test_verify_jwt_with_valid_token():
    payload = {"sub": "test_user"}
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    result = verify_jwt(token)
    assert result.get("sub") == "development"


def test_verify_jwt_no_credentials():
    """Test verify_jwt with no credentials (development mode)"""
    result = verify_jwt()
    assert result == {"sub": "development", "disabled_auth": True}


def test_verify_jwt_with_credentials():
    """Test verify_jwt with credentials (development mode)"""
    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer", credentials="dummy-token"
    )
    result = verify_jwt(credentials)
    assert result == {"sub": "development", "disabled_auth": True}
