from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime
import os
from dotenv import load_dotenv
from db import (
    init_db,
    fetch_all_events,
    insert_event,
    fetch_event_by_id,
    update_event,
    delete_event,
    # drinks
    fetch_drinks_by_event,
    insert_drink,
    delete_drink,
    fetch_drink_by_id,
    fetch_drinks_summary_by_event,
    # batches
    create_sale_batch,
    fetch_batches_by_event,
    fetch_drinks_by_batch,
)

# Cargar variables del entorno
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret")

# Inicializar DB si no existe
init_db()

APP_NAME = os.environ.get("APP_NAME", "DiscoManager Lite")
DEFAULT_CITY = os.environ.get("CITY", "Cordoba")

# ========================
# Catálogo fijo de tragos
# ========================
catalogo_tragos = [
    {"id": 1, "nombre": "Fernet con Coca", "precio": 1500},
    {"id": 2, "nombre": "Cerveza", "precio": 1200},
    {"id": 3, "nombre": "Vodka con Speed", "precio": 2000},
    {"id": 4, "nombre": "Gin Tonic", "precio": 1800},
    {"id": 5, "nombre": "Agua", "precio": 800},
]

# ========================
# Helpers
# ========================
def evento_es_hoy(evento):
    hoy = datetime.now().date()
    fecha_evento = datetime.strptime(evento["fecha"], "%Y-%m-%d").date()
    return fecha_evento == hoy

@app.context_processor
def inject_globals():
    return dict(APP_NAME=APP_NAME, evento_es_hoy=evento_es_hoy)

# ========================
# Dashboard
# ========================
@app.route("/")
def dashboard():
    today = datetime.now().strftime("%Y-%m-%d")
    eventos = fetch_all_events()
    evento_hoy = next((e for e in eventos if e["fecha"] == today), None)
    return render_template("index.html", today=today, city=DEFAULT_CITY, evento_hoy=evento_hoy)

# ========================
# Eventos
# ========================
@app.route("/eventos")
def eventos():
    eventos = fetch_all_events()
    return render_template("eventos.html", eventos=eventos)

@app.route("/eventos/nuevo", methods=["GET", "POST"], endpoint="nuevo_evento")
def crear_evento():
    if request.method == "POST":
        nombre    = request.form.get("nombre", "").strip()
        fecha     = request.form.get("fecha")
        hora      = request.form.get("hora") or None
        capacidad = int(request.form.get("capacidad") or 0)
        estado    = request.form.get("estado", "activo")

        if not nombre or not fecha:
            flash("Nombre y fecha son obligatorios.", "error")
            return render_template("eventos_nuevo.html")

        insert_event(nombre, fecha, hora, capacidad, estado)
        flash("Evento creado con éxito", "ok")
        return redirect(url_for("eventos"))

    return render_template("eventos_nuevo.html")

@app.route("/eventos/<int:event_id>/editar", methods=["GET", "POST"])
def editar_evento(event_id):
    e = fetch_event_by_id(event_id)
    if not e:
        flash("Evento no encontrado", "error")
        return redirect(url_for("eventos"))

    if request.method == "POST":
        nombre    = request.form.get("nombre", "").strip()
        fecha     = request.form.get("fecha")
        hora      = request.form.get("hora") or None
        capacidad = int(request.form.get("capacidad") or 0)
        estado    = request.form.get("estado", "activo")

        if not nombre or not fecha:
            flash("Nombre y fecha son obligatorios.", "error")
            return render_template("eventos_editar.html", e=e)

        update_event(event_id, nombre, fecha, hora, capacidad, estado)
        flash("Evento actualizado", "ok")
        return redirect(url_for("eventos"))

    return render_template("eventos_editar.html", e=e)

@app.post("/eventos/<int:event_id>/borrar")
def borrar_evento(event_id):
    delete_event(event_id)
    flash("Evento eliminado", "ok")
    return redirect(url_for("eventos"))

# ========================
# Ventas de tragos
# ========================
@app.route("/eventos/<int:event_id>/vender", methods=["GET", "POST"])
def vender(event_id):
    e = fetch_event_by_id(event_id)
    if not e:
        flash("Evento no encontrado", "error")
        return redirect(url_for("eventos"))

    if not evento_es_hoy(e):
        flash("Este evento no es hoy, no se pueden registrar ventas.", "error")
        return redirect(url_for("eventos"))

    if request.method == "POST":
        # Recolectar cantidades
        registros = []
        for item in catalogo_tragos:
            cant = int(request.form.get(f"cantidad_{item['id']}", 0))
            if cant > 0:
                registros.append((item["nombre"], item["precio"], cant))

        if registros:
            batch_id = create_sale_batch(event_id)
            for nombre, precio, cantidad in registros:
                insert_drink(event_id, nombre, precio, cantidad, batch_id=batch_id)
            flash("Ventas registradas con éxito", "ok")
        else:
            flash("No se registraron ventas", "error")

        # Quedarnos en /vender mostrando flash
        return redirect(url_for("vender", event_id=event_id))

    return render_template("vender.html", evento=e, catalogo=catalogo_tragos)

@app.route("/eventos/<int:event_id>/tragos")
def ver_tragos(event_id):
    e = fetch_event_by_id(event_id)
    if not e:
        flash("Evento no encontrado", "error")
        return redirect(url_for("eventos"))

    # Resumen por trago (global)
    resumen = fetch_drinks_summary_by_event(event_id)

    # Lotes (batches) y sus items
    batches = fetch_batches_by_event(event_id)
    batches_items = {}
    for b in batches:
        batches_items[b["id"]] = fetch_drinks_by_batch(b["id"])

    # Detalle plano (por registro) por si querés filtrar/buscar
    detalle = fetch_drinks_by_event(event_id)

    return render_template(
        "tragos.html",
        evento=e,
        resumen=resumen,
        batches=batches,
        batches_items=batches_items,
        tragos=detalle
    )

@app.post("/eventos/tragos/<int:drink_id>/eliminar")
def eliminar_trago(drink_id):
    d = fetch_drink_by_id(drink_id)
    if not d:
        flash("Venta no encontrada", "error")
        return redirect(url_for("eventos"))

    delete_drink(drink_id)
    flash("Venta eliminada", "ok")
    return redirect(url_for("ver_tragos", event_id=d["event_id"]))

# ========================
# Página "Acerca"
# ========================
@app.route("/acerca")
def acerca():
    return render_template("acerca.html")

# ========================
# Punto de entrada
# ========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(debug=True, port=port)
