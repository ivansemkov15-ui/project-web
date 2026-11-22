import psycopg
import pytest

import db
from app import create_app
from auth import create_token


@pytest.fixture(autouse=True)
def jwt_secret(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", "unit-test-secret-0123456789abcdef0123456789abcdef")


@pytest.fixture
def client():
    application = create_app()
    application.config["TESTING"] = True
    return application.test_client()


@pytest.fixture
def headers():
    return {"Authorization": f"Bearer {create_token(1)}"}


@pytest.mark.parametrize("path", [
    "/api/contacts?page=999999999999999999999999999",
    "/api/contacts?per_page=101",
    "/api/contacts?group_id=2147483648",
    "/api/contacts?search=" + ("x" * 101),
])
def test_invalid_list_query_returns_400(client, headers, path):
    response = client.get(path, headers=headers)
    assert response.status_code == 400
    assert "error" in response.json


@pytest.mark.parametrize(("method", "path", "payload"), [
    ("GET", "/api/contacts/2147483648", None),
    ("DELETE", "/api/contacts/2147483648", None),
    ("PATCH", "/api/contacts/2147483648", {"name": "Test"}),
    ("DELETE", "/api/groups/2147483648", None),
])
def test_large_resource_id_is_not_found(client, headers, method, path, payload):
    response = client.open(path, method=method, json=payload, headers=headers)
    assert response.status_code == 404


def test_contact_group_id_overflow(client, headers):
    response = client.post(
        "/api/contacts", json={"name": "Name", "phone": "123", "group_id": 2147483648},
        headers=headers,
    )
    assert response.status_code == 400


def test_oversized_request_is_json(client):
    response = client.post(
        "/api/auth/register",
        data="x" * (16 * 1024 + 1),
        content_type="application/json",
    )
    assert response.status_code == 413
    assert response.json == {"error": "Request body is too large"}


def test_database_connection_error_is_503(client, monkeypatch, headers):
    def unavailable(user_id):
        raise psycopg.OperationalError("private details should not be returned")

    monkeypatch.setattr(db, "list_groups", unavailable)
    response = client.get("/api/groups", headers=headers)
    assert response.status_code == 503
    assert response.json == {"error": "Database is temporarily unavailable"}


def test_password_length_is_bounded(client):
    response = client.post(
        "/api/auth/register",
        json={"user_name": "student", "password": "p" * 1025},
    )
    assert response.status_code == 400
