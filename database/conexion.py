import sqlite3

def conectar():
    conexion = sqlite3.connect("tienda.db")
    conexion.row_factory = sqlite3.Row  # 🔥 IMPORTANTE (para usar p.Nombre)
    return conexion