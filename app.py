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

# ====== extra imports para reporte ======
import io, base64
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # backend sin GUI
import matplotlib.pyplot as plt

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

def build_event_report_image(event_id: int) -> str | None:
    """Genera gráfico PNG (base64) con cantidad vendida por trago para un evento."""
    resumen = fetch_drinks_summary_by_event(event_id)
    if not resumen:
        return None

    df = pd.DataFrame(resumen)
    if df.empty:
        return None

    df["nombre"] = df["nombre"].astype(str)
    df["cantidad"] = pd.to_numeric(df["cantidad"], errors="coerce").fillna(0).astype(int)
    df = df.sort_values("cantidad", ascending=False)

    # Paleta simple y legible
    palette = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#06b6d4", "#84cc16", "#f97316"]
    colors = [palette[i % len(palette)] for i in range(len(df))]

    fig, ax = plt.subplots(figsize=(6.5, 3.6), dpi=150)
    ax.bar(df["nombre"], df["cantidad"], color=colors)
    ax.set_title("Cantidad vendida por trago")
    ax.set_xlabel("Trago")
    ax.set_ylabel("Cantidad")
    ax.tick_params(axis="x", rotation=45, labelsize=8)
    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode("ascii")

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

    # Todos los eventos de hoy
    eventos_hoy = [e for e in eventos if e["fecha"] == today]

    # Generar reportes por evento
    reportes = {}
    for ev in eventos_hoy:
        img = build_event_report_image(ev["id"])
        if img:
            reportes[ev["id"]] = img

    return render_template(
        "index.html",
        today=today,
        city=DEFAULT_CITY,
        eventos_hoy=eventos_hoy,
        reportes=reportes,
    )


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
        nombre    = (request.form.get("nombre") or "").strip()
        fecha     = (request.form.get("fecha") or "").strip()
        hora      = (request.form.get("hora") or "").strip()
        capacidad_raw = request.form.get("capacidad", "").strip()
        estado    = request.form.get("estado", "activo")

        # Normalizar capacidad
        try:
            capacidad = int(capacidad_raw) if capacidad_raw != "" else 0
        except ValueError:
            capacidad = -1  # forzar error

        try:
            insert_event(nombre, fecha, hora, capacidad, estado)
            flash("Evento creado con éxito.", "success")
            return redirect(url_for("eventos"))
        except ValueError as ve:
            flash(str(ve), "error")
            return render_template("eventos_nuevo.html",
                                   form={"nombre": nombre, "fecha": fecha, "hora": hora,
                                         "capacidad": capacidad_raw, "estado": estado})

    return render_template("eventos_nuevo.html")

@app.route("/eventos/<int:event_id>/editar", methods=["GET", "POST"])
def editar_evento(event_id):
    e = fetch_event_by_id(event_id)
    if not e:
        flash("Evento no encontrado.", "error")
        return redirect(url_for("eventos"))

    if request.method == "POST":
        nombre    = (request.form.get("nombre") or "").strip()
        fecha     = (request.form.get("fecha") or "").strip()
        hora      = (request.form.get("hora") or "").strip()
        capacidad_raw = request.form.get("capacidad", "").strip()
        estado    = request.form.get("estado", "activo")

        try:
            capacidad = int(capacidad_raw) if capacidad_raw != "" else 0
        except ValueError:
            capacidad = -1

        try:
            update_event(event_id, nombre, fecha, hora, capacidad, estado)
            flash("Evento actualizado.", "success")
            return redirect(url_for("eventos"))
        except ValueError as ve:
            flash(str(ve), "error")
            # Reinyectar valores en el formulario
            e = {
                "id": event_id, "nombre": nombre, "fecha": fecha, "hora": hora,
                "capacidad": capacidad_raw, "estado": estado
            }
            return render_template("eventos_editar.html", e=e)

    return render_template("eventos_editar.html", e=e)

@app.post("/eventos/<int:event_id>/borrar")
def borrar_evento(event_id):
    delete_event(event_id)
    flash("Evento eliminado.", "success")
    return redirect(url_for("eventos"))

# ========================
# Ventas de tragos
# ========================
@app.route("/eventos/<int:event_id>/vender", methods=["GET", "POST"])
def vender(event_id):
    e = fetch_event_by_id(event_id)
    if not e:
        flash("Evento no encontrado.", "error")
        return redirect(url_for("eventos"))

    if not evento_es_hoy(e):
        flash("Este evento no es hoy, no se pueden registrar ventas.", "error")
        return redirect(url_for("eventos"))

    if request.method == "POST":
        registros = []
        for item in catalogo_tragos:
            try:
                cant = int(request.form.get(f"cantidad_{item['id']}", 0))
            except ValueError:
                cant = 0
            if cant > 0:
                registros.append((item["nombre"], item["precio"], cant))

        if not registros:
            flash("No se registró ninguna bebida. Seleccioná al menos una cantidad.", "error")
            return redirect(url_for("vender", event_id=event_id))

        # Crear batch y guardar ventas
        batch_id = create_sale_batch(event_id)
        for nombre, precio, cantidad in registros:
            insert_drink(event_id, nombre, precio, cantidad, batch_id=batch_id)

        # Resumen claro: "3 Fernet con Coca, 2 Cervezas"
        partes = [f"{cantidad} {nombre}" for (nombre, _precio, cantidad) in registros]
        resumen = ", ".join(partes)

        flash(f"Venta realizada con éxito – {resumen}.", "success")
        return redirect(url_for("vender", event_id=event_id))

    return render_template("vender.html", evento=e, catalogo=catalogo_tragos)

@app.route("/eventos/<int:event_id>/tragos")
def ver_tragos(event_id):
    e = fetch_event_by_id(event_id)
    if not e:
        flash("Evento no encontrado.", "error")
        return redirect(url_for("eventos"))

    resumen = fetch_drinks_summary_by_event(event_id)
    batches = fetch_batches_by_event(event_id)
    batches_items = {b["id"]: fetch_drinks_by_batch(b["id"]) for b in batches}
    detalle = fetch_drinks_by_event(event_id)

    return render_template(
        "tragos.html",
        evento=e,
        resumen=resumen,
        batches=batches,
        batches_items=batches_items,
        tragos=detalle,
    )

@app.post("/eventos/tragos/<int:drink_id>/eliminar")
def eliminar_trago(drink_id):
    d = fetch_drink_by_id(drink_id)
    if not d:
        flash("Venta no encontrada.", "error")
        return redirect(url_for("eventos"))

    delete_drink(drink_id)
    flash("Venta eliminada.", "success")
    return redirect(url_for("ver_tragos", event_id=d["event_id"]))

# ========================
# Reportes
# ========================
@app.route("/reportes/evento/<int:event_id>")
def reporte_evento(event_id):
    e = fetch_event_by_id(event_id)
    if not e:
        flash("Evento no encontrado.", "error")
        return redirect(url_for("eventos"))

    resumen = fetch_drinks_summary_by_event(event_id)
    report_img = build_event_report_image(event_id)
    return render_template("reporte_evento.html", evento=e, resumen=resumen, report_img=report_img)

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
