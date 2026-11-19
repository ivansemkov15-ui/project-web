import psycopg
from flask import Blueprint, g, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash

import db
from auth import create_token, require_auth


auth_api = Blueprint("auth_api", __name__)


@auth_api.post("/api/auth/register")
def register():
    data = request.get_json(silent=True) or {}
    if not isinstance(data, dict):
        return jsonify({"error": "JSON object is required"}), 400
    user_name = data.get("user_name")
    password = data.get("password")

    if not isinstance(user_name, str) or not 3 <= len(user_name) <= 50:
        return jsonify({"error": "user_name must contain 3-50 characters"}), 400
    if not all(char.isalnum() or char == "_" for char in user_name):
        return jsonify({"error": "user_name may contain letters, digits and _"}), 400
    if not isinstance(password, str) or len(password) < 8:
        return jsonify({"error": "password must contain at least 8 characters"}), 400

    try:
        user = db.create_user(user_name, generate_password_hash(password))
    except psycopg.errors.UniqueViolation:
        return jsonify({"error": "This user_name is already taken"}), 409

    return jsonify(user), 201


@auth_api.post("/api/auth/login")
def login():
    data = request.get_json(silent=True) or {}
    if not isinstance(data, dict):
        return jsonify({"error": "JSON object is required"}), 400
    if not isinstance(data.get("user_name"), str) or not isinstance(data.get("password"), str):
        return jsonify({"error": "user_name and password are required"}), 400
    user = db.get_user_by_name(data["user_name"])
    if user is None or not check_password_hash(user["password_hash"], data.get("password") or ""):
        return jsonify({"error": "Incorrect user_name or password"}), 401

    return jsonify({
        "access_token": create_token(user["id"]),
        "refresh_token": create_token(user["id"], "refresh"),
        "token_type": "Bearer",
    })


@auth_api.post("/api/auth/refresh")
@require_auth("refresh")
def refresh():
    if db.get_user_by_id(g.user_id) is None:
        return jsonify({"error": "User not found"}), 401
    return jsonify({"access_token": create_token(g.user_id), "token_type": "Bearer"})
