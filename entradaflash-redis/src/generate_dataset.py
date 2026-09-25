"""
Genera el conjunto de datos sintéticos que exige el caso EntradaFlash CR:
  - Al menos 50 000 usuarios simulados
  - Al menos 100 000 intentos de reserva

Todo se genera con una semilla fija (SEMILLA), así que correr este script
dos veces produce EXACTAMENTE los mismos datos: eso es lo que el enunciado
pide con "generados reproduciblemente" — el profesor puede correrlo de
nuevo y obtener el mismo dataset.

Los datos se guardan como archivos CSV en data/, sin tocar Redis todavía.
Luego, 'src/load_test.py --desde-archivo' lee esos CSV y sí los envía
contra Redis para medir latencia y rendimiento reales.

Uso:
    python -m src.generate_dataset
"""
import csv
import os
import random

from src.setup_inventory import EVENTOS

SEMILLA = 42
N_USUARIOS = 50_000
N_INTENTOS = 100_000

DIRECTORIO_DATOS = os.path.join(os.path.dirname(__file__), "..", "data")


def generar_usuarios(n: int = N_USUARIOS, seed: int = SEMILLA):
    random.seed(seed)
    return [
        {"usuario_id": f"u{i}", "nombre": f"Usuario Simulado {i}"}
        for i in range(1, n + 1)
    ]


def generar_intentos_reserva(n: int = N_INTENTOS, n_usuarios: int = N_USUARIOS, seed: int = SEMILLA):
    # Usamos la MISMA semilla que generar_usuarios para que, si alguien
    # regenera todo desde cero, los usuarios referenciados aquí sigan
    # siendo consistentes con el archivo usuarios.csv.
    random.seed(seed)
    intentos = []
    for i in range(n):
        usuario_id = f"u{random.randint(1, n_usuarios)}"
        evento = random.choice(EVENTOS)
        zona = random.choice(list(evento["zonas"].keys()))
        cantidad = random.randint(1, 4)
        intentos.append({
            "intento_id": i + 1,
            "usuario_id": usuario_id,
            "evento_id": evento["id"],
            "zona": zona,
            "cantidad": cantidad,
        })
    return intentos


def guardar_csv(registros, nombre_archivo: str) -> str:
    os.makedirs(DIRECTORIO_DATOS, exist_ok=True)
    ruta = os.path.join(DIRECTORIO_DATOS, nombre_archivo)
    with open(ruta, "w", newline="", encoding="utf-8") as f:
        campos = list(registros[0].keys())
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        writer.writerows(registros)
    return ruta


def generar_dataset():
    usuarios = generar_usuarios()
    intentos = generar_intentos_reserva()

    ruta_usuarios = guardar_csv(usuarios, "usuarios.csv")
    ruta_intentos = guardar_csv(intentos, "intentos_reserva.csv")

    print(f"Usuarios generados:            {len(usuarios):,} -> {ruta_usuarios}")
    print(f"Intentos de reserva generados: {len(intentos):,} -> {ruta_intentos}")
    print(f"Semilla usada: {SEMILLA} (correr este script de nuevo da el mismo resultado)")


if __name__ == "__main__":
    generar_dataset()
