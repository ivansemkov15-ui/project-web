import json
import os
from pathlib import Path

from flask import Flask, jsonify

from auth_api import auth_api
from contacts_api import contacts_api
from groups_api import groups_api
from stats_api import stats_api
from users_api import users_api


BASE_DIR = Path(__file__).resolve().parent


def create_app():
    app = Flask(__name__, static_folder="static")
    app.json.ensure_ascii = False

    app.register_blueprint(auth_api)
    app.register_blueprint(contacts_api)
    app.register_blueprint(groups_api)
    app.register_blueprint(stats_api)
    app.register_blueprint(users_api)

    @app.get("/")
    def index():
        if (BASE_DIR / "static" / "index.html").exists():
            return app.send_static_file("index.html")
        return jsonify({"message": "Phonebook API is running"})

    @app.get("/dashboard")
    def dashboard():
        if (BASE_DIR / "static" / "dashboard.html").exists():
            return app.send_static_file("dashboard.html")
        return jsonify({"message": "Dashboard page is being developed", "api": "/api/stats"})

    @app.get("/about")
    def about():
        if (BASE_DIR / "static" / "about.html").exists():
            return app.send_static_file("about.html")
        return about_api()

    @app.get("/api/about")
    def about_api():
        with (BASE_DIR / "about.json").open(encoding="utf-8") as file:
            return jsonify(json.load(file))

    @app.get("/health")
    def health():
        return jsonify({"status": "ok", "service": "core"})

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")))
