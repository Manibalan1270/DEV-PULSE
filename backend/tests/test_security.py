import uuid

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

import auth
from main import app

client = TestClient(app)  # no "with": startup (DB table creation) is not run
ORG = str(uuid.uuid4())
CLAIMS = {"sub": str(uuid.uuid4()), "role": "ceo", "org_id": ORG, "display_name": "Test"}


def test_refresh_token_cannot_be_used_as_access_token():
    refresh = auth.create_refresh_token(CLAIMS)
    with pytest.raises(HTTPException):
        auth.verify_token(refresh)  # expects an access token
    assert auth.verify_token(refresh, expected_type="refresh")["sub"] == CLAIMS["sub"]


def test_access_token_cannot_be_used_to_refresh():
    access = auth.create_access_token(CLAIMS)
    with pytest.raises(HTTPException):
        auth.verify_token(access, expected_type="refresh")


def test_tokens_from_before_this_fix_are_rejected():
    from jose import jwt
    from datetime import datetime, timedelta, timezone

    old_style = jwt.encode(
        {**CLAIMS, "exp": datetime.now(timezone.utc) + timedelta(days=7)},
        auth.JWT_SECRET_KEY,
        algorithm=auth.JWT_ALGORITHM,
    )
    with pytest.raises(HTTPException):
        auth.verify_token(old_style)


def test_register_requires_sign_in():
    r = client.post(
        "/auth/register",
        json={"email": "x@y.test", "password": "password123", "role": "ceo", "org_id": ORG},
    )
    assert r.status_code == 401


@pytest.mark.parametrize("query", ["", "?token=garbage"])
def test_websocket_rejects_missing_or_bad_token(query):
    with pytest.raises(WebSocketDisconnect) as exc:
        with client.websocket_connect(f"/ws/{ORG}{query}") as ws:
            ws.receive_text()
    assert exc.value.code == 1008


def test_websocket_rejects_token_for_another_org():
    token = auth.create_access_token({**CLAIMS, "org_id": str(uuid.uuid4())})
    with pytest.raises(WebSocketDisconnect) as exc:
        with client.websocket_connect(f"/ws/{ORG}?token={token}") as ws:
            ws.receive_text()
    assert exc.value.code == 1008


def test_websocket_rejects_developer_role():
    token = auth.create_access_token({**CLAIMS, "role": "developer"})
    with pytest.raises(WebSocketDisconnect) as exc:
        with client.websocket_connect(f"/ws/{ORG}?token={token}") as ws:
            ws.receive_text()
    assert exc.value.code == 1008


def test_password_hashing_round_trip():
    hashed = auth.hash_password("correct horse battery")
    assert auth.verify_password("correct horse battery", hashed)
    assert not auth.verify_password("wrong", hashed)


def test_health():
    assert client.get("/health").status_code == 200
