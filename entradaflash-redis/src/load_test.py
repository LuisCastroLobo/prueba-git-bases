"""
Ejecuta los intentos de reserva contra Redis y mide latencia, throughput y
tasa de éxito/rechazo. Cubre el requisito 7 del caso (medir latencia y
rendimiento de un conjunto común de operaciones de lectura/escritura).

Dos modos:

1) Reproducible con el dataset generado (RECOMENDADO para el paper, porque
   usa EXACTAMENTE los mismos 50 000 usuarios / 100 000 intentos que exige
   el enunciado, guardados por src/generate_dataset.py):

       python -m src.generate_dataset          # una sola vez
       python -m src.load_test --desde-archivo data/intentos_reserva.csv

2) Generación al vuelo (rápido para pruebas exploratorias, misma semilla
   así que también es reproducible entre corridas):

       python -m src.load_test --usuarios 50000 --intentos 100000
"""
import argparse
import csv
import random
import statistics
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.config import get_redis_connection
from src.reservation_service import ReservationService
from src.setup_inventory import EVENTOS

SEMILLA = 42


def _intentar(servicio, usuario_id, evento_id, zona, cantidad):
    inicio = time.perf_counter()
    try:
        reserva_id = servicio.crear_reserva(usuario_id, evento_id, zona, cantidad)
        exito = reserva_id is not None
    except Exception:
        exito = False
    duracion_ms = (time.perf_counter() - inicio) * 1000
    return exito, duracion_ms


def _imprimir_resultados(intentos_totales, latencias, exitosos, rechazados, duracion_total):
    latencias.sort()

    def percentil(p):
        idx = int(len(latencias) * p) - 1
        return latencias[max(idx, 0)]

    print("=== Resultados de la prueba de carga ===")
    print(f"Intentos totales:        {intentos_totales:,}")
    print(f"Reservas exitosas:       {exitosos:,}")
    print(f"Rechazadas (sin stock):  {rechazados:,}")
    print(f"Duración total:          {duracion_total:.2f} s")
    print(f"Throughput:              {intentos_totales / duracion_total:.1f} intentos/seg")
    print(f"Latencia promedio:       {statistics.mean(latencias):.2f} ms")
    print(f"Latencia p50:            {percentil(0.50):.2f} ms")
    print(f"Latencia p95:            {percentil(0.95):.2f} ms")
    print(f"Latencia p99:            {percentil(0.99):.2f} ms")


def ejecutar_desde_archivo(ruta_intentos: str, hilos: int = 50):
    """Reproduce contra Redis el dataset exacto generado por generate_dataset.py."""
    r = get_redis_connection()
    servicio = ReservationService(r)

    with open(ruta_intentos, newline="", encoding="utf-8") as f:
        intentos = list(csv.DictReader(f))

    latencias, exitosos, rechazados = [], 0, 0

    def tarea(fila):
        return _intentar(
            servicio,
            fila["usuario_id"],
            int(fila["evento_id"]),
            fila["zona"],
            int(fila["cantidad"]),
        )

    inicio_total = time.perf_counter()
    with ThreadPoolExecutor(max_workers=hilos) as executor:
        futuros = [executor.submit(tarea, fila) for fila in intentos]
        for futuro in as_completed(futuros):
            exito, duracion_ms = futuro.result()
            latencias.append(duracion_ms)
            exitosos += 1 if exito else 0
            rechazados += 0 if exito else 1
    duracion_total = time.perf_counter() - inicio_total

    _imprimir_resultados(len(intentos), latencias, exitosos, rechazados, duracion_total)


def ejecutar_generando_al_vuelo(usuarios: int, intentos: int, hilos: int = 50):
    """Genera los intentos en memoria (misma semilla, reproducible) y los ejecuta."""
    random.seed(SEMILLA)
    r = get_redis_connection()
    servicio = ReservationService(r)

    latencias, exitosos, rechazados = [], 0, 0

    def tarea(_i):
        usuario_id = f"u{random.randint(1, usuarios)}"
        evento = random.choice(EVENTOS)
        zona = random.choice(list(evento["zonas"].keys()))
        cantidad = random.randint(1, 4)
        return _intentar(servicio, usuario_id, evento["id"], zona, cantidad)

    inicio_total = time.perf_counter()
    with ThreadPoolExecutor(max_workers=hilos) as executor:
        futuros = [executor.submit(tarea, i) for i in range(intentos)]
        for futuro in as_completed(futuros):
            exito, duracion_ms = futuro.result()
            latencias.append(duracion_ms)
            exitosos += 1 if exito else 0
            rechazados += 0 if exito else 1
    duracion_total = time.perf_counter() - inicio_total

    _imprimir_resultados(intentos, latencias, exitosos, rechazados, duracion_total)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--desde-archivo", type=str, default=None,
                         help="Ruta al CSV de intentos generado por generate_dataset.py")
    parser.add_argument("--usuarios", type=int, default=50_000)
    parser.add_argument("--intentos", type=int, default=100_000)
    parser.add_argument("--hilos", type=int, default=50)
    args = parser.parse_args()

    if args.desde_archivo:
        ejecutar_desde_archivo(args.desde_archivo, args.hilos)
    else:
        ejecutar_generando_al_vuelo(args.usuarios, args.intentos, args.hilos)
