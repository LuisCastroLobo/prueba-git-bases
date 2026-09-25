"""
Escucha eventos de expiración de Redis (keyspace notifications) y, cuando una
clave 'reserva:{id}:vigencia' expira sin haberse confirmado, devuelve
automáticamente el inventario reservado a la zona correspondiente.

Por qué dos claves y no una sola con TTL:
    cuando una clave con TTL expira, Redis simplemente la borra; se pierde el
    dato de CUÁNTO había que devolver. Por eso guardamos el detalle en
    'reserva:{id}' (sin TTL) y usamos 'reserva:{id}:vigencia' solo como
    disparador de expiración.

Requiere que el servidor tenga habilitado: notify-keyspace-events Ex
Este script lo habilita automáticamente al arrancar.

Uso:
    python -m src.expiry_listener
"""
import re

from src.config import get_redis_connection

PATRON_VIGENCIA = re.compile(r"^reserva:(.+):vigencia$")


def iniciar_listener(r=None):
    r = r or get_redis_connection()
    r.config_set("notify-keyspace-events", "Ex")

    pubsub = r.pubsub()
    pubsub.psubscribe("__keyevent@0__:expired")

    print("Escuchando expiraciones de reservas... (Ctrl+C para detener)")
    for mensaje in pubsub.listen():
        if mensaje["type"] != "pmessage":
            continue

        clave_expirada = mensaje["data"]
        match = PATRON_VIGENCIA.match(clave_expirada)
        if not match:
            continue

        reserva_id = match.group(1)
        reserva_key = f"reserva:{reserva_id}"
        datos = r.hgetall(reserva_key)

        if not datos or datos.get("estado") != "pendiente":
            continue  # ya fue confirmada o cancelada, no hay nada que devolver

        zona_key = datos["zona_key"]
        cantidad = int(datos["cantidad"])
        r.incrby(zona_key, cantidad)
        r.hset(reserva_key, "estado", "expirada")
        print(f"Reserva {reserva_id} expiró -> se devolvieron {cantidad} entradas a {zona_key}")


if __name__ == "__main__":
    iniciar_listener()
