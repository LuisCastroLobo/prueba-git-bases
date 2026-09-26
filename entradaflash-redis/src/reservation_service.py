import uuid

from src.config import get_redis_connection
from src.lua_scripts import CANCEL_LUA, CONFIRM_LUA, RESERVE_LUA


class ReservationService:
    """
    Encapsula toda la lógica de negocio de EntradaFlash CR sobre Redis.

    Diseño de claves:
      evento:{id}:info                             -> hash (nombre, etc.)
      evento:{id}:zona:{zona}:disponibilidad        -> string (contador entero)
      reserva:{id}                                  -> hash (usuario, zona_key,
                                                        cantidad, estado)
      reserva:{id}:vigencia                          -> string con TTL; al
                                                        expirar dispara la
                                                        devolución de inventario
                                                        (ver expiry_listener.py)
      carrito:{usuario_id}                           -> set de reserva_ids,
                                                        con TTL de sesión
    """

    def __init__(self, r=None, reserva_ttl: int = 300):
        self.r = r or get_redis_connection()
        self.reserva_ttl = reserva_ttl
        self._reserve = self.r.register_script(RESERVE_LUA)
        self._confirm = self.r.register_script(CONFIRM_LUA)
        self._cancel = self.r.register_script(CANCEL_LUA)

    @staticmethod
    def clave_disponibilidad(evento_id, zona) -> str:
        return f"evento:{evento_id}:zona:{zona}:disponibilidad"

    # ---------- Consultas ----------
    def consultar_disponibilidad(self, evento_id, zona):
        valor = self.r.get(self.clave_disponibilidad(evento_id, zona))
        return int(valor) if valor is not None else None

    def obtener_reserva(self, reserva_id):
        return self.r.hgetall(f"reserva:{reserva_id}")

    # ---------- Reservas ----------
    def crear_reserva(self, usuario_id, evento_id, zona, cantidad):
        reserva_id = str(uuid.uuid4())
        zona_key = self.clave_disponibilidad(evento_id, zona)
        reserva_key = f"reserva:{reserva_id}"
        vigencia_key = f"reserva:{reserva_id}:vigencia"

        resultado = self._reserve(
            keys=[zona_key, reserva_key, vigencia_key],
            args=[cantidad, usuario_id, self.reserva_ttl],
        )

        if resultado == -1:
            raise ValueError(f"La zona '{zona}' del evento {evento_id} no existe")
        if resultado == 0:
            return None  # sin inventario suficiente

        self._agregar_a_carrito(usuario_id, reserva_id)
        return reserva_id

    def confirmar_reserva(self, reserva_id) -> bool:
        reserva_key = f"reserva:{reserva_id}"
        vigencia_key = f"reserva:{reserva_id}:vigencia"
        return self._confirm(keys=[reserva_key, vigencia_key]) == 1

    def cancelar_reserva(self, reserva_id) -> bool:
        reserva_key = f"reserva:{reserva_id}"
        vigencia_key = f"reserva:{reserva_id}:vigencia"
        return self._cancel(keys=[reserva_key, vigencia_key]) == 1

    # ---------- Carrito / sesión temporal ----------
    def _agregar_a_carrito(self, usuario_id, reserva_id, ttl: int = 1800):
        carrito_key = f"carrito:{usuario_id}"
        self.r.sadd(carrito_key, reserva_id)
        self.r.expire(carrito_key, ttl)

    def obtener_carrito(self, usuario_id):
        carrito_key = f"carrito:{usuario_id}"
        reserva_ids = self.r.smembers(carrito_key)
        return [self.obtener_reserva(rid) for rid in reserva_ids]
