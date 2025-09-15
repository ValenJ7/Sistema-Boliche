from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret")

APP_NAME = os.environ.get("APP_NAME", "DiscoManager Lite")
DEFAULT_CITY = os.environ.get("CITY", "Cordoba")

@app.context_processor
def inject_globals():
    return dict(APP_NAME=APP_NAME)

@app.route("/")
def dashboard():
    today = datetime.now().strftime("%Y-%m-%d")
    return render_template("index.html", today=today, city=DEFAULT_CITY)

@app.route("/eventos")
def eventos():
    # Lista de ejemplo (luego reemplazamos con SQLite)
    sample = [
        {"nombre": "Electro Night", "fecha": "2025-10-31", "capacidad": 500, "estado": "Programado"},
        {"nombre": "Retro 80s", "fecha": "2025-11-15", "capacidad": 350, "estado": "Programado"},
    ]
    return render_template("eventos.html", eventos=sample)

@app.route("/acerca")
def acerca():
    return render_template("acerca.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(debug=True, port=port)
