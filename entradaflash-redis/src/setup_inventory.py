"""
Genera el inventario base del caso: al menos 5 eventos, cada uno con varias
zonas, con un mínimo de 20 000 entradas en total. Es reproducible porque las
cantidades están fijas (no aleatorias) en EVENTOS.

Uso:
    python -m src.setup_inventory
"""
from src.config import get_redis_connection

EVENTOS = [
    {"id": 1, "nombre": "Concierto Rock CR", "zonas": {"General": 6000, "VIP": 1500, "Platinum": 500}},
    {"id": 2, "nombre": "Partido Seleccion Nacional", "zonas": {"Norte": 4000, "Sur": 4000, "Preferencial": 1000}},
    {"id": 3, "nombre": "Festival Electronico", "zonas": {"General": 3000, "VIP": 800}},
    {"id": 4, "nombre": "Obra de Teatro Nacional", "zonas": {"Luneta": 600, "Balcon": 400}},
    {"id": 5, "nombre": "Stand Up Comedy Night", "zonas": {"General": 500, "Mesa VIP": 200}},
]


def cargar_inventario(r=None, limpiar: bool = True) -> int:
    r = r or get_redis_connection()

    if limpiar:
        for clave in r.scan_iter("evento:*"):
            r.delete(clave)

    total_entradas = 0
    for evento in EVENTOS:
        r.hset(f"evento:{evento['id']}:info", mapping={"nombre": evento["nombre"]})
        for zona, capacidad in evento["zonas"].items():
            clave = f"evento:{evento['id']}:zona:{zona}:disponibilidad"
            r.set(clave, capacidad)
            total_entradas += capacidad

    print(f"Inventario cargado: {len(EVENTOS)} eventos, {total_entradas} entradas totales")
    return total_entradas


if __name__ == "__main__":
    cargar_inventario()
