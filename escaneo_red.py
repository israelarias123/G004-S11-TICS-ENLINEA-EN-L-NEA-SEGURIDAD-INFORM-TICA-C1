"""
Módulo complementario de escaneo básico de red para el laboratorio.
Realiza un escaneo TCP de puertos sobre un host indicado y reporta los
servicios comunes asociados a los puertos abiertos.

Usa solo la librería estándar de Python (socket, threading). Pensado para
ejecutarse contra el propio equipo (127.0.0.1) o hosts para los que se
cuente con autorización explícita. Escanear redes ajenas sin permiso puede
ser ilegal.

Ejecución:
    python escaneo_red.py                 # escanea 127.0.0.1, puertos comunes
    python escaneo_red.py 192.168.x.xx    # host específico
    python escaneo_red.py 127.0.0.1 1 1024  # host + rango de puertos
"""

import socket
import sys
import threading
from datetime import datetime
from queue import Queue

# Servicios habituales por puerto (referencia didáctica).
SERVICIOS = {
    21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP", 53: "DNS",
    80: "HTTP", 110: "POP3", 143: "IMAP", 443: "HTTPS", 445: "SMB",
    3306: "MySQL", 3389: "RDP", 5000: "Flask/HTTP-dev", 5432: "PostgreSQL",
    6379: "Redis", 8080: "HTTP-alt", 8443: "HTTPS-alt", 27017: "MongoDB",
}

# Puertos comunes que se escanean por defecto.
PUERTOS_COMUNES = sorted(SERVICIOS.keys())

TIMEOUT = 0.5          # segundos por intento de conexión
N_HILOS = 100          # hilos concurrentes

cola = Queue()
abiertos = []
lock = threading.Lock()


def escanear_puerto(host, puerto):
    """Devuelve True si el puerto TCP está abierto."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(TIMEOUT)
        return s.connect_ex((host, puerto)) == 0


def worker(host):
    while not cola.empty():
        puerto = cola.get()
        try:
            if escanear_puerto(host, puerto):
                servicio = SERVICIOS.get(puerto, "desconocido")
                with lock:
                    abiertos.append((puerto, servicio))
                    print(f"  [+] Puerto {puerto:>5}/tcp  ABIERTO   ->  {servicio}")
        finally:
            cola.task_done()


def resolver(host):
    """Resuelve el nombre de host a IP; termina el programa si falla."""
    try:
        return socket.gethostbyname(host)
    except socket.gaierror:
        print(f"[!] No se pudo resolver el host: {host}")
        sys.exit(1)


def escanear(host, puertos):
    ip = resolver(host)
    print("=" * 60)
    print(f"  ESCANEO DE RED  -  objetivo: {host} ({ip})")
    print(f"  Puertos a probar: {len(puertos)}")
    print(f"  Inicio: {datetime.now():%Y-%m-%d %H:%M:%S}")
    print("=" * 60)

    for p in puertos:
        cola.put(p)

    hilos = []
    for _ in range(min(N_HILOS, len(puertos))):
        t = threading.Thread(target=worker, args=(ip,), daemon=True)
        t.start()
        hilos.append(t)

    cola.join()

    print("-" * 60)
    if abiertos:
        print(f"  {len(abiertos)} puerto(s) abierto(s):")
        for puerto, servicio in sorted(abiertos):
            print(f"    - {puerto}/tcp  ({servicio})")
    else:
        print("  No se encontraron puertos abiertos en el rango indicado.")
    print("=" * 60)


def parsear_args():
    """host [puerto_inicio puerto_fin] desde la línea de comandos."""
    host = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    if len(sys.argv) >= 4:
        inicio, fin = int(sys.argv[2]), int(sys.argv[3])
        puertos = list(range(inicio, fin + 1))
    else:
        puertos = PUERTOS_COMUNES
    return host, puertos


if __name__ == "__main__":
    objetivo, lista_puertos = parsear_args()
    try:
        escanear(objetivo, lista_puertos)
    except KeyboardInterrupt:
        print("\n[!] Escaneo interrumpido por el usuario.")
