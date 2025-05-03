import os
import psycopg2
from flask import Flask, render_template, request, jsonify

app = Flask(__name__, static_folder='static', template_folder='templates')

DATABASE_URL = os.environ.get("DATABASE_URL")
print(f"DATABASE_URL on startup: {DATABASE_URL}")

def get_db_connection():
    conn = None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        print("Database connection successful")
        return conn
    except psycopg2.Error as e:
        print(f"Database connection error in get_db_connection: {e}")
        return None

def init_db():
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS codes (
                    id SERIAL PRIMARY KEY,
                    app_name TEXT NOT NULL,
                    code TEXT NOT NULL UNIQUE,
                    used BOOLEAN NOT NULL DEFAULT FALSE,
                    created_at DATE NOT NULL DEFAULT CURRENT_DATE,
                    updated_at DATE NOT NULL DEFAULT CURRENT_DATE
                )
            """)
            conn.commit()
            cur.close()
            print("Database initialized successfully (init_db)")
        except psycopg2.Error as e:
            print(f"Error during database initialization (init_db): {e}")
        finally:
            conn.close()
    else:
        print("Could not get database connection for init_db")

@app.cli.command("initdb")
def initdb_command():
    """Initializes the database."""
    init_db()
    print("Initialized the database via command.")

@app.route("/<app_name>")
def promo_page(app_name):
    conn = get_db_connection()
    if not conn:
        return "Failed to connect to database", 500
    cur = conn.cursor()
    try:
        cur.execute("SELECT code, used FROM codes WHERE app_name = %s", (app_name,))
        codes = cur.fetchall()
        cur.close()
        conn.close()
        return render_template("app_page.html", app_name=app_name, codes=[{"code": row[0], "used": row[1]} for row in codes])
    except psycopg2.Error as e:
        cur.close()
        conn.close()
        return f"Database query error in promo_page: {e}", 500

@app.route("/mark_used", methods=["POST"])
def mark_used():
    data = request.get_json()
    app_name = data.get("app_name")
    code = data.get("code")
    conn = get_db_connection()
    if not conn:
        return jsonify({"success": False, "error": "Failed to connect to database"}), 500
    cur = conn.cursor()
    try:
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
    except psycopg2.Error as e:
        cur.close()
        conn.close()
        return jsonify({"success": False, "error": f"Database error in mark_used: {e}"}), 500

if __name__ == "__main__":
    app.run(debug=True, port=8080)