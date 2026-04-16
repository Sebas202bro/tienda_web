from flask import Flask, render_template, request, redirect, session, jsonify
from database.conexion import conectar

app = Flask(__name__)
app.secret_key = "secreto"
app.config['SESSION_PERMANENT'] = False

from database.conexion import conectar

def init_db():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Productos (
        Id INTEGER PRIMARY KEY AUTOINCREMENT,
        Nombre TEXT,
        PrecioCompra REAL,
        PrecioVenta REAL,
        Stock INTEGER
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Ventas (
        Id INTEGER PRIMARY KEY AUTOINCREMENT,
        Fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        Total REAL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS DetalleVenta (
        Id INTEGER PRIMARY KEY AUTOINCREMENT,
        VentaId INTEGER,
        ProductoId INTEGER,
        Cantidad INTEGER,
        Precio REAL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Gastos (
        Id INTEGER PRIMARY KEY AUTOINCREMENT,
        Descripcion TEXT,
        Monto REAL,
        Fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()

init_db()

USUARIO = "admin"
PASSWORD = "1234"


# ---------------- UTIL ----------------
def obtener_productos():
    conn = conectar()
    if conn is None:
        return []

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Productos")
    data = cursor.fetchall()
    conn.close()
    return data


# ---------------- LOGIN ----------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = request.form['usuario']
        password = request.form['password']

        if user == USUARIO and password == PASSWORD:
            session['usuario'] = user
            return redirect('/')
        return render_template('login.html', error="Datos incorrectos")

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')


@app.before_request
def proteger():
    rutas_libres = ['login', 'static']
    if request.endpoint not in rutas_libres and 'usuario' not in session:
        return redirect('/login')


# ---------------- INVENTARIO ----------------
@app.route('/')
def index():
    busqueda = request.args.get('q', '')

    conn = conectar()
    if conn is None:
        return "Error de conexión con SQL Server"

    cursor = conn.cursor()

    if busqueda:
        cursor.execute("SELECT * FROM Productos WHERE Nombre LIKE ?", ('%' + busqueda + '%',))
    else:
        cursor.execute("SELECT * FROM Productos")

    productos = cursor.fetchall()
    conn.close()

    return render_template('index.html', productos=productos, busqueda=busqueda)


# ---------------- CRUD PRODUCTOS ----------------
@app.route('/agregar', methods=['POST'])
def agregar():
    conn = conectar()
    if conn is None:
        return "Error de conexión con SQL Server"

    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO Productos (Nombre, PrecioCompra, PrecioVenta, Stock)
        VALUES (?, ?, ?, ?)
    """, (
        request.form['nombre'],
        request.form['precio_compra'],
        request.form['precio_venta'],
        request.form['stock']
    ))

    conn.commit()
    conn.close()
    return redirect('/')


@app.route('/eliminar/<int:id>')
def eliminar(id):
    conn = conectar()
    if conn is None:
        return "Error de conexión con SQL Server"

    cursor = conn.cursor()
    cursor.execute("DELETE FROM Productos WHERE Id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect('/')


@app.route('/editar/<int:id>')
def editar(id):
    conn = conectar()
    if conn is None:
        return "Error de conexión con SQL Server"

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Productos WHERE Id = ?", (id,))
    producto = cursor.fetchone()
    conn.close()

    if not producto:
        return redirect('/')

    return render_template('editar.html', producto=producto)


@app.route('/actualizar/<int:id>', methods=['POST'])
def actualizar(id):
    conn = conectar()
    if conn is None:
        return "Error de conexión con SQL Server"

    cursor = conn.cursor()
    cursor.execute("""
        UPDATE Productos
        SET Nombre = ?, PrecioCompra = ?, PrecioVenta = ?, Stock = ?
        WHERE Id = ?
    """, (
        request.form['nombre'],
        request.form['precio_compra'],
        request.form['precio_venta'],
        request.form['stock'],
        id
    ))

    conn.commit()
    conn.close()
    return redirect('/')


# ---------------- DASHBOARD ----------------
@app.route('/dashboard')
def dashboard():
    conn = conectar()
    if conn is None:
        return "Error de conexión con SQL Server"

    cursor = conn.cursor()

    fecha_inicio = request.args.get('inicio', '').strip()
    fecha_fin = request.args.get('fin', '').strip()

    filtro_ventas = ""
    filtro_detalle = ""
    params_ventas = []
    params_detalle = []

    if fecha_inicio and fecha_fin:
        filtro_ventas = " WHERE CONVERT(date, Fecha) BETWEEN ? AND ?"
        filtro_detalle = " WHERE CONVERT(date, v.Fecha) BETWEEN ? AND ?"
        params_ventas = [fecha_inicio, fecha_fin]
        params_detalle = [fecha_inicio, fecha_fin]
    elif fecha_inicio:
        filtro_ventas = " WHERE CONVERT(date, Fecha) >= ?"
        filtro_detalle = " WHERE CONVERT(date, v.Fecha) >= ?"
        params_ventas = [fecha_inicio]
        params_detalle = [fecha_inicio]
    elif fecha_fin:
        filtro_ventas = " WHERE CONVERT(date, Fecha) <= ?"
        filtro_detalle = " WHERE CONVERT(date, v.Fecha) <= ?"
        params_ventas = [fecha_fin]
        params_detalle = [fecha_fin]

    cursor.execute(f"SELECT ISNULL(SUM(Total), 0) FROM Ventas{filtro_ventas}", params_ventas)
    total_ventas = cursor.fetchone()[0]

    cursor.execute(f"SELECT COUNT(*) FROM Ventas{filtro_ventas}", params_ventas)
    num_ventas = cursor.fetchone()[0]

    cursor.execute(f"""
        SELECT ISNULL(SUM(d.Cantidad), 0)
        FROM DetalleVenta d
        INNER JOIN Ventas v ON v.Id = d.VentaId
        {filtro_detalle}
    """, params_detalle)
    productos_vendidos = cursor.fetchone()[0]

    cursor.execute(f"""
        SELECT ISNULL(SUM((p.PrecioVenta - p.PrecioCompra) * d.Cantidad), 0)
        FROM DetalleVenta d
        INNER JOIN Productos p ON p.Id = d.ProductoId
        INNER JOIN Ventas v ON v.Id = d.VentaId
        {filtro_detalle}
    """, params_detalle)
    ganancia_total = cursor.fetchone()[0]

    cursor.execute(f"SELECT ISNULL(SUM(Monto), 0) FROM Gastos{filtro_ventas}", params_ventas)
    total_gastos = cursor.fetchone()[0]

    ganancia_neta = ganancia_total - total_gastos

    cursor.execute(f"""
        SELECT CONVERT(date, v.Fecha) AS Fecha,
               SUM((p.PrecioVenta - p.PrecioCompra) * d.Cantidad) AS Ganancia
        FROM Ventas v
        INNER JOIN DetalleVenta d ON v.Id = d.VentaId
        INNER JOIN Productos p ON p.Id = d.ProductoId
        {filtro_detalle}
        GROUP BY CONVERT(date, v.Fecha)
        ORDER BY CONVERT(date, v.Fecha)
    """, params_detalle)
    datos = cursor.fetchall()

    fechas = [str(d[0]) for d in datos]
    totales = [float(d[1] or 0) for d in datos]

    cursor.execute(f"""
        SELECT p.Nombre,
               SUM((p.PrecioVenta - p.PrecioCompra) * d.Cantidad) AS Ganancia
        FROM DetalleVenta d
        INNER JOIN Productos p ON p.Id = d.ProductoId
        INNER JOIN Ventas v ON v.Id = d.VentaId
        {filtro_detalle}
        GROUP BY p.Nombre
        ORDER BY Ganancia DESC
    """, params_detalle)
    productos_top = cursor.fetchall()

    conn.close()

    return render_template(
        'dashboard.html',
        total_ventas=total_ventas,
        num_ventas=num_ventas,
        productos_vendidos=productos_vendidos,
        ganancia_total=ganancia_total,
        total_gastos=total_gastos,
        ganancia_neta=ganancia_neta,
        fechas=fechas,
        totales=totales,
        productos_top=productos_top,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin
    )


# ---------------- VENTAS ----------------
@app.route('/ventas')
def ventas():
    conn = conectar()
    if conn is None:
        return "Error de conexión con SQL Server"

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Productos")
    productos = cursor.fetchall()
    conn.close()

    if 'carrito' not in session:
        session['carrito'] = []

    return render_template("ventas.html", productos=productos, carrito=session['carrito'], error=None)


@app.route('/obtener_producto/<int:id>')
def obtener_producto(id):
    conn = conectar()
    if conn is None:
        return jsonify({"nombre": "", "precio": 0})

    cursor = conn.cursor()
    cursor.execute("SELECT Nombre, PrecioVenta FROM Productos WHERE Id = ?", (id,))
    p = cursor.fetchone()
    conn.close()

    if not p:
        return jsonify({"nombre": "", "precio": 0})

    return jsonify({
        "nombre": p[0],
        "precio": float(p[1])
    })


# ---------------- CARRITO ----------------
@app.route('/agregar_carrito', methods=['POST'])
def agregar_carrito():
    try:
        id_producto = int(request.form['id'])
        cantidad = int(request.form['cantidad'])
    except (ValueError, TypeError):
        return redirect('/ventas')

    if cantidad <= 0:
        productos = obtener_productos()
        return render_template(
            "ventas.html",
            productos=productos,
            carrito=session.get('carrito', []),
            error="La cantidad debe ser mayor a 0"
        )

    conn = conectar()
    if conn is None:
        return "Error de conexión con SQL Server"

    cursor = conn.cursor()
    cursor.execute("SELECT Id, Nombre, PrecioVenta, Stock FROM Productos WHERE Id = ?", (id_producto,))
    p = cursor.fetchone()
    conn.close()

    if not p:
        return redirect('/ventas')

    if cantidad > p[3]:
        productos = obtener_productos()
        return render_template(
            "ventas.html",
            productos=productos,
            carrito=session.get('carrito', []),
            error="Stock insuficiente"
        )

    carrito = session.get('carrito', [])

    for item in carrito:
        if item['id'] == id_producto:
            if item['cantidad'] + cantidad > p[3]:
                productos = obtener_productos()
                return render_template(
                    "ventas.html",
                    productos=productos,
                    carrito=carrito,
                    error="Stock insuficiente"
                )
            item['cantidad'] += cantidad
            session['carrito'] = carrito
            session.modified = True
            return redirect('/ventas')

    carrito.append({
        "id": int(p[0]),
        "nombre": p[1],
        "precio": float(p[2]),
        "cantidad": cantidad
    })

    session['carrito'] = carrito
    session.modified = True
    return redirect('/ventas')


@app.route('/eliminar_carrito/<int:id_producto>')
def eliminar_carrito(id_producto):
    carrito = session.get('carrito', [])
    carrito = [item for item in carrito if item['id'] != id_producto]
    session['carrito'] = carrito
    session.modified = True
    return redirect('/ventas')


@app.route('/actualizar_carrito/<int:id_producto>/<accion>')
def actualizar_carrito(id_producto, accion):
    carrito = session.get('carrito', [])

    conn = conectar()
    if conn is None:
        return redirect('/ventas')

    cursor = conn.cursor()
    cursor.execute("SELECT Stock FROM Productos WHERE Id = ?", (id_producto,))
    producto = cursor.fetchone()
    conn.close()

    stock_actual = producto[0] if producto else 0

    for item in carrito:
        if item['id'] == id_producto:
            if accion == 'sumar':
                if item['cantidad'] < stock_actual:
                    item['cantidad'] += 1
            elif accion == 'restar':
                item['cantidad'] -= 1
                if item['cantidad'] <= 0:
                    carrito.remove(item)
            break

    session['carrito'] = carrito
    session.modified = True
    return redirect('/ventas')


# ---------------- GUARDAR VENTA ----------------
@app.route('/guardar_venta')
def guardar_venta():
    carrito = session.get('carrito', [])

    if not carrito:
        return redirect('/ventas')

    conn = conectar()
    if conn is None:
        return "Error de conexión con SQL Server"

    cursor = conn.cursor()

    for item in carrito:
        cursor.execute("SELECT Stock FROM Productos WHERE Id = ?", (item['id'],))
        producto = cursor.fetchone()

        if not producto or item['cantidad'] > producto[0]:
            conn.close()
            productos = obtener_productos()
            return render_template(
                "ventas.html",
                productos=productos,
                carrito=carrito,
                error=f"Stock insuficiente para {item['nombre']}"
            )

    total = sum(item['precio'] * item['cantidad'] for item in carrito)

    cursor.execute("INSERT INTO Ventas (Total) OUTPUT INSERTED.Id VALUES (?)", (total,))
    venta_id = cursor.fetchone()[0]

    for item in carrito:
        cursor.execute("""
            INSERT INTO DetalleVenta (VentaId, ProductoId, Cantidad, Precio)
            VALUES (?, ?, ?, ?)
        """, (venta_id, item['id'], item['cantidad'], item['precio']))

        cursor.execute("""
            UPDATE Productos
            SET Stock = Stock - ?
            WHERE Id = ?
        """, (item['cantidad'], item['id']))

    conn.commit()
    conn.close()

    session['carrito'] = []
    session.modified = True
    return redirect('/ventas')


# ---------------- GASTOS ----------------
@app.route('/gastos')
def gastos():
    conn = conectar()
    if conn is None:
        return "Error de conexión con SQL Server"

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Gastos ORDER BY Fecha DESC")
    lista = cursor.fetchall()

    cursor.execute("SELECT ISNULL(SUM(Monto), 0) FROM Gastos")
    total = cursor.fetchone()[0]

    conn.close()
    return render_template("gastos.html", gastos=lista, total_gastos=total)


@app.route('/agregar_gasto', methods=['POST'])
def agregar_gasto():
    conn = conectar()
    if conn is None:
        return "Error de conexión con SQL Server"

    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO Gastos (Descripcion, Monto)
        VALUES (?, ?)
    """, (
        request.form['descripcion'],
        request.form['monto']
    ))

    conn.commit()
    conn.close()
    return redirect('/gastos')


# ---------------- HISTORIAL ----------------
@app.route('/historial')
def historial():
    conn = conectar()
    if conn is None:
        return "Error de conexión con SQL Server"

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Ventas ORDER BY Fecha DESC")
    ventas = cursor.fetchall()
    conn.close()

    return render_template("historial.html", ventas=ventas)


@app.route('/detalle/<int:id>')
def detalle(id):
    conn = conectar()
    if conn is None:
        return "Error de conexión con SQL Server"

    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.Nombre, d.Cantidad, d.Precio
        FROM DetalleVenta d
        INNER JOIN Productos p ON p.Id = d.ProductoId
        WHERE d.VentaId = ?
    """, (id,))
    detalles = cursor.fetchall()
    conn.close()

    total = sum(d[1] * d[2] for d in detalles)

    return render_template("detalle.html", detalles=detalles, venta_id=id, total=total)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)