"""
Prueba puntual y muy visual para la demostración en vivo: dos 'clientes'
compiten por la ÚLTIMA entrada disponible de una zona. Solo uno debe
lograr reservarla; el inventario nunca debe quedar negativo.

Uso:
    python -m tests.test_concurrency
"""
from concurrent.futures import ThreadPoolExecutor

from src.config import get_redis_connection
from src.reservation_service import ReservationService
from src.setup_inventory import cargar_inventario


def test_no_hay_sobreventa():
    r = get_redis_connection()
    cargar_inventario(r)

    servicio = ReservationService(r)
    # Dejamos solo 1 entrada disponible para forzar la competencia real
    r.set("evento:1:zona:VIP:disponibilidad", 1)

    with ThreadPoolExecutor(max_workers=2) as executor:
        futuro_a = executor.submit(servicio.crear_reserva, "usuarioA", 1, "VIP", 1)
        futuro_b = executor.submit(servicio.crear_reserva, "usuarioB", 1, "VIP", 1)
        resultados = [futuro_a.result(), futuro_b.result()]

    exitosas = [x for x in resultados if x is not None]
    assert len(exitosas) == 1, "¡Se produjo sobreventa! Ambos clientes reservaron."

    disponible_final = int(r.get("evento:1:zona:VIP:disponibilidad"))
    assert disponible_final == 0, "El inventario debería quedar en exactamente 0."

    print("OK: exactamente una reserva tuvo éxito, sin inventario negativo.")


if __name__ == "__main__":
    test_no_hay_sobreventa()
