CREATE TABLE users (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_name VARCHAR(50) NOT NULL UNIQUE,
    password_hash TEXT NOT NULL
);

CREATE TABLE groups (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(60) NOT NULL,
    UNIQUE (user_id, name),
    CONSTRAINT groups_user_id_id_key UNIQUE (user_id, id)
);

CREATE TABLE contacts (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    group_id INTEGER,
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(30) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT contacts_user_id_group_id_fkey
        FOREIGN KEY (user_id, group_id) REFERENCES groups(user_id, id)
        ON DELETE SET NULL (group_id)
);

CREATE INDEX contacts_user_name_idx ON contacts(user_id, name);
CREATE INDEX contacts_user_created_idx ON contacts(user_id, created_at);
CREATE INDEX contacts_group_idx ON contacts(group_id);
