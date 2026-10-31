# 🛡️ Laboratorio Práctico de Hacking Web con Flask y Python

Entorno web **controlado y educativo** desarrollado con **Python + Flask + SQLite** para
el estudio práctico de vulnerabilidades web, su explotación y su mitigación.

> ⚠️ **Aviso.** Este proyecto contiene vulnerabilidades **intencionales** con fines
> exclusivamente académicos. Debe ejecutarse únicamente en entornos locales y
> controlados (`127.0.0.1`). No lo despliegue en producción ni lo utilice contra
> sistemas de terceros sin autorización expresa.

---

## 🎯 Objetivos

1. **Simular una página web vulnerable:** login expuesto a **Inyección SQL (SQLi)**,
   un **buscador** explotable con **UNION** para extraer registros, y un muro de soporte
   expuesto a **Cross-Site Scripting (XSS) reflejado**.
2. **Explotar** las vulnerabilidades con un script de pruebas controladas que logra el
   **bypass de autenticación** y la **extracción de credenciales** (UNION).
3. **Mitigar y defender:** neutralizar los ataques con **consultas parametrizadas**
   (sentencias preparadas), **sanitización de salida** y **hash de contraseñas**.
4. **Módulos complementarios:** escaneo básico de red (puertos/servicios) y buenas
   prácticas de endurecimiento (*hardening*) en bases de datos.

---

## 📂 Estructura del proyecto

| Archivo | Descripción |
|---|---|
| `app_vulnerable.py` | Servidor web Flask **vulnerable** (SQLi en login + buscador, XSS). Puerto **5000**. |
| `app_seguro.py` | Servidor web Flask **seguro/mitigado** (consultas parametrizadas, escape XSS y hash de contraseñas). Puerto **5001**. |
| `ataque_sql_i.py` | Script de pruebas: bypass de login + extracción UNION (acepta la URL objetivo como argumento). |
| `escaneo_red.py` | Módulo de escaneo TCP de puertos y servicios (solo librería estándar). |
| `templates/index.html` | Interfaz principal: login + muro de soporte + buscador. |
| `templates/panel.html` | Panel confidencial mostrado tras un acceso exitoso. |
| `lab_web.db` | BD de la app **vulnerable** (texto plano). Se crea sola. |
| `lab_seguro.db` | BD de la app **segura** (contraseñas hasheadas). Se crea sola. |
| `requirements.txt` | Dependencias de Python. |
| `.gitignore` | Excluye BD, cachés y entornos virtuales del repositorio. |
| `MANUAL_USO.md` | Guía detallada paso a paso. |

---

## 🧰 Tecnologías

- **Backend:** Python 3, Flask 3, SQLite.
- **Frontend:** Tailwind CSS, **FontAwesome 6**, **SweetAlert2** e Inter (diseño limpio,
  minimalista, responsive y con bordes suaves).
- **Pruebas / red:** `requests`, `socket`, `threading`.

---

## 🚀 Instalación y ejecución rápida

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2a. Versión VULNERABLE  ->  http://127.0.0.1:5000
python app_vulnerable.py

# 2b. Versión SEGURA      ->  http://127.0.0.1:5001
python app_seguro.py
```

> Puedes levantar ambas a la vez (en terminales distintas) para comparar el
> comportamiento ante los mismos ataques.

### Credenciales legítimas de prueba

| Usuario | Contraseña | Rol |
|---|---|---|
| `admin` | `Secreto123` | Administrador Supremo |
| `juan` | `123456` | Usuario Regular |

---

## 💥 Demostración de las vulnerabilidades (SQLi)

Con `app_vulnerable.py` corriendo (puerto 5000):

**a) Bypass de login** — en el campo **Usuario** escribe `admin'--` (o `' OR '1'='1`);
se omite la contraseña y se accede al panel confidencial.

**b) Extracción de datos (UNION)** — en el **buscador de empleados** escribe:

```
' UNION SELECT username, password, rol FROM usuarios--
```

La respuesta añade a los empleados las **credenciales de la tabla `usuarios`**
(`admin / Secreto123`, `juan / 123456`).

Para automatizar ambos ataques:

```bash
python ataque_sql_i.py
```

---

## 🔒 Mitigación

La versión corregida está en `app_seguro.py` (no hay que modificar nada). Levántala y
repite el ataque apuntando a su puerto:

```bash
python app_seguro.py
python ataque_sql_i.py http://127.0.0.1:5001/
```

Defensas aplicadas:

- **Consultas parametrizadas** (login y buscador): la entrada se trata como **dato**, no
  como código SQL → el bypass y el UNION dejan de funcionar.
- **Escape de salida** (`markupsafe.escape`) → neutraliza el XSS reflejado.
- **Hash de contraseñas** (`werkzeug.security`, scrypt + salt) → aunque se robara la
  tabla, no se verían las claves en texto plano.

El script reportará `0/5` bypass y `0/2` extracciones.

---

## 🔍 Escaneo de red

```bash
python escaneo_red.py                  # 127.0.0.1, puertos comunes
python escaneo_red.py 127.0.0.1 1 1024 # rango de puertos personalizado
```

---

## 📖 Más información

Consulte **[MANUAL_USO.md](MANUAL_USO.md)** para la guía detallada, capturas del flujo,
explicación técnica de cada vulnerabilidad y recomendaciones de *hardening*.
