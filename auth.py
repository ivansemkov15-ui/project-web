import os
from datetime import datetime, timedelta, timezone
from functools import wraps

import jwt
from flask import g, jsonify, request


def get_jwt_secret():
    secret = os.getenv("JWT_SECRET", "")
    if len(secret.encode("utf-8")) < 32 or secret == "replace-with-a-long-random-secret-before-sharing":
        raise RuntimeError("JWT_SECRET must be a random secret of at least 32 bytes")
    return secret


def create_token(user_id, token_type="access"):
    minutes = 30 if token_type == "access" else 10080
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "type": token_type,
        "iat": now,
        "exp": now + timedelta(minutes=minutes),
    }
    secret = get_jwt_secret()
    return jwt.encode(payload, secret, algorithm="HS256")


def require_auth(token_type="access"):
    def decorator(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            header = request.headers.get("Authorization", "")
            if not header.startswith("Bearer "):
                return jsonify({"error": "Authorization token is required"}), 401

            token = header.removeprefix("Bearer ").strip()
            secret = get_jwt_secret()
            try:
                payload = jwt.decode(
                    token,
                    secret,
                    algorithms=["HS256"],
                    options={"require": ["sub", "type", "iat", "exp"]},
                )
                if payload["type"] != token_type:
                    return jsonify({"error": "Wrong token type"}), 401
                g.user_id = int(payload["sub"])
            except (jwt.InvalidTokenError, ValueError, TypeError):
                return jsonify({"error": "Invalid or expired token"}), 401

            return function(*args, **kwargs)

        return wrapper

    return decorator
