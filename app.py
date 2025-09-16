from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime
import os
from dotenv import load_dotenv
from db import init_db, fetch_all_events, insert_event

# Cargar variables del entorno
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret")

# Inicializar DB si no existe
init_db()

APP_NAME = os.environ.get("APP_NAME", "DiscoManager Lite")
DEFAULT_CITY = os.environ.get("CITY", "Cordoba")

# Variables globales para usar en las plantillas
@app.context_processor
def inject_globals():
    return dict(APP_NAME=APP_NAME)

# Dashboard principal
@app.route("/")
def dashboard():
    today = datetime.now().strftime("%Y-%m-%d")
    return render_template("index.html", today=today, city=DEFAULT_CITY)

# Listado de eventos
@app.route("/eventos")
def eventos():
    eventos = fetch_all_events()  # ahora viene de SQLite
    return render_template("eventos.html", eventos=eventos)

# Formulario para crear evento
@app.route("/eventos/nuevo", methods=["GET", "POST"])
def nuevo_evento():
    if request.method == "POST":
        nombre = request.form.get("nombre")
        fecha = request.form.get("fecha")
        hora = request.form.get("hora")
        capacidad = request.form.get("capacidad")
        estado = request.form.get("estado", "activo")

        if not nombre or not fecha or not capacidad:
            flash("Todos los campos son obligatorios", "error")
            return redirect(url_for("nuevo_evento"))

        insert_event(nombre, fecha, hora, capacidad, estado)
        flash("Evento creado con éxito", "success")
        return redirect(url_for("eventos"))

    return render_template("nuevo_evento.html")

# Página "Acerca"
@app.route("/acerca")
def acerca():
    return render_template("acerca.html")

# Punto de entrada
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(debug=True, port=port)
