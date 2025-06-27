from flask import Flask, render_template, request, redirect, url_for, flash, g
import sqlite3
from database import get_db, query_db

app = Flask(__name__)
app.secret_key = "1201"


# Cerrar la conexión a la base de datos al finalizar
@app.teardown_appcontext
def close_db(error):
    if hasattr(g, "_database"):
        g._database.close()


#
@app.route("/")
def index():
    return render_template("base.html")


# Gestión de Materiales
@app.route("/materiales", methods=["GET", "POST"])
def materiales():
    db = get_db()

    if request.method == "POST":
        # Agregar nuevo material
        codigo = request.form["codigo"]
        nombre = request.form["nombre"]
        descripcion = request.form["descripcion"]
        unidad_medida = request.form["unidad_medida"]
        stock_minimo = request.form["stock_minimo"]

        try:
            db.execute(
                "INSERT INTO Materiales (codigo, nombre, descripcion, unidad_medida, stock_minimo) "
                "VALUES (?, ?, ?, ?, ?)",
                (codigo, nombre, descripcion, unidad_medida, stock_minimo),
            )
            db.commit()
            flash("Material agregado correctamente", "success")
        except sqlite3.IntegrityError:
            flash("Error: El código ya existe", "danger")

        return redirect(url_for("materiales"))

    # Listar materiales
    materiales = query_db("SELECT * FROM VistaStock")
    return render_template("materiales.html", materiales=materiales)


# Eliminar material
@app.route("/materiales/eliminar/<int:id_material>", methods=["POST"])
def eliminar_material(id_material):
    db = get_db()
    try:
        db.execute("DELETE FROM Materiales WHERE id_material = ?", (id_material,))
        db.commit()
        flash("Material eliminado correctamente", "success")
    except Exception as e:
        flash(f"Error al eliminar: {str(e)}", "danger")
    return redirect(url_for("materiales"))


# Editar material (mostrar formulario y actualizar)
@app.route("/materiales/editar/<int:id_material>", methods=["GET", "POST"])
def editar_material(id_material):
    db = get_db()
    if request.method == "POST":
        codigo = request.form["codigo"]
        nombre = request.form["nombre"]
        descripcion = request.form["descripcion"]
        unidad_medida = request.form["unidad_medida"]
        stock_minimo = request.form["stock_minimo"]
        try:
            db.execute(
                """
                UPDATE Materiales SET codigo=?, nombre=?, descripcion=?, unidad_medida=?, stock_minimo=?
                WHERE id_material=?
            """,
                (codigo, nombre, descripcion, unidad_medida, stock_minimo, id_material),
            )
            db.commit()
            flash("Material actualizado correctamente", "success")
            return redirect(url_for("materiales"))
        except Exception as e:
            flash(f"Error al actualizar: {str(e)}", "danger")
    # GET: mostrar datos actuales
    material = query_db(
        "SELECT * FROM Materiales WHERE id_material = ?", [id_material], one=True
    )
    return render_template("editar_material.html", material=material)


# Gestión de Movimientos
@app.route("/movimientos", methods=["GET", "POST"])
def movimientos():
    db = get_db()

    if request.method == "POST":
        # Registrar movimiento
        id_material = request.form["id_material"]
        tipo = request.form["tipo"]
        cantidad = float(request.form["cantidad"])
        responsable = request.form["responsable"]
        proyecto = request.form.get("proyecto", "")
        observaciones = request.form.get("observaciones", "")

        # Validar stock para salidas
        if tipo == "salida":
            stock = query_db(
                "SELECT stock_actual FROM Materiales WHERE id_material = ?",
                [id_material],
                one=True,
            )
            if stock and stock["stock_actual"] < cantidad:
                flash("Error: Stock insuficiente", "danger")
                return redirect(url_for("movimientos"))

        try:
            db.execute(
                "INSERT INTO Movimientos (id_material, tipo_movimiento, cantidad, responsable, proyecto_destino, observaciones) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (id_material, tipo, cantidad, responsable, proyecto, observaciones),
            )
            db.commit()
            flash("Movimiento registrado correctamente", "success")
        except Exception as e:
            flash(f"Error: {str(e)}", "danger")

        return redirect(url_for("movimientos"))

    # Listar movimientos y materiales disponibles
    movimientos = query_db("SELECT * FROM VistaHistorial LIMIT 500")
    materiales = query_db(
        "SELECT id_material, codigo, nombre FROM Materiales WHERE activo = 1"
    )
    return render_template(
        "movimientos.html", movimientos=movimientos, materiales=materiales
    )


# Reportes
@app.route("/reportes")
def reportes():
    # Materiales con stock bajo
    stock_bajo = query_db("SELECT * FROM VistaStock WHERE estado = 'REORDEN'")

    # Filtros
    fecha_inicio = request.args.get("fecha_inicio")
    fecha_fin = request.args.get("fecha_fin")
    tipo_movimiento = request.args.get("tipo_movimiento")
    material = request.args.get("material")

    # Base de la consulta
    query = "SELECT * FROM VistaHistorial WHERE 1=1"
    params = []

    # Filtro por fechas
    if fecha_inicio:
        query += " AND date(fecha_movimiento) >= date(?)"
        params.append(fecha_inicio)
    if fecha_fin:
        query += " AND date(fecha_movimiento) <= date(?)"
        params.append(fecha_fin)
    # Filtro por tipo
    if tipo_movimiento:
        query += " AND tipo_movimiento = ?"
        params.append(tipo_movimiento)
    # Filtro por material
    if material:
        query += " AND material = ?"
        params.append(material)

    query += " ORDER BY fecha_movimiento DESC LIMIT 500"
    movimientos_recientes = query_db(query, params)

    # Lista de materiales para el filtro
    materiales = query_db(
        "SELECT nombre FROM Materiales WHERE activo = 1 ORDER BY nombre"
    )

    return render_template(
        "reportes.html",
        stock_bajo=stock_bajo,
        movimientos_recientes=movimientos_recientes,
        materiales=materiales,
        request=request,
    )


if __name__ == "__main__":
    app.run(debug=True)
