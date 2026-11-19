import hashlib
import os

import requests
from flask import Blueprint, g, jsonify

import db
from auth import require_auth


stats_api = Blueprint("stats_api", __name__)


def supporting_url():
    return os.getenv("SUPPORTING_URL", "http://localhost:8001").rstrip("/")


@stats_api.get("/api/stats")
@require_auth()
def stats():
    return jsonify(db.get_statistics(g.user_id))


@stats_api.get("/api/analytics")
@require_auth()
def analytics():
    data = db.get_statistics(g.user_id)
    try:
        response = requests.post(
            supporting_url() + "/api/summary", json=data, timeout=3
        )
        response.raise_for_status()
        return jsonify({"source": "supporting", "data": response.json()})
    except (requests.RequestException, ValueError):
        return jsonify({"source": "fallback", "data": {**data, "groups_count": len(data["groups"])}})


@stats_api.get("/api/hash/<value>")
def hash_string(value):
    try:
        response = requests.get(
            supporting_url() + "/api/hash/" + requests.utils.quote(value, safe=""),
            timeout=3,
        )
        response.raise_for_status()
        return jsonify(response.json())
    except (requests.RequestException, ValueError):
        result = hashlib.sha256(value.encode("utf-8")).hexdigest()
        return jsonify({"request": value, "result": result})
