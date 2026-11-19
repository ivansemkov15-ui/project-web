import hashlib

import jwt
import pytest
from fastapi.testclient import TestClient

import db
from app import create_app
from auth import create_token
from supporting_api import app as supporting_app


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


def test_public_endpoints(client):
    assert client.get("/health").json["status"] == "ok"
    assert client.get("/api/about").json["name"] == "Телефонный справочник"


def test_unauthorized_contacts(client):
    response = client.get("/api/contacts")
    assert response.status_code == 401


def test_invalid_json(client):
    response = client.post("/api/auth/register", json=[])
    assert response.status_code == 400

    token = create_token(1)
    response = client.post(
        "/api/groups",
        json=[],
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 400


def test_registration(client, monkeypatch):
    monkeypatch.setattr(db, "create_user", lambda name, password_hash: {"id": 1, "user_name": name})
    response = client.post(
        "/api/auth/register",
        json={"user_name": "student", "password": "password123"},
    )
    assert response.status_code == 201
    assert response.json["user_name"] == "student"


def test_login_and_refresh(client, monkeypatch):
    from werkzeug.security import generate_password_hash

    user = {"id": 1, "user_name": "student", "password_hash": generate_password_hash("password123")}
    monkeypatch.setattr(db, "get_user_by_name", lambda name: user if name == "student" else None)
    monkeypatch.setattr(db, "get_user_by_id", lambda user_id: {"id": 1, "user_name": "student"})

    response = client.post("/api/auth/login", json={"user_name": "student", "password": "password123"})
    assert response.status_code == 200
    access = response.json["access_token"]
    refresh = response.json["refresh_token"]
    assert access != refresh

    response = client.post("/api/auth/refresh", headers={"Authorization": f"Bearer {refresh}"})
    assert response.status_code == 200
    assert response.json["access_token"]

    response = client.post("/api/auth/refresh", headers={"Authorization": f"Bearer {access}"})
    assert response.status_code == 401


def test_contacts_list(client, monkeypatch):
    monkeypatch.setattr(db, "list_contacts", lambda *args: ([{"id": 5, "name": "Anna"}], 1))
    token = create_token(1)
    response = client.get("/api/contacts?page=1&per_page=10", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json["items"][0]["name"] == "Anna"
    assert response.json["pages"] == 1


def test_contact_validation(client):
    token = create_token(1)
    response = client.post("/api/contacts", json={"name": "", "phone": "123"}, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 400


def test_profile_is_private(client, monkeypatch):
    monkeypatch.setattr(db, "get_user_by_id", lambda user_id: {"id": 1, "user_name": "student"})
    token = create_token(1)
    response = client.get("/someone_else", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403


def test_supporting_service():
    client = TestClient(supporting_app)
    assert client.get("/health").status_code == 200
    response = client.get("/api/hash/hello")
    assert response.json() == {
        "request": "hello",
        "result": hashlib.sha256(b"hello").hexdigest(),
    }
    response = client.get("/api/hash/a%2Fb")
    assert response.json()["request"] == "a/b"

    response = client.post("/api/summary", json={
        "total_contacts": 2,
        "groups": [{"name": "Friends", "count": 2}],
        "without_group": 0,
    })
    assert response.json()["groups_count"] == 1


def test_jwt_contains_user_id():
    token = create_token(15)
    payload = jwt.decode(token, "development-secret-change-me", algorithms=["HS256"])
    assert payload["sub"] == "15"
