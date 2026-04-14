from database.conexion import conectar

conexion = conectar()
cursor = conexion.cursor()

# 📦 PRODUCTOS
cursor.execute("""
CREATE TABLE IF NOT EXISTS Productos (
    Id INTEGER PRIMARY KEY AUTOINCREMENT,
    Nombre TEXT,
    PrecioCompra REAL,
    PrecioVenta REAL,
    Stock INTEGER
)
""")

# 🛒 VENTAS
cursor.execute("""
CREATE TABLE IF NOT EXISTS Ventas (
    Id INTEGER PRIMARY KEY AUTOINCREMENT,
    Total REAL,
    Fecha DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

# 📄 DETALLE
cursor.execute("""
CREATE TABLE IF NOT EXISTS DetalleVenta (
    Id INTEGER PRIMARY KEY AUTOINCREMENT,
    VentaId INTEGER,
    ProductoId INTEGER,
    Cantidad INTEGER
)
""")

# 💸 GASTOS
cursor.execute("""
CREATE TABLE IF NOT EXISTS Gastos (
    Id INTEGER PRIMARY KEY AUTOINCREMENT,
    Descripcion TEXT,
    Monto REAL,
    Fecha DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

conexion.commit()
conexion.close()

print("✅ Base de datos creada correctamente")