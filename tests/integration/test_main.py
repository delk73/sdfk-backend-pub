import os
from fastapi.testclient import TestClient
from app.main import app
from app.cache import cache

os.environ.setdefault("OLLAMA_API_URL", "http://localhost:11434")

client = TestClient(app)

# Add a dummy clear to cache if missing
if not hasattr(cache, "clear"):
    cache.clear = lambda: None


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "SDFK Backend API"}
