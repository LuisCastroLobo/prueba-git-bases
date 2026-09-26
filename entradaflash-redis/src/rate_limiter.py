from src.config import get_redis_connection


class RateLimiter:
    """
    Limita cuántos intentos puede hacer un usuario/IP en una ventana de tiempo.
    Patrón: INCR + EXPIRE (ventana fija). Sencillo y suficiente para el
    requisito 6 del caso (mecanismo simple de rate limiting).
    """

    def __init__(self, r=None, limite: int = 20, ventana_segundos: int = 60):
        self.r = r or get_redis_connection()
        self.limite = limite
        self.ventana = ventana_segundos

    def permitir(self, identificador: str) -> bool:
        clave = f"ratelimit:{identificador}"
        conteo = self.r.incr(clave)
        if conteo == 1:
            self.r.expire(clave, self.ventana)
        return conteo <= self.limite
