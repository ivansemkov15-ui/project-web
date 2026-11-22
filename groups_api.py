import psycopg
from flask import Blueprint, g, jsonify, request

import db
from auth import require_auth


groups_api = Blueprint("groups_api", __name__)


@groups_api.get("/api/groups")
@require_auth()
def groups_list():
    return jsonify(db.list_groups(g.user_id))


@groups_api.post("/api/groups")
@require_auth()
def groups_create():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "JSON object is required"}), 400
    name = data.get("name")
    if not isinstance(name, str) or not 1 <= len(name.strip()) <= 60:
        return jsonify({"error": "name must contain 1-60 characters"}), 400

    try:
        group = db.create_group(g.user_id, name.strip())
    except psycopg.errors.UniqueViolation:
        return jsonify({"error": "This group already exists"}), 409
    return jsonify(group), 201


@groups_api.delete("/api/groups/<int:group_id>")
@require_auth()
def groups_delete(group_id):
    if group_id > 2147483647 or not db.delete_group(g.user_id, group_id):
        return jsonify({"error": "Group not found"}), 404
    return "", 204
