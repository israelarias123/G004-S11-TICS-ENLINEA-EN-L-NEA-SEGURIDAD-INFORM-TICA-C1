"""
Servidor web VULNERABLE del Laboratorio de Hacking Web (Aegis Corp).

Expone de forma INTENCIONAL tres vulnerabilidades con fines educativos:
  1. Inyección SQL (SQLi) en el formulario de inicio de sesión
     (bypass de autenticación por concatenación insegura de cadenas).
  2. Inyección SQL en el módulo de búsqueda, explotable con UNION para
     EXTRAER registros de otra tabla (exfiltración de credenciales).
  3. Cross-Site Scripting (XSS) reflejado en el muro de soporte
     (la entrada del usuario se renderiza sin sanitizar, con | safe).

Uso exclusivamente académico y en entornos controlados (127.0.0.1).
Ejecución:
    python app_vulnerable.py      ->  http://127.0.0.1:5000
"""

from flask import Flask, render_template, request, session, redirect, url_for
import sqlite3

DB_PATH = "lab_web.db"
PUERTO = 5000

app = Flask(__name__)
app.secret_key = "clave_secreta_para_sesiones_inseguras"


def init_db():
    """Crea las tablas y carga datos semilla si están vacías."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Tabla de usuarios (contraseñas en texto plano: INSEGURO a propósito).
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            password TEXT NOT NULL,
            rol TEXT NOT NULL
        )
        """
    )
    cursor.execute("SELECT COUNT(*) FROM usuarios")
    if cursor.fetchone()[0] == 0:
        cursor.executemany(
            "INSERT INTO usuarios (username, password, rol) VALUES (?, ?, ?)",
            [
                ("admin", "Secreto123", "Administrador Supremo"),
                ("juan", "123456", "Usuario Regular"),
            ],
        )

    # Tabla pública de empleados (lo que el buscador debería devolver).
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS empleados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            departamento TEXT NOT NULL,
            email TEXT NOT NULL
        )
        """
    )
    cursor.execute("SELECT COUNT(*) FROM empleados")
    if cursor.fetchone()[0] == 0:
        cursor.executemany(
            "INSERT INTO empleados (nombre, departamento, email) VALUES (?, ?, ?)",
            [
                ("Ana Torres", "Recursos Humanos", "ana.torres@aegiscorp.com"),
                ("Luis Méndez", "Tecnología", "luis.mendez@aegiscorp.com"),
                ("Carla Ruiz", "Finanzas", "carla.ruiz@aegiscorp.com"),
                ("Pedro Salas", "Soporte", "pedro.salas@aegiscorp.com"),
            ],
        )

    conn.commit()
    conn.close()


def autenticar(username, password):
    """
    VERSIÓN VULNERABLE.
    La entrada del usuario se incrusta directamente en la consulta SQL,
    permitiendo la inyección (p. ej. usuario = admin'--).
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    query = (
        f"SELECT * FROM usuarios WHERE username = '{username}' "
        f"AND password = '{password}'"
    )
    print(f"[SQL VULNERABLE · login] {query}")
    cursor.execute(query)

    user = cursor.fetchone()
    conn.close()
    return user


def buscar_empleados(termino):
    """
    VERSIÓN VULNERABLE.
    Concatena el término en la consulta, permitiendo inyección UNION para
    extraer datos de otras tablas (p. ej. credenciales de 'usuarios').
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    query = (
        "SELECT nombre, departamento, email FROM empleados "
        f"WHERE nombre LIKE '%{termino}%'"
    )
    print(f"[SQL VULNERABLE · buscar] {query}")
    cursor.execute(query)

    filas = cursor.fetchall()
    conn.close()
    return filas


@app.route("/", methods=["GET", "POST"])
def index():
    login_mensaje = None
    comentario_usuario = None
    resultados = None
    termino = ""

    if request.method == "POST":
        if "login_btn" in request.form:
            username = request.form.get("username", "")
            password = request.form.get("password", "")
            try:
                user = autenticar(username, password)
                if user:
                    session["user_id"] = user[0]
                    session["username"] = user[1]
                    session["rol"] = user[3]
                    return redirect(url_for("panel_privilegiado"))
                login_mensaje = "Credenciales incorrectas."
            except Exception as e:
                login_mensaje = f"Error en la consulta SQL: {e}"

        elif "comentario_btn" in request.form:
            # VULNERABLE: la entrada NO se sanitiza (se renderiza con | safe).
            comentario_usuario = request.form.get("comentario", "")

        elif "buscar_btn" in request.form:
            termino = request.form.get("termino", "")
            try:
                resultados = buscar_empleados(termino)
            except Exception as e:
                login_mensaje = f"Error en la consulta SQL: {e}"

    return render_template(
        "index.html",
        login_mensaje=login_mensaje,
        comentario_usuario=comentario_usuario,
        resultados=resultados,
        termino=termino,
        modo="VULNERABLE",
    )


@app.route("/panel")
def panel_privilegiado():
    if "username" not in session:
        return redirect(url_for("index"))

    info_confidencial = {
        "usuarios_sistema": [
            {"id": 1, "user": "admin", "pass_hash": "e10adc3949ba59abbe56e057f20f883e", "tarjeta": "4532-XXXX-XXXX-8912"},
            {"id": 2, "user": "juan", "pass_hash": "202cb962ac59075b964b07152d234b70", "tarjeta": "5412-XXXX-XXXX-3311"},
        ],
        "planes_estrategicos": "Proyecto Zeus: migración de infraestructura a la nube corporativa prevista para Q4. Claves de acceso root respaldadas en bóveda central.",
        "presupuesto": "$1,450,000 USD - Auditoría interna de seguridad aprobada.",
    }

    return render_template(
        "panel.html",
        username=session.get("username"),
        rol=session.get("rol"),
        info=info_confidencial,
    )


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


if __name__ == "__main__":
    init_db()
    print("=" * 60)
    print("  Aegis Corp Lab  |  MODO: VULNERABLE")
    print(f"  http://127.0.0.1:{PUERTO}")
    print("=" * 60)
    app.run(debug=True, port=PUERTO)
