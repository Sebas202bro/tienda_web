from flask import Flask, render_template, request, redirect, session, jsonify
from database.conexion import conectar

app = Flask(__name__)
app.secret_key = "secreto"

USUARIO = "admin"
PASSWORD = "1234"

# ---------------- UTIL ----------------
def obtener_productos():
    conn = conectar()
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
    cursor = conn.cursor()

    if busqueda:
        cursor.execute("SELECT * FROM Productos WHERE Nombre LIKE ?", ('%' + busqueda + '%',))
    else:
        cursor.execute("SELECT * FROM Productos")

    productos = cursor.fetchall()
    conn.close()

    return render_template('index.html', productos=productos, busqueda=busqueda)

# ---------------- CRUD ----------------
@app.route('/agregar', methods=['POST'])
def agregar():
    conn = conectar()
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
    cursor = conn.cursor()

    cursor.execute("DELETE FROM Productos WHERE Id = ?", (id,))

    conn.commit()
    conn.close()
    return redirect('/')


@app.route('/editar/<int:id>')
def editar(id):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM Productos WHERE Id = ?", (id,))
    producto = cursor.fetchone()

    conn.close()
    return render_template('editar.html', producto=producto)


@app.route('/actualizar/<int:id>', methods=['POST'])
def actualizar(id):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE Productos
        SET Nombre=?, PrecioCompra=?, PrecioVenta=?, Stock=?
        WHERE Id=?
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
    cursor = conn.cursor()

    cursor.execute("SELECT SUM(Total) FROM Ventas")
    total_ventas = cursor.fetchone()[0] or 0

    cursor.execute("SELECT COUNT(*) FROM Ventas")
    num_ventas = cursor.fetchone()[0] or 0

    cursor.execute("SELECT SUM(Cantidad) FROM DetalleVenta")
    productos_vendidos = cursor.fetchone()[0] or 0

    cursor.execute("""
        SELECT SUM((p.PrecioVenta - p.PrecioCompra) * d.Cantidad)
        FROM DetalleVenta d
        JOIN Productos p ON p.Id = d.ProductoId
    """)
    ganancia_total = cursor.fetchone()[0] or 0

    cursor.execute("SELECT SUM(Monto) FROM Gastos")
    total_gastos = cursor.fetchone()[0] or 0

    ganancia_neta = ganancia_total - total_gastos

    cursor.execute("""
        SELECT DATE(v.Fecha),
               SUM((p.PrecioVenta - p.PrecioCompra) * d.Cantidad)
        FROM Ventas v
        JOIN DetalleVenta d ON v.Id = d.VentaId
        JOIN Productos p ON p.Id = d.ProductoId
        GROUP BY DATE(v.Fecha)
        ORDER BY DATE(v.Fecha)
    """)

    datos = cursor.fetchall()
    fechas = [d[0] for d in datos]
    totales = [float(d[1] or 0) for d in datos]

    cursor.execute("""
        SELECT p.Nombre,
               SUM((p.PrecioVenta - p.PrecioCompra) * d.Cantidad)
        FROM DetalleVenta d
        JOIN Productos p ON p.Id = d.ProductoId
        GROUP BY p.Nombre
        ORDER BY 2 DESC
    """)

    productos_top = cursor.fetchall()

    conn.close()

    return render_template(
        "dashboard.html",
        total_ventas=total_ventas,
        num_ventas=num_ventas,
        productos_vendidos=productos_vendidos,
        ganancia_total=ganancia_total,
        total_gastos=total_gastos,
        ganancia_neta=ganancia_neta,
        fechas=fechas,
        totales=totales,
        productos_top=productos_top
    )

# ---------------- VENTAS ----------------
@app.route('/ventas')
def ventas():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM Productos")
    productos = cursor.fetchall()
    conn.close()

    if 'carrito' not in session:
        session['carrito'] = []

    return render_template("ventas.html", productos=productos, carrito=session['carrito'])


@app.route('/obtener_producto/<int:id>')
def obtener_producto(id):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("SELECT Nombre, PrecioVenta FROM Productos WHERE Id=?", (id,))
    p = cursor.fetchone()

    conn.close()

    return jsonify({
        "nombre": p[0],
        "precio": float(p[1])
    })


# ---------------- CARRITO ----------------
@app.route('/agregar_carrito', methods=['POST'])
def agregar_carrito():
    id = int(request.form['id'])
    cantidad = int(request.form['cantidad'])

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM Productos WHERE Id=?", (id,))
    p = cursor.fetchone()
    conn.close()

    carrito = session.get('carrito', [])

    for item in carrito:
        if item['id'] == id:
            item['cantidad'] += cantidad
            break
    else:
        carrito.append({
            "id": id,
            "nombre": p.Nombre,
            "precio": p.PrecioVenta,
            "cantidad": cantidad
        })

    session['carrito'] = carrito
    return redirect('/ventas')


@app.route('/eliminar_carrito/<int:index>')
def eliminar_carrito(index):
    carrito = session.get('carrito', [])

    if 0 <= index < len(carrito):
        carrito.pop(index)

    session['carrito'] = carrito
    return redirect('/ventas')


@app.route('/guardar_venta')
def guardar_venta():
    carrito = session.get('carrito', [])

    if not carrito:
        return redirect('/ventas')

    conn = conectar()
    cursor = conn.cursor()

    total = sum(i['precio'] * i['cantidad'] for i in carrito)

    cursor.execute("INSERT INTO Ventas (Total) VALUES (?)", (total,))
    venta_id = cursor.lastrowid

    for i in carrito:
        cursor.execute("""
            INSERT INTO DetalleVenta (VentaId, ProductoId, Cantidad, Precio)
            VALUES (?, ?, ?, ?)
        """, (venta_id, i['id'], i['cantidad'], i['precio']))

        cursor.execute("""
            UPDATE Productos
            SET Stock = Stock - ?
            WHERE Id = ?
        """, (i['cantidad'], i['id']))

    conn.commit()
    conn.close()

    session['carrito'] = []
    return redirect('/ventas')

# ---------------- GASTOS ----------------
@app.route('/gastos')
def gastos():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM Gastos ORDER BY Fecha DESC")
    lista = cursor.fetchall()

    cursor.execute("SELECT SUM(Monto) FROM Gastos")
    total = cursor.fetchone()[0] or 0

    conn.close()

    return render_template("gastos.html", gastos=lista, total_gastos=total)


@app.route('/agregar_gasto', methods=['POST'])
def agregar_gasto():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO Gastos (Descripcion, Monto) VALUES (?, ?)",
        (request.form['descripcion'], request.form['monto'])
    )

    conn.commit()
    conn.close()

    return redirect('/gastos')

# ---------------- HISTORIAL ----------------
@app.route('/historial')
def historial():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM Ventas ORDER BY Fecha DESC")
    ventas = cursor.fetchall()

    conn.close()
    return render_template("historial.html", ventas=ventas)


@app.route('/detalle/<int:id>')
def detalle(id):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT p.Nombre, d.Cantidad, d.Precio
        FROM DetalleVenta d
        JOIN Productos p ON p.Id = d.ProductoId
        WHERE d.VentaId=?
    """, (id,))

    detalles = cursor.fetchall()
    conn.close()

    total = sum(d[1] * d[2] for d in detalles)

    return render_template("detalle.html", detalles=detalles, venta_id=id, total=total)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
