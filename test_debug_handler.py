#!/usr/bin/env python3

from app.error_handlers import global_exception_handler
from fastapi.testclient import TestClient
from fastapi import FastAPI
import sys
import os

sys.path.insert(0, os.path.abspath("."))


# Create a minimal test app
app = FastAPI()
app.add_exception_handler(Exception, global_exception_handler)


@app.get("/test")
def test_route():
    raise RuntimeError("Test error")


# Test the app
client = TestClient(app)
response = client.get("/test")

print(f"Status Code: {response.status_code}")
print(f"Response Text: {response.text}")
print(f"Headers: {dict(response.headers)}")

try:
    json_data = response.json()
    print(f"JSON Response: {json_data}")
except Exception as e:
    print(f"Failed to parse JSON: {e}")
