"""
Simula usuarios concurrentes intentando reservar entradas y mide latencia,
throughput y tasa de éxito/rechazo. Cubre el requisito 7 del caso (medir
latencia y rendimiento de un conjunto común de operaciones).

Uso:
    python -m src.load_test --usuarios 50000 --intentos 100000 --hilos 50

Nota: primero corran src/setup_inventory.py para tener inventario cargado.
"""
import argparse
import random
import statistics
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.config import get_redis_connection
from src.reservation_service import ReservationService
from src.setup_inventory import EVENTOS

SEMILLA = 42


def intento_de_reserva(servicio, usuario_id):
    evento = random.choice(EVENTOS)
    zona = random.choice(list(evento["zonas"].keys()))
    cantidad = random.randint(1, 4)

    inicio = time.perf_counter()
    try:
        reserva_id = servicio.crear_reserva(usuario_id, evento["id"], zona, cantidad)
        exito = reserva_id is not None
    except Exception:
        exito = False
    duracion_ms = (time.perf_counter() - inicio) * 1000
    return exito, duracion_ms


def ejecutar(usuarios: int, intentos: int, hilos: int = 50):
    random.seed(SEMILLA)
    r = get_redis_connection()
    servicio = ReservationService(r)

    latencias = []
    exitosos = 0
    rechazados = 0

    def tarea(_i):
        usuario_id = f"u{random.randint(1, usuarios)}"
        return intento_de_reserva(servicio, usuario_id)

    inicio_total = time.perf_counter()
    with ThreadPoolExecutor(max_workers=hilos) as executor:
        futuros = [executor.submit(tarea, i) for i in range(intentos)]
        for futuro in as_completed(futuros):
            exito, duracion_ms = futuro.result()
            latencias.append(duracion_ms)
            if exito:
                exitosos += 1
            else:
                rechazados += 1
    duracion_total = time.perf_counter() - inicio_total

    latencias.sort()

    def percentil(p):
        idx = int(len(latencias) * p) - 1
        return latencias[max(idx, 0)]

    print("=== Resultados de la prueba de carga ===")
    print(f"Intentos totales:        {intentos}")
    print(f"Reservas exitosas:       {exitosos}")
    print(f"Rechazadas (sin stock):  {rechazados}")
    print(f"Duración total:          {duracion_total:.2f} s")
    print(f"Throughput:              {intentos / duracion_total:.1f} intentos/seg")
    print(f"Latencia promedio:       {statistics.mean(latencias):.2f} ms")
    print(f"Latencia p50:            {percentil(0.50):.2f} ms")
    print(f"Latencia p95:            {percentil(0.95):.2f} ms")
    print(f"Latencia p99:            {percentil(0.99):.2f} ms")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--usuarios", type=int, default=50000)
    parser.add_argument("--intentos", type=int, default=100000)
    parser.add_argument("--hilos", type=int, default=50)
    args = parser.parse_args()
    ejecutar(args.usuarios, args.intentos, args.hilos)
