"""
Servidor web SEGURO (mitigado) del Laboratorio de Hacking Web (Aegis Corp).

Es la versión corregida de `app_vulnerable.py`. Aplica tres defensas:
  1. Consultas parametrizadas (sentencias preparadas) contra la Inyección SQL
     en el login y en el buscador (neutraliza el bypass y el UNION).
  2. Escape/sanitización de la salida contra el XSS reflejado.
  3. Almacenamiento de contraseñas con HASH + salt (werkzeug), en lugar de
     texto plano: aunque un atacante robara la tabla, no vería las claves.

Usa su PROPIA base de datos (lab_seguro.db) con contraseñas hasheadas, para
no interferir con la base en texto plano de la versión vulnerable.

Uso exclusivamente académico y en entornos controlados (127.0.0.1).
Ejecución:
    python app_seguro.py          ->  http://127.0.0.1:5001
"""

from flask import Flask, render_template, request, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from markupsafe import escape
import sqlite3

DB_PATH = "lab_seguro.db"
PUERTO = 5001

app = Flask(__name__)
app.secret_key = "clave_secreta_para_sesiones_seguras"


def init_db():
    """Crea las tablas y carga datos semilla (contraseñas hasheadas)."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

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
        # Las contraseñas se guardan HASHEADAS (nunca en texto plano).
        cursor.executemany(
            "INSERT INTO usuarios (username, password, rol) VALUES (?, ?, ?)",
            [
                ("admin", generate_password_hash("Secreto123"), "Administrador Supremo"),
                ("juan", generate_password_hash("123456"), "Usuario Regular"),
            ],
        )

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
    VERSIÓN SEGURA.
    1) Consulta parametrizada para obtener al usuario por su nombre (los '?'
       hacen que la entrada sea tratada como DATO, no como código SQL).
    2) Verificación del hash de la contraseña con check_password_hash.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    query = "SELECT id, username, password, rol FROM usuarios WHERE username = ?"
    print(f"[SQL SEGURO · login] {query}  params=({username!r},)")
    cursor.execute(query, (username,))
    fila = cursor.fetchone()
    conn.close()

    if fila and check_password_hash(fila[2], password):
        return fila
    return None


def buscar_empleados(termino):
    """
    VERSIÓN SEGURA.
    El término viaja como parámetro; el comodín LIKE se aplica al valor, no a
    la consulta. Un payload UNION se busca literalmente y no devuelve nada.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    query = "SELECT nombre, departamento, email FROM empleados WHERE nombre LIKE ?"
    print(f"[SQL SEGURO · buscar] {query}  params=('%{termino}%',)")
    cursor.execute(query, (f"%{termino}%",))

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
            # SEGURO: se escapan los caracteres HTML para mostrarlos como texto.
            comentario_usuario = escape(request.form.get("comentario", ""))

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
        modo="SEGURO",
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
    print("  Aegis Corp Lab  |  MODO: SEGURO (mitigado)")
    print(f"  http://127.0.0.1:{PUERTO}")
    print("=" * 60)
    app.run(debug=True, port=PUERTO)
