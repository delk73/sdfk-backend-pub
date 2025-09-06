from fastapi import FastAPI
from fastapi.testclient import TestClient
import json

from app.logging import get_logger, RequestLoggingMiddleware
from app.middleware.request_id import RequestIDMiddleware


def test_logger_includes_request_id(capsys):
    app = FastAPI()
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(RequestLoggingMiddleware)

    logger = get_logger(__name__)

    @app.get("/test")
    async def _test():
        logger.info("hello from handler")
        return {"ok": True}

    client = TestClient(app)

    client.get("/test")

    output = capsys.readouterr().out

    has_id = False
    for line in output.splitlines():
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue
        if (
            data.get("message") == "hello from handler"
            and data.get("request_id") != "no-request-id"
        ):
            has_id = True
            break

    assert has_id
