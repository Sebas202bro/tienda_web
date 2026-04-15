import pyodbc

def conectar():
    try:
        conn = pyodbc.connect(
            "DRIVER={ODBC Driver 17 for SQL Server};"
            "SERVER=localhost;"
            "DATABASE=TiendaDB;"
            "Trusted_Connection=yes;",
            timeout=5
        )
        return conn
    except Exception as e:
        print("❌ ERROR CONECTANDO A SQL SERVER:", e)
        return None