import os
import psycopg2
from flask import Flask, render_template, request, jsonify

app = Flask(__name__, static_folder='static', template_folder='templates')

DATABASE_URL = os.environ.get("DATABASE_URL")

def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL)
    return conn

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS codes (
            id SERIAL PRIMARY KEY,
            app_name TEXT NOT NULL,
            code TEXT NOT NULL UNIQUE,
            used BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    cur.close()
    conn.close()

@app.cli.command("initdb")
def initdb_command():
    """Initializes the database."""
    init_db()
    print("Initialized the database.")

@app.route("/<app_name>")
def promo_page(app_name):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT code, used FROM codes WHERE app_name = %s", (app_name,))
    codes = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("app_page.html", app_name=app_name, codes=[{"code": row[0], "used": row[1]} for row in codes])

@app.route("/mark_used", methods=["POST"])
def mark_used():
    data = request.get_json()
    app_name = data.get("app_name")
    code = data.get("code")
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, used FROM codes WHERE app_name = %s AND code = %s", (app_name, code))
    result = cur.fetchone()

    if not result:
        cur.close()
        conn.close()
        return jsonify({"success": False, "error": "Code not found"}), 404

    code_id, used = result
    if used:
        cur.close()
        conn.close()
        return jsonify({"success": False, "error": "Code already used"}), 400

    cur.execute("UPDATE codes SET used = TRUE WHERE id = %s", (code_id,))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"success": True})

if __name__ == "__main__":
    app.run(debug=True)