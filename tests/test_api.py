import pytest
from fastapi.testclient import TestClient
from veroplc.main import app

client = TestClient(app)

def test_api_health():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"

def test_api_benchmarks_list():
    resp = client.get("/api/benchmarks")
    assert resp.status_code == 200
    assert len(resp.json()) >= 3

def test_api_verify_endpoint():
    payload = {
        "code": """
        PROGRAM MicroTest
        VAR_INPUT
            In1 : BOOL;
        END_VAR
        VAR_OUTPUT
            Out1 : BOOL;
        END_VAR
        Out1 := In1;
        END_PROGRAM
        """,
        "code_format": "ST",
        "k_max": 3,
        "invariants": [{"name": "Equiv", "expression": "Out1 = In1"}]
    }
    resp = client.post("/api/verify", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "UNSAT"
