import os

import psycopg
from psycopg.rows import dict_row


def query(sql, params=(), one=False):
    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql://phonebook:phonebook@127.0.0.1:5432/phonebook",
    )
    with psycopg.connect(database_url, row_factory=dict_row, connect_timeout=5) as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            if cursor.description is None:
                return None
            return cursor.fetchone() if one else cursor.fetchall()


def get_user_by_name(user_name):
    return query(
        "SELECT id, user_name, password_hash FROM users WHERE user_name = %s",
        (user_name,),
        one=True,
    )


def get_user_by_id(user_id):
    return query(
        "SELECT id, user_name FROM users WHERE id = %s",
        (user_id,),
        one=True,
    )


def create_user(user_name, password_hash):
    return query(
        "INSERT INTO users (user_name, password_hash) VALUES (%s, %s) "
        "RETURNING id, user_name",
        (user_name, password_hash),
        one=True,
    )


def list_groups(user_id):
    return query(
        "SELECT id, name FROM groups WHERE user_id = %s ORDER BY name, id",
        (user_id,),
    )


def group_exists(user_id, group_id):
    return query(
        "SELECT id FROM groups WHERE user_id = %s AND id = %s",
        (user_id, group_id),
        one=True,
    ) is not None


def create_group(user_id, name):
    return query(
        "INSERT INTO groups (user_id, name) VALUES (%s, %s) RETURNING id, name",
        (user_id, name),
        one=True,
    )


def delete_group(user_id, group_id):
    return query(
        "DELETE FROM groups WHERE id = %s AND user_id = %s RETURNING id",
        (group_id, user_id),
        one=True,
    ) is not None


def list_contacts(user_id, search, group_id, sort_by, order, page, per_page):
    conditions = ["c.user_id = %s"]
    params = [user_id]

    if search:
        conditions.append("(c.name ILIKE %s OR c.phone ILIKE %s)")
        params.extend([f"%{search}%", f"%{search}%"])
    if group_id is not None:
        conditions.append("c.group_id = %s")
        params.append(group_id)

    where = " AND ".join(conditions)
    count_row = query(
        f"SELECT COUNT(*) AS total FROM contacts c WHERE {where}",
        tuple(params),
        one=True,
    )

    allowed_sort = {"name": "c.name", "phone": "c.phone", "created_at": "c.created_at"}
    column = allowed_sort.get(sort_by, "c.name")
    direction = "DESC" if order == "desc" else "ASC"
    offset = (page - 1) * per_page

    rows = query(
        "SELECT c.id, c.name, c.phone, c.group_id, g.name AS group_name, c.created_at "
        "FROM contacts c LEFT JOIN groups g ON c.group_id = g.id "
        f"WHERE {where} ORDER BY {column} {direction}, c.id ASC LIMIT %s OFFSET %s",
        tuple(params + [per_page, offset]),
    )
    return rows, count_row["total"]


def get_contact(user_id, contact_id):
    return query(
        "SELECT c.id, c.name, c.phone, c.group_id, g.name AS group_name, c.created_at "
        "FROM contacts c LEFT JOIN groups g ON c.group_id = g.id "
        "WHERE c.user_id = %s AND c.id = %s",
        (user_id, contact_id),
        one=True,
    )


def create_contact(user_id, name, phone, group_id):
    return query(
        "INSERT INTO contacts (user_id, name, phone, group_id) "
        "VALUES (%s, %s, %s, %s) RETURNING id",
        (user_id, name, phone, group_id),
        one=True,
    )


def update_contact(user_id, contact_id, changes):
    fields = []
    values = []
    for field in ("name", "phone", "group_id"):
        if field in changes:
            fields.append(f"{field} = %s")
            values.append(changes[field])

    if not fields:
        return None

    values.extend([user_id, contact_id])
    return query(
        f"UPDATE contacts SET {', '.join(fields)} "
        "WHERE user_id = %s AND id = %s RETURNING id",
        tuple(values),
        one=True,
    )


def delete_contact(user_id, contact_id):
    return query(
        "DELETE FROM contacts WHERE user_id = %s AND id = %s RETURNING id",
        (user_id, contact_id),
        one=True,
    ) is not None


def get_statistics(user_id):
    total = query(
        "SELECT COUNT(*) AS count FROM contacts WHERE user_id = %s",
        (user_id,),
        one=True,
    )["count"]
    groups = query(
        "SELECT g.name, COUNT(c.id) AS count "
        "FROM groups g LEFT JOIN contacts c ON c.group_id = g.id AND c.user_id = g.user_id "
        "WHERE g.user_id = %s GROUP BY g.id, g.name ORDER BY g.name",
        (user_id,),
    )
    without_group = query(
        "SELECT COUNT(*) AS count FROM contacts "
        "WHERE user_id = %s AND group_id IS NULL",
        (user_id,),
        one=True,
    )["count"]
    return {"total_contacts": total, "groups": groups, "without_group": without_group}
