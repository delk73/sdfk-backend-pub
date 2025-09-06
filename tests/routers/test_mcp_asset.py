from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_ping_asset():
    """Test the MCP asset router ping endpoint."""
    response = client.get("/mcp/asset/ping")
    assert response.status_code == 200
    assert response.json() == {"status": "MCP asset router live"}
