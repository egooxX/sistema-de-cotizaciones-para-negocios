"""Sistema de Cotizaciones para Negocios — versión en Python (Flask).

Proyecto de Diego Rodriguez Zamora (GitHub: egooxX).
Crea cotizaciones en minutos: cliente, catálogo reutilizable, folio
consecutivo, descuento e IVA 16%, PDF listo para WhatsApp, historial con
estados y panel de montos pendientes y aceptados.

Uso:
    python -m venv .venv
    .venv/bin/pip install -r requirements.txt
    .venv/bin/python app.py        # abre http://127.0.0.1:5000
    .venv/bin/python seed.py       # (opcional) carga datos de ejemplo
"""

import os
import sqlite3
import time
import urllib.parse
from datetime import date, timedelta

from flask import (
    Flask, g, redirect, render_template, request, url_for, flash, send_file,
)
from fpdf import FPDF

from totales import calcular_totales, formato_mxn

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "cotizaciones-dev")
app.config["DATABASE"] = os.path.join(app.instance_path, "cotizaciones.db")
os.makedirs(app.instance_path, exist_ok=True)

ESTADOS = ["pendiente", "aceptada", "rechazada", "vencida"]


# ---------------------------------------------------------------- base de datos
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    with app.open_resource("schema.sql") as f:
        db.executescript(f.read().decode("utf-8"))
    db.commit()


with app.app_context():
    init_db()


def ahora_ms():
    return int(time.time() * 1000)


def siguiente_folio(db):
    """COT-2026-001, consecutivo por año."""
    anio = date.today().year
    fila = db.execute(
        "SELECT folio FROM quotes WHERE folio LIKE ? ORDER BY id DESC LIMIT 1",
        (f"COT-{anio}-%",),
    ).fetchone()
    n = int(fila["folio"].rsplit("-", 1)[1]) + 1 if fila else 1
    return f"COT-{anio}-{n:03d}"


def totales_de_cotizacion(db, quote_id):
    items = db.execute(
        "SELECT quantity, unit_price FROM quote_items WHERE quote_id = ?",
        (quote_id,),
    ).fetchall()
    quote = db.execute("SELECT * FROM quotes WHERE id = ?", (quote_id,)).fetchone()
    return calcular_totales(
        [(r["quantity"], r["unit_price"]) for r in items],
        quote["discount_percent"],
        quote["tax_percent"],
    )


# ---------------------------------------------------------------------- rutas
@app.route("/")
def panel():
    db = get_db()
    cotizaciones = db.execute(
        "SELECT * FROM quotes ORDER BY created_at DESC LIMIT 10"
    ).fetchall()
    resumen = {"pendiente": 0.0, "aceptada": 0.0}
    for q in db.execute("SELECT id, status FROM quotes").fetchall():
        t = totales_de_cotizacion(db, q["id"])
        if q["status"] in resumen:
            resumen[q["status"]] += float(t["total"])
    return render_template(
        "panel.html",
        cotizaciones=cotizaciones,
        resumen=resumen,
        totales={q["id"]: totales_de_cotizacion(db, q["id"]) for q in cotizaciones},
    )


@app.route("/cotizaciones")
def lista_cotizaciones():
    db = get_db()
    estado = request.args.get("estado", "")
    busqueda = request.args.get("q", "").strip()
    sql = "SELECT * FROM quotes WHERE 1=1"
    params = []
    if estado in ESTADOS:
        sql += " AND status = ?"
        params.append(estado)
    if busqueda:
        sql += " AND (folio LIKE ? OR client_name LIKE ? OR title LIKE ?)"
        params += [f"%{busqueda}%"] * 3
    sql += " ORDER BY created_at DESC"
    cotizaciones = db.execute(sql, params).fetchall()
    return render_template(
        "lista.html",
        cotizaciones=cotizaciones,
        totales={q["id"]: totales_de_cotizacion(db, q["id"]) for q in cotizaciones},
        estado=estado, busqueda=busqueda, estados=ESTADOS,
    )


@app.route("/cotizaciones/nueva", methods=["GET", "POST"])
def nueva_cotizacion():
    db = get_db()
    perfil = db.execute("SELECT * FROM business_profile WHERE id = 1").fetchone()
    catalogo = db.execute(
        "SELECT * FROM catalog_items WHERE active = 1 ORDER BY name"
    ).fetchall()
    clientes = db.execute("SELECT * FROM clients ORDER BY name").fetchall()

    if request.method == "POST":
        descripciones = request.form.getlist("descripcion[]")
        cantidades = request.form.getlist("cantidad[]")
        precios = request.form.getlist("precio[]")
        items = [
            (float(c), float(p))
            for d, c, p in zip(descripciones, cantidades, precios)
            if d.strip() and float(c) > 0
        ]
        if not items:
            flash("Agrega al menos un producto o servicio.", "error")
            return redirect(url_for("nueva_cotizacion"))

        nombre_cliente = request.form["cliente_nombre"].strip()
        cliente_id = request.form.get("cliente_id") or None
        if cliente_id:
            cliente = db.execute(
                "SELECT * FROM clients WHERE id = ?", (cliente_id,)
            ).fetchone()
            nombre_cliente = cliente["name"]
        elif nombre_cliente:
            existente = db.execute(
                "SELECT id FROM clients WHERE name = ?", (nombre_cliente,)
            ).fetchone()
            if existente:
                cliente_id = existente["id"]
            else:
                cur = db.execute(
                    "INSERT INTO clients (name, company, phone, email, created_at)"
                    " VALUES (?, ?, ?, ?, ?)",
                    (nombre_cliente, request.form.get("cliente_empresa", ""),
                     request.form.get("cliente_telefono", ""),
                     request.form.get("cliente_email", ""), ahora_ms()),
                )
                cliente_id = cur.lastrowid

        vigencia = int(request.form.get("vigencia_dias") or perfil["default_validity_days"])
        valido_hasta = (date.today() + timedelta(days=vigencia)).isoformat()
        folio = siguiente_folio(db)
        cur = db.execute(
            """INSERT INTO quotes
               (folio, title, client_id, client_name, client_company,
                client_phone, client_email, status, valid_until,
                discount_percent, tax_percent, notes, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, 'pendiente', ?, ?, ?, ?, ?, ?)""",
            (folio, request.form.get("titulo") or "Cotización de servicios",
             cliente_id, nombre_cliente,
             request.form.get("cliente_empresa", ""),
             request.form.get("cliente_telefono", ""),
             request.form.get("cliente_email", ""), valido_hasta,
             float(request.form.get("descuento", 0) or 0),
             float(request.form.get("iva", perfil["default_tax_percent"]) or 16),
             request.form.get("notas", ""), ahora_ms(), ahora_ms()),
        )
        quote_id = cur.lastrowid
        for i, (d, c, p) in enumerate(
            zip(descripciones, cantidades, precios)
        ):
            if not d.strip():
                continue
            db.execute(
                """INSERT INTO quote_items
                   (quote_id, description, quantity, unit_price, unit, sort_order)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (quote_id, d.strip(), float(c), float(p),
                 request.form.getlist("unidad[]")[i] if i < len(request.form.getlist("unidad[]")) else "pieza", i),
            )
        db.commit()
        flash(f"Cotización {folio} creada.", "ok")
        return redirect(url_for("detalle_cotizacion", quote_id=quote_id))

    return render_template(
        "nueva.html", perfil=perfil, catalogo=catalogo, clientes=clientes
    )


@app.route("/cotizaciones/<int:quote_id>")
def detalle_cotizacion(quote_id):
    db = get_db()
    quote = db.execute("SELECT * FROM quotes WHERE id = ?", (quote_id,)).fetchone()
    if quote is None:
        flash("Cotización no encontrada.", "error")
        return redirect(url_for("lista_cotizaciones"))
    items = db.execute(
        "SELECT * FROM quote_items WHERE quote_id = ? ORDER BY sort_order",
        (quote_id,),
    ).fetchall()
    perfil = db.execute("SELECT * FROM business_profile WHERE id = 1").fetchone()
    totales = totales_de_cotizacion(db, quote_id)
    texto_wa = (
        f"Hola {quote['client_name']}, te comparto la cotización {quote['folio']} "
        f"por un total de {formato_mxn(totales['total'])} MXN, vigente hasta "
        f"{quote['valid_until']}. ¡Quedo atento!"
    )
    wa_url = "https://wa.me/?text=" + urllib.parse.quote(texto_wa)
    return render_template(
        "detalle.html", quote=quote, items=items, perfil=perfil,
        totales=totales, estados=ESTADOS, wa_url=wa_url,
    )


@app.route("/cotizaciones/<int:quote_id>/estado", methods=["POST"])
def cambiar_estado(quote_id):
    db = get_db()
    estado = request.form.get("estado")
    if estado in ESTADOS:
        db.execute(
            "UPDATE quotes SET status = ?, updated_at = ? WHERE id = ?",
            (estado, ahora_ms(), quote_id),
        )
        db.commit()
        flash(f"Estado cambiado a {estado}.", "ok")
    return redirect(url_for("detalle_cotizacion", quote_id=quote_id))


@app.route("/cotizaciones/<int:quote_id>/duplicar", methods=["POST"])
def duplicar_cotizacion(quote_id):
    db = get_db()
    q = db.execute("SELECT * FROM quotes WHERE id = ?", (quote_id,)).fetchone()
    if q is None:
        return redirect(url_for("lista_cotizaciones"))
    folio = siguiente_folio(db)
    cur = db.execute(
        """INSERT INTO quotes
           (folio, title, client_id, client_name, client_company, client_phone,
            client_email, status, valid_until, discount_percent, tax_percent,
            notes, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, 'pendiente', ?, ?, ?, ?, ?, ?)""",
        (folio, q["title"], q["client_id"], q["client_name"], q["client_company"],
         q["client_phone"], q["client_email"], q["valid_until"],
         q["discount_percent"], q["tax_percent"], q["notes"], ahora_ms(), ahora_ms()),
    )
    nuevo_id = cur.lastrowid
    for it in db.execute(
        "SELECT * FROM quote_items WHERE quote_id = ? ORDER BY sort_order",
        (quote_id,),
    ).fetchall():
        db.execute(
            """INSERT INTO quote_items
               (quote_id, catalog_id, description, detail, quantity,
                unit_price, unit, sort_order)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (nuevo_id, it["catalog_id"], it["description"], it["detail"],
             it["quantity"], it["unit_price"], it["unit"], it["sort_order"]),
        )
    db.commit()
    flash(f"Duplicada como {folio}.", "ok")
    return redirect(url_for("detalle_cotizacion", quote_id=nuevo_id))


@app.route("/cotizaciones/<int:quote_id>/eliminar", methods=["POST"])
def eliminar_cotizacion(quote_id):
    db = get_db()
    db.execute("DELETE FROM quote_items WHERE quote_id = ?", (quote_id,))
    db.execute("DELETE FROM quotes WHERE id = ?", (quote_id,))
    db.commit()
    flash("Cotización eliminada.", "ok")
    return redirect(url_for("lista_cotizaciones"))


# ------------------------------------------------------------------------ PDF
def generar_pdf(db, quote_id):
    quote = db.execute("SELECT * FROM quotes WHERE id = ?", (quote_id,)).fetchone()
    items = db.execute(
        "SELECT * FROM quote_items WHERE quote_id = ? ORDER BY sort_order",
        (quote_id,),
    ).fetchall()
    perfil = db.execute("SELECT * FROM business_profile WHERE id = 1").fetchone()
    totales = totales_de_cotizacion(db, quote_id)

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 10, perfil["name"], new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    for linea in (perfil["tagline"], perfil["phone"], perfil["email"], perfil["address"]):
        if linea:
            pdf.cell(0, 5, linea, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 8, f"Cotización {quote['folio']}", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 5, f"Cliente: {quote['client_name']}", new_x="LMARGIN", new_y="NEXT")
    if quote["client_company"]:
        pdf.cell(0, 5, f"Empresa: {quote['client_company']}", new_x="LMARGIN", new_y="NEXT")
    if quote["client_phone"]:
        pdf.cell(0, 5, f"Teléfono: {quote['client_phone']}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 5, f"Vigencia hasta: {quote['valid_until']}  |  Estado: {quote['status']}",
             new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(95, 7, "Descripción", border=1)
    pdf.cell(20, 7, "Cant.", border=1)
    pdf.cell(35, 7, "Precio unit.", border=1)
    pdf.cell(35, 7, "Importe", border=1, new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    for it in items:
        importe = it["quantity"] * it["unit_price"]
        pdf.cell(95, 7, it["description"][:55], border=1)
        pdf.cell(20, 7, str(it["quantity"]), border=1)
        pdf.cell(35, 7, formato_mxn(it["unit_price"]), border=1)
        pdf.cell(35, 7, formato_mxn(importe), border=1, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    for etiqueta, valor in [
        ("Subtotal", totales["subtotal"]),
        (f"Descuento ({quote['discount_percent']}%)", -totales["descuento"]),
        (f"IVA ({quote['tax_percent']}%)", totales["iva"]),
    ]:
        pdf.cell(130, 6, etiqueta, align="R")
        pdf.cell(55, 6, formato_mxn(valor), align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(130, 8, "Total", align="R")
    pdf.cell(55, 8, formato_mxn(totales["total"]) + " MXN", align="R",
             new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    pdf.set_font("Helvetica", "", 9)
    pdf.multi_cell(0, 5, perfil["notes"])
    return bytes(pdf.output())


@app.route("/cotizaciones/<int:quote_id>/pdf")
def pdf_cotizacion(quote_id):
    db = get_db()
    quote = db.execute("SELECT folio FROM quotes WHERE id = ?", (quote_id,)).fetchone()
    if quote is None:
        flash("Cotización no encontrada.", "error")
        return redirect(url_for("lista_cotizaciones"))
    contenido = generar_pdf(db, quote_id)
    ruta = os.path.join(app.instance_path, f"{quote['folio']}.pdf")
    with open(ruta, "wb") as f:
        f.write(contenido)
    return send_file(ruta, as_attachment=True,
                     download_name=f"{quote['folio']}.pdf")


# ------------------------------------------------------- catálogo y clientes
@app.route("/catalogo", methods=["GET", "POST"])
def catalogo():
    db = get_db()
    if request.method == "POST":
        db.execute(
            "INSERT INTO catalog_items (name, description, price, unit, category, created_at)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (request.form["nombre"], request.form.get("descripcion", ""),
             float(request.form.get("precio", 0) or 0),
             request.form.get("unidad", "pieza"),
             request.form.get("categoria", "General"), ahora_ms()),
        )
        db.commit()
        flash("Producto agregado al catálogo.", "ok")
        return redirect(url_for("catalogo"))
    items = db.execute("SELECT * FROM catalog_items ORDER BY name").fetchall()
    return render_template("catalogo.html", items=items)


@app.route("/catalogo/<int:item_id>/eliminar", methods=["POST"])
def eliminar_catalogo(item_id):
    db = get_db()
    db.execute("DELETE FROM catalog_items WHERE id = ?", (item_id,))
    db.commit()
    return redirect(url_for("catalogo"))


@app.route("/clientes")
def clientes():
    db = get_db()
    lista = db.execute("SELECT * FROM clients ORDER BY name").fetchall()
    return render_template("clientes.html", clientes=lista)


@app.route("/config", methods=["GET", "POST"])
def config():
    db = get_db()
    if request.method == "POST":
        db.execute(
            """UPDATE business_profile SET
               name = ?, tagline = ?, owner = ?, phone = ?, email = ?,
               address = ?, rfc = ?, default_tax_percent = ?,
               default_validity_days = ?, notes = ?, updated_at = ?
               WHERE id = 1""",
            (request.form["nombre"], request.form.get("tagline", ""),
             request.form.get("owner", ""), request.form.get("telefono", ""),
             request.form.get("email", ""), request.form.get("direccion", ""),
             request.form.get("rfc", ""),
             float(request.form.get("iva", 16) or 16),
             int(request.form.get("vigencia", 15) or 15),
             request.form.get("notas", ""), ahora_ms()),
        )
        db.commit()
        flash("Datos del negocio guardados.", "ok")
        return redirect(url_for("config"))
    perfil = db.execute("SELECT * FROM business_profile WHERE id = 1").fetchone()
    return render_template("config.html", perfil=perfil)


@app.template_filter("mxn")
def filtro_mxn(valor):
    return formato_mxn(valor)


if __name__ == "__main__":
    app.run(debug=True)
