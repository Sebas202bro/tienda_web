from database.conexion import conectar

conn = conectar()
cursor = conn.cursor()

# Tabla Productos
cursor.execute("""
CREATE TABLE IF NOT EXISTS Productos (
    Id INTEGER PRIMARY KEY AUTOINCREMENT,
    Nombre TEXT NOT NULL,
    PrecioCompra REAL NOT NULL,
    PrecioVenta REAL NOT NULL,
    Stock INTEGER NOT NULL
)
""")

# Tabla Ventas
cursor.execute("""
CREATE TABLE IF NOT EXISTS Ventas (
    Id INTEGER PRIMARY KEY AUTOINCREMENT,
    Fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    Total REAL NOT NULL
)
""")

# Tabla DetalleVenta
cursor.execute("""
CREATE TABLE IF NOT EXISTS DetalleVenta (
    Id INTEGER PRIMARY KEY AUTOINCREMENT,
    VentaId INTEGER NOT NULL,
    ProductoId INTEGER NOT NULL,
    Cantidad INTEGER NOT NULL,
    Precio REAL NOT NULL,
    FOREIGN KEY (VentaId) REFERENCES Ventas(Id),
    FOREIGN KEY (ProductoId) REFERENCES Productos(Id)
)
""")

# Tabla Gastos
cursor.execute("""
CREATE TABLE IF NOT EXISTS Gastos (
    Id INTEGER PRIMARY KEY AUTOINCREMENT,
    Descripcion TEXT NOT NULL,
    Monto REAL NOT NULL,
    Fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

conn.commit()
conn.close()

print("Base de datos creada correctamente.")