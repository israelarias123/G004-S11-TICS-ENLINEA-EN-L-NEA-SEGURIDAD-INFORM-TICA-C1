# 📘 Manual de Uso — Laboratorio Práctico de Hacking Web

Guía detallada del entorno **Aegis Corp Lab** (Flask + SQLite). Este manual acompaña
al `README.md` y explica paso a paso cómo instalar, ejecutar, explotar y mitigar las
vulnerabilidades del laboratorio.

> ⚠️ Entorno con vulnerabilidades intencionales. Úselo **solo** en su propio equipo
> (`127.0.0.1`) y con fines educativos.

---

## 1. Requisitos previos

- **Python 3.9+** instalado (`python --version`).
- `pip` disponible.
- Un navegador web moderno.

---

## 2. Instalación

```bash
# (Opcional pero recomendado) entorno virtual
python -m venv venv
# Activar el entorno virtual
# Linux/macOS:
source venv/bin/activate        
# Windows: 
venv\Scripts\activate

# Dependencias
pip install -r requirements.txt
```

---

## 3. Puesta en marcha del servidor

El laboratorio tiene **dos aplicaciones independientes**:

| Aplicación | Comando | URL |
|---|---|---|
| **Vulnerable** | `python app_vulnerable.py` | http://127.0.0.1:5000 |
| **Segura** (mitigada) | `python app_seguro.py` | http://127.0.0.1:5001 |

Puede ejecutarlas por separado o ambas a la vez (en terminales distintas) para comparar.
Por ejemplo, la vulnerable:

```bash
python app_vulnerable.py
```

```
============================================================
  Aegis Corp Lab  |  MODO: VULNERABLE
  http://127.0.0.1:5000
============================================================
```

Abra la URL en el navegador; la cabecera muestra una insignia **Modo Vulnerable** (roja)
o **Modo Seguro** (verde). La base de datos `lab_web.db` se crea y se rellena
automáticamente en el primer arranque.

### Credenciales legítimas

| Usuario | Contraseña |
|---|---|
| `admin` | `Secreto123` |
| `juan`  | `123456` |

---

## 4. Vulnerabilidad 1 — Inyección SQL (bypass de login)

### 4.1 ¿Por qué es vulnerable?

En `app_vulnerable.py`, el servidor construye la consulta concatenando texto:

```python
query = f"SELECT * FROM usuarios WHERE username = '{username}' AND password = '{password}'"
```

La entrada del usuario se mezcla con el código SQL, de modo que un atacante puede alterar
la lógica de la consulta.

### 4.2 Explotación manual

En el formulario de login, **campo Usuario**, escriba uno de estos payloads (la
contraseña puede ser cualquier cosa):

| Payload en *Usuario* | Efecto |
|---|---|
| `' OR '1'='1` | La condición siempre es verdadera. |
| `admin'--` | Comenta el resto de la consulta (incluida la contraseña). |
| `' OR 1=1--` | Devuelve el primer registro de la tabla. |

Al enviar, SweetAlert2 confirma el acceso y se abre el **Panel Confidencial** con datos
ficticios (credenciales, hashes, presupuesto).

#### ¿Cómo queda la consulta?

Con usuario `admin'--` la consulta efectiva es:

```sql
SELECT * FROM usuarios WHERE username = 'admin'--' AND password = '...'
```

Todo lo que sigue a `--` es un comentario, por lo que la contraseña ya no se comprueba.

### 4.3 Explotación automatizada

Con el servidor corriendo, en otra terminal:

```bash
python ataque_sql_i.py
```

El script prueba varios payloads e informa cuántos lograron acceso. En modo vulnerable
el resultado será algo como `5/5 bypass logrados`.

### 4.4 Extracción de registros con UNION (buscador de empleados)

El buscador arma su consulta concatenando el término:

```python
query = "SELECT nombre, departamento, email FROM empleados WHERE nombre LIKE '%" + termino + "%'"
```

Como devuelve **3 columnas**, un ataque `UNION SELECT` con 3 columnas permite leer otra
tabla. En el campo **Directorio de Empleados** escriba:

```
' UNION SELECT username, password, rol FROM usuarios--
```

La tabla de resultados añadirá, junto a los empleados, las **credenciales** de la tabla
`usuarios` (`admin / Secreto123`, `juan / 123456`). Esto demuestra la *exfiltración de
datos*: el atacante no solo entra, también **roba información** de otras tablas.

El script `ataque_sql_i.py` automatiza también esta fase (`2/2 extracciones logradas`).

---

## 5. Vulnerabilidad 2 — XSS reflejado (muro de soporte)

### 5.1 ¿Por qué es vulnerable?

La plantilla imprime el comentario con el filtro `| safe`, desactivando el escape de
Jinja2. El contenido del usuario se inyecta tal cual en el HTML.

### 5.2 Explotación

En el campo **Reporte / Comentario** envíe, por ejemplo:

```html
<img src=x onerror="alert('XSS')">
```

o:

```html
<b style="color:red">texto inyectado</b>
```

El navegador interpreta y ejecuta el marcado en lugar de mostrarlo como texto.

---

## 6. Mitigación y defensa

La versión corregida ya está lista en **`app_seguro.py`** (no hay que modificar código).
Ejecútela en el puerto 5001:

```bash
python app_seguro.py
```

Usa su propia base de datos (`lab_seguro.db`) y aplica tres defensas:

### 6.1 Consultas parametrizadas (contra SQLi en login y buscador)

```python
# Login
cursor.execute("SELECT ... FROM usuarios WHERE username = ?", (username,))
# Buscador
cursor.execute("SELECT ... FROM empleados WHERE nombre LIKE ?", (f"%{termino}%",))
```

Los `?` son *placeholders*: el motor trata la entrada como **dato**, nunca como código
SQL. Tanto el bypass de login como el `UNION` del buscador dejan de funcionar.

### 6.2 Sanitización de salida (contra XSS)

```python
comentario_usuario = escape(comentario)   # markupsafe.escape
```

Los caracteres `<`, `>`, `"`, etc. se convierten en entidades HTML, por lo que el
navegador los muestra como texto y no los ejecuta.

### 6.3 Hash de contraseñas (defensa en profundidad)

```python
from werkzeug.security import generate_password_hash, check_password_hash
# Al guardar:   generate_password_hash("Secreto123")   -> 'scrypt:...'
# Al verificar: check_password_hash(hash_guardado, password)
```

Las contraseñas se almacenan **hasheadas con salt** (scrypt), no en texto plano. Aunque
un atacante extrajera la tabla, solo vería hashes irreversibles.

### 6.4 Verificación

Lance el ataque apuntando al puerto seguro:

```bash
python ataque_sql_i.py http://127.0.0.1:5001/
```

Debería reportar `0/5 bypass` y `0/2 extracciones`. El muro de soporte mostrará el
marcado como texto plano en lugar de ejecutarlo.

---

## 7. Módulo de escaneo de red

```bash
# Puertos comunes en el equipo local
python escaneo_red.py

# Host y rango de puertos específicos
python escaneo_red.py 127.0.0.1 1 1024
```

Reporta los puertos TCP abiertos y el servicio habitual asociado (p. ej. `5000 ->
Flask/HTTP-dev` cuando el laboratorio está en marcha).

> Escanee solo equipos propios o con autorización expresa.

---

## 8. Buenas prácticas de *hardening* en bases de datos

- **Siempre** usar consultas parametrizadas / ORM; nunca concatenar entradas.
- Aplicar **mínimo privilegio**: la cuenta de la aplicación no debe ser administradora.
- **Nunca** almacenar contraseñas en texto plano; usar *hashing* fuerte con *salt*
  (bcrypt, Argon2). *(En este laboratorio se guardan en claro solo para fines didácticos.)*
- Validar y normalizar entradas en el servidor (listas de permitidos).
- Desactivar el modo `debug` de Flask en cualquier entorno no local.
- Registrar y monitorizar intentos de acceso fallidos.
- Mantener copias de seguridad y aplicar parches del motor de base de datos.

---

## 9. Solución de problemas

| Problema | Solución |
|---|---|
| `ModuleNotFoundError: flask` | Ejecute `pip install -r requirements.txt`. |
| `No se pudo conectar` en el ataque | Asegúrese de que `python app_vulnerable.py` está corriendo. |
| El puerto 5000/5001 está ocupado | Cambie `PUERTO` al inicio de `app_vulnerable.py` o `app_seguro.py`. |
| El ataque falla contra la vulnerable | Verifique que apunta al puerto 5000 (`app_vulnerable.py`). |
| Quiere reiniciar los datos | Borre `lab_web.db` y vuelva a arrancar el servidor. |
