import os
import secrets

import psycopg
from psycopg.rows import dict_row
from flask import Flask, jsonify, request
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "")
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "")
APP_TITLE = os.getenv("APP_TITLE", "Cloud Mini Project")
APP_VERSION = os.getenv("APP_VERSION", "1.0")

def get_connection():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not configured")
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)

def is_admin_request():
    header = request.headers.get("Authorization", "")
    prefix = "Bearer "

    if not header.startswith(prefix) or not ADMIN_TOKEN:
        return False

    provided_token = header[len(prefix):].strip()
    return secrets.compare_digest(provided_token, ADMIN_TOKEN)

@app.get("/")
def index():
    return jsonify({
        "application": APP_TITLE,
        "version": APP_VERSION,
        "status": "running",
        "endpoints": [
            "/health",
            "/api/stock",
            "/api/admin/stats"
        ]
    })

@app.get("/health")
def health():
    try:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1 AS ok;")
                cursor.fetchone()

        return jsonify({
            "status": "ok",
            "database": "ok",
            "version": APP_VERSION
        }), 200

    except Exception:
        return jsonify({
            "status": "degraded",
            "database": "error",
            "version": APP_VERSION
        }), 503

@app.get("/api/stock")
def get_items():
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, sku, name, status, created_at
                FROM products
                ORDER BY id DESC;
                """
            )
            items = cursor.fetchall()

    return jsonify(items)

@app.post("/api/stock")
def create_item():
    if not is_admin_request():
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    sku = str(data.get("sku", "")).strip()
    name = str(data.get("name", "")).strip()
    status = str(data.get("status", "new")).strip()

    if not sku or not name:
        return jsonify({
            "error": "sku and name are required"
        }), 400

    if status not in {"new", "in_progress", "done"}:
        return jsonify({"error": "invalid status"}), 400

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO products (sku, name, status)
                VALUES (%s, %s, %s)
                RETURNING id, sku, name, status, created_at;
                """,
                (sku, name, status)
            )
            item = cursor.fetchone()

    return jsonify(item), 201

@app.get("/api/admin/stats")
def admin_stats():
    if not is_admin_request():
        return jsonify({"error": "Unauthorized"}), 401

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT status, COUNT(*) AS count
                FROM products
                GROUP BY status
                ORDER BY status;
                """
            )
            stats = cursor.fetchall()

    return jsonify({
        "application": APP_TITLE,
        "version": APP_VERSION,
        "statistics": stats
    })

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True)
