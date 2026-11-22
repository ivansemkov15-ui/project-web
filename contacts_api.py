from flask import Blueprint, g, jsonify, request
from psycopg.errors import ForeignKeyViolation

import db
from auth import require_auth


contacts_api = Blueprint("contacts_api", __name__)
CONTACT_GROUP_CONSTRAINT = "contacts_user_id_group_id_fkey"


def validate_contact(data, required=False):
    if not isinstance(data, dict):
        return None, "JSON object is required"

    changes = {}
    for field, limit in (("name", 100), ("phone", 30)):
        if required or field in data:
            value = data.get(field)
            if not isinstance(value, str) or not 1 <= len(value.strip()) <= limit:
                return None, f"{field} must contain 1-{limit} characters"
            changes[field] = value.strip()

    if "group_id" in data or required:
        group_id = data.get("group_id")
        if group_id is not None and (type(group_id) is not int or group_id < 1):
            return None, "group_id must be a positive integer or null"
        changes["group_id"] = group_id

    if not changes:
        return None, "No fields to update"
    return changes, None


def check_group(changes):
    group_id = changes.get("group_id")
    if group_id is not None and not db.group_exists(g.user_id, group_id):
        return jsonify({"error": "Group not found"}), 400
    return None


@contacts_api.get("/api/contacts")
@require_auth()
def contacts_list():
    try:
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 10))
        group_id = request.args.get("group_id")
        group_id = int(group_id) if group_id is not None else None
    except ValueError:
        return jsonify({"error": "Invalid pagination or group_id"}), 400

    if page < 1 or not 1 <= per_page <= 100 or (group_id is not None and group_id < 1):
        return jsonify({"error": "Invalid pagination or group_id"}), 400

    sort_by = request.args.get("sort_by", "name")
    order = request.args.get("order", "asc")
    if sort_by not in ("name", "phone", "created_at") or order not in ("asc", "desc"):
        return jsonify({"error": "Invalid sorting parameters"}), 400

    search = request.args.get("search", "").strip()
    rows, total = db.list_contacts(g.user_id, search, group_id, sort_by, order, page, per_page)
    return jsonify({
        "items": rows,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page,
    })


@contacts_api.post("/api/contacts")
@require_auth()
def contacts_create():
    changes, error = validate_contact(request.get_json(silent=True), required=True)
    if error:
        return jsonify({"error": error}), 400
    group_error = check_group(changes)
    if group_error:
        return group_error

    try:
        contact = db.create_contact(g.user_id, changes["name"], changes["phone"], changes["group_id"])
    except ForeignKeyViolation as error:
        if error.diag.constraint_name != CONTACT_GROUP_CONSTRAINT:
            raise
        return jsonify({"error": "Group not found"}), 400
    return jsonify(db.get_contact(g.user_id, contact["id"])), 201


@contacts_api.get("/api/contacts/<int:contact_id>")
@require_auth()
def contacts_get(contact_id):
    contact = db.get_contact(g.user_id, contact_id)
    if contact is None:
        return jsonify({"error": "Contact not found"}), 404
    return jsonify(contact)


@contacts_api.route("/api/contacts/<int:contact_id>", methods=["PUT", "PATCH"])
@require_auth()
def contacts_update(contact_id):
    changes, error = validate_contact(request.get_json(silent=True))
    if error:
        return jsonify({"error": error}), 400
    group_error = check_group(changes)
    if group_error:
        return group_error

    try:
        updated = db.update_contact(g.user_id, contact_id, changes)
    except ForeignKeyViolation as error:
        if error.diag.constraint_name != CONTACT_GROUP_CONSTRAINT:
            raise
        return jsonify({"error": "Group not found"}), 400
    if updated is None:
        return jsonify({"error": "Contact not found"}), 404
    return jsonify(db.get_contact(g.user_id, contact_id))


@contacts_api.delete("/api/contacts/<int:contact_id>")
@require_auth()
def contacts_delete(contact_id):
    if not db.delete_contact(g.user_id, contact_id):
        return jsonify({"error": "Contact not found"}), 404
    return "", 204
