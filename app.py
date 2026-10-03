from __future__ import annotations

import os
import re
import sqlite3
from datetime import datetime
from functools import wraps

from flask import Flask, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.secret_key = "city-chatbot-secret-key-2026"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                message TEXT NOT NULL,
                response TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS cities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                country TEXT,
                state TEXT,
                description TEXT
            )
            """
        )

        city_count = conn.execute("SELECT COUNT(*) FROM cities").fetchone()[0]
        if city_count == 0:
            default_cities = [
                ("New York", "USA", "New York", "Times Square, Central Park, Brooklyn Bridge, and world-class museums."),
                ("London", "UK", "England", "Big Ben, Tower Bridge, Buckingham Palace, and the West End."),
                ("Paris", "France", "Ile-de-France", "Eiffel Tower, Louvre, Montmartre, and the Seine riverside."),
                ("Tokyo", "Japan", "Tokyo", "Shibuya Crossing, Senso-ji, Tokyo Tower, and vibrant neighborhoods."),
                ("Dubai", "UAE", "Dubai", "Burj Khalifa, Dubai Marina, desert safari, and luxury shopping."),
                ("Singapore", "Singapore", "Singapore", "Gardens by the Bay, Marina Bay, Sentosa, and hawker centers."),
                ("Barcelona", "Spain", "Catalonia", "Sagrada Familia, Gothic Quarter, Beachfront, and tapas culture."),
            ]
            conn.executemany(
                "INSERT INTO cities (name, country, state, description) VALUES (?, ?, ?, ?)",
                default_cities,
            )

        user_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        if user_count == 0:
            demo_user = {
                "name": "Demo User",
                "email": "demo@citychatbot.com",
                "username": "demo",
                "password_hash": generate_password_hash("demo123"),
            }
            conn.execute(
                "INSERT INTO users (name, email, username, password_hash) VALUES (?, ?, ?, ?)",
                (
                    demo_user["name"],
                    demo_user["email"],
                    demo_user["username"],
                    demo_user["password_hash"],
                ),
            )

        conn.commit()


def login_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return view_func(*args, **kwargs)

    return wrapped


def normalize_text(value):
    if value is None:
        return ""
    return " ".join(str(value).strip().split())


def safe_json_response(payload, status=200):
    response = jsonify(payload)
    response.status_code = status
    return response


def get_user_by_id(user_id):
    with get_db_connection() as conn:
        return conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


def get_city_list():
    with get_db_connection() as conn:
        rows = conn.execute(
            "SELECT id, name, country, state, description FROM cities ORDER BY name ASC"
        ).fetchall()
        return [dict(row) for row in rows]


def generate_city_chatbot_response(city_name: str, question: str) -> str:
    city = normalize_text(city_name) or "your city"
    text = normalize_text(question).lower()

    if any(word in text for word in ["tourist", "famous", "attraction", "places", "landmark", "visit"]):
        return (
            f"The popular tourist places in {city} include iconic landmarks, scenic viewpoints, and local heritage spots. "
            f"Start with the city center, a famous landmark, and a nearby park or market for a balanced experience."
        )

    if any(word in text for word in ["restaurant", "eat", "food", "dining", "cafe", "coffee"]):
        return (
            f"You can find great restaurants in {city} in the central districts, markets, and popular neighborhoods. "
            f"Look for local street food, family-run cafes, and highly rated dining areas near the main attractions."
        )

    if any(word in text for word in ["hospital", "clinic", "medical", "doctor", "urgent care"]):
        return (
            f"For hospitals in {city}, check the major medical centers and nearby clinics located near central roads and transit hubs. "
            f"It is best to use a map app to find the nearest option and confirm emergency services."
        )

    if any(word in text for word in ["weather", "rain", "sunny", "temperature", "forecast"]):
        return (
            f"The weather in {city} can change throughout the day, so check the local forecast before outdoor plans. "
            f"Carry light layers if you are exploring the city in the morning or evening."
        )

    if any(word in text for word in ["bus", "station", "transport", "metro", "train", "airport", "travel"]):
        return (
            f"Public transport in {city} is usually available through bus stations, metro lines, and major transit points. "
            f"Use the nearest station or main avenue to find routes that connect to tourist spots and residential areas."
        )

    if any(word in text for word in ["shopping", "mall", "market", "buy", "store"]):
        return (
            f"For shopping in {city}, explore commercial streets, city-center malls, and local markets. "
            f"These areas usually offer clothing, gifts, food, and daily essentials in one place."
        )

    if any(word in text for word in ["event", "festival", "concert", "happening", "activity"]):
        return (
            f"Events in {city} are often hosted in entertainment districts, cultural centers, and public squares. "
            f"Check local listings or social pages to see live music, festivals, exhibitions, and seasonal celebrations."
        )

    if any(word in text for word in ["how can i go", "how to reach", "reach", "go there", "direction", "navigate"]):
        return (
            f"To reach places in {city}, use public transport, ride-hailing apps, or a guided route from your current location. "
            f"The easiest plan is to choose a central station or landmark and follow the route shown on the map."
        )

    if any(word in text for word in ["nearby", "close", "around", "near"]):
        return (
            f"Nearby attractions and services in {city} are usually concentrated around major transit points and popular streets. "
            f"Checking a map app for the nearest landmark is the fastest way to find them."
        )

    return (
        "I can help you find places, restaurants, hospitals, transportation, tourist attractions and other information about your city."
    )


@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("chatbot_page"))
    return redirect(url_for("login_page"))


@app.route("/login", methods=["GET", "POST"])
def login_page():
    if request.method == "POST":
        data = request.get_json(silent=True)
        if data is None:
            data = request.form

        username_or_email = normalize_text(data.get("username") or data.get("email") or data.get("username_or_email"))
        password = normalize_text(data.get("password") or "")

        if not username_or_email or not password:
            return safe_json_response({"success": False, "message": "Username/email and password are required."}, 400)

        try:
            with get_db_connection() as conn:
                user = conn.execute(
                    "SELECT * FROM users WHERE username = ? OR email = ?",
                    (username_or_email, username_or_email),
                ).fetchone()
        except sqlite3.Error:
            return safe_json_response({"success": False, "message": "Database error. Please try again later."}, 500)

        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["name"] = user["name"]
            return safe_json_response({"success": True, "redirect": url_for("chatbot_page")})

        return safe_json_response({"success": False, "message": "Invalid username/email or password."}, 401)

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register_page():
    if request.method == "POST":
        data = request.get_json(silent=True)
        if data is None:
            data = request.form

        name = normalize_text(data.get("name"))
        email = normalize_text(data.get("email"))
        username = normalize_text(data.get("username"))
        password = normalize_text(data.get("password") or "")
        confirm_password = normalize_text(data.get("confirm_password") or "")

        if not all([name, email, username, password, confirm_password]):
            return safe_json_response({"success": False, "message": "All fields are required."}, 400)

        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
            return safe_json_response({"success": False, "message": "Enter a valid email address."}, 400)

        if len(username) < 3:
            return safe_json_response({"success": False, "message": "Username must contain at least 3 characters."}, 400)

        if password != confirm_password:
            return safe_json_response({"success": False, "message": "Passwords do not match."}, 400)

        if len(password) < 6:
            return safe_json_response({"success": False, "message": "Password must be at least 6 characters long."}, 400)

        try:
            with get_db_connection() as conn:
                duplicate_email = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
                if duplicate_email:
                    return safe_json_response({"success": False, "message": "This email is already registered."}, 409)

                duplicate_username = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
                if duplicate_username:
                    return safe_json_response({"success": False, "message": "This username is already taken."}, 409)

                password_hash = generate_password_hash(password)
                conn.execute(
                    "INSERT INTO users (name, email, username, password_hash) VALUES (?, ?, ?, ?)",
                    (name, email, username, password_hash),
                )
                conn.commit()
        except sqlite3.Error:
            return safe_json_response({"success": False, "message": "Database error while creating your account."}, 500)

        return safe_json_response({"success": True, "message": "Account created successfully. Please log in."})

    return render_template("register.html")


@app.route("/logout", methods=["POST", "GET"])
def logout():
    session.clear()
    return redirect(url_for("login_page"))


@app.route("/home")
@login_required
def home_page():
    current_user = get_user_by_id(session["user_id"])
    return render_template("home.html", user=current_user)


@app.route("/chatbot")
@login_required
def chatbot_page():
    current_user = get_user_by_id(session["user_id"])
    return render_template("chatbot.html", user=current_user, cities=get_city_list())


@app.route("/api/me")
@login_required
def api_me():
    current_user = get_user_by_id(session["user_id"])
    if not current_user:
        return safe_json_response({"success": False, "message": "User not found."}, 404)
    return safe_json_response({
        "success": True,
        "user": {
            "id": current_user["id"],
            "name": current_user["name"],
            "email": current_user["email"],
            "username": current_user["username"],
        }
    })


@app.route("/api/cities")
@login_required
def api_cities():
    return safe_json_response({"success": True, "cities": get_city_list()})


@app.route("/api/chat", methods=["POST"])
@login_required
def api_chat():
    if not request.is_json and request.form is None:
        return safe_json_response({"success": False, "message": "Invalid request format."}, 400)

    data = request.get_json(silent=True)
    if data is None:
        data = request.form

    city = normalize_text(data.get("city") or "")
    message = normalize_text(data.get("message") or "")

    if not message:
        return safe_json_response({"success": False, "message": "Please enter a message."}, 400)

    try:
        bot_reply = generate_city_chatbot_response(city, message)

        with get_db_connection() as conn:
            conn.execute(
                "INSERT INTO chat_history (user_id, message, response) VALUES (?, ?, ?)",
                (session["user_id"], message, bot_reply),
            )
            conn.commit()
    except sqlite3.Error:
        return safe_json_response({"success": False, "message": "Could not save chat history."}, 500)

    return safe_json_response({"success": True, "response": bot_reply, "city": city})


@app.route("/api/chat/history", methods=["GET", "DELETE"])
@login_required
def chat_history():
    if request.method == "DELETE":
        try:
            with get_db_connection() as conn:
                conn.execute("DELETE FROM chat_history WHERE user_id = ?", (session["user_id"],))
                conn.commit()
            return safe_json_response({"success": True, "message": "Chat history cleared."})
        except sqlite3.Error:
            return safe_json_response({"success": False, "message": "Unable to clear chat history."}, 500)

    try:
        with get_db_connection() as conn:
            rows = conn.execute(
                "SELECT id, message, response, created_at FROM chat_history WHERE user_id = ? ORDER BY id ASC",
                (session["user_id"],),
            ).fetchall()
    except sqlite3.Error:
        return safe_json_response({"success": False, "message": "Database error while retrieving chat history."}, 500)

    history = [{
        "id": row["id"],
        "message": row["message"],
        "response": row["response"],
        "created_at": row["created_at"],
    } for row in rows]

    return safe_json_response({"success": True, "history": history})


@app.errorhandler(404)
def not_found(error):
    return render_template("login.html"), 404


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
