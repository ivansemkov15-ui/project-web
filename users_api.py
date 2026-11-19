from flask import Blueprint, g, jsonify

import db
from auth import require_auth


users_api = Blueprint("users_api", __name__)


@users_api.get("/api/users/me")
@require_auth()
def current_user():
    user = db.get_user_by_id(g.user_id)
    if user is None:
        return jsonify({"error": "User not found"}), 404
    return jsonify(user)


@users_api.get("/<username>")
@require_auth()
def user_profile(username):
    user = db.get_user_by_id(g.user_id)
    if user is None:
        return jsonify({"error": "User not found"}), 404
    if user["user_name"] != username:
        return jsonify({"error": "Access denied"}), 403
    return jsonify(user)
