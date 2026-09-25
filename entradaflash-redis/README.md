# EntradaFlash CR — Solución Clave-Valor con Redis

Proyecto para XS0131 - Investigación Grupal 1 (Grupo 1, Caso 1).

## Qué resuelve

Una capa de datos de baja latencia sobre Redis que evita la sobreventa de
entradas durante preventas de alta demanda: consulta de disponibilidad,
reservas temporales con expiración automática (TTL), confirmación/cancelación
sin inventario negativo, control de concurrencia atómico, carrito de sesión
por usuario, y rate limiting.

## Prerrequisitos

- Docker Desktop (para correr el servidor Redis)
- Python 3.10 o superior
- pip

## Instalación

```bash
# 1. Levantar un servidor Redis local con Docker
docker run -d --name redis-entradaflash -p 6379:6379 redis

# 2. Crear entorno virtual e instalar dependencias
python -m venv venv
venv\Scripts\activate        # En Windows
# source venv/bin/activate   # En Mac/Linux
pip install -r requirements.txt

# 3. Copiar el archivo de variables de entorno
copy .env.example .env       # En Windows
# cp .env.example .env       # En Mac/Linux
```

## Carga de datos

```bash
# 1. Inventario: 5 eventos con varias zonas cada uno, 20 000+ entradas totales
python -m src.setup_inventory

# 2. Dataset sintético: 50 000 usuarios simulados y 100 000 intentos de
#    reserva, generados con una semilla fija (reproducible). Se guardan
#    como CSV en data/, sin tocar Redis todavía.
python -m src.generate_dataset
```

## Ejecución

En una terminal, dejen corriendo el listener que devuelve inventario cuando
una reserva expira sin confirmarse:

```bash
python -m src.expiry_listener
```

En otra terminal, prueben la lógica manualmente en Python:

```python
from src.reservation_service import ReservationService

servicio = ReservationService()
servicio.consultar_disponibilidad(1, "VIP")          # -> 1500
reserva_id = servicio.crear_reserva("usuario1", 1, "VIP", 2)
servicio.confirmar_reserva(reserva_id)                # -> True
```

## Pruebas

```bash
# Prueba puntual de concurrencia (dos clientes, una sola entrada disponible)
python -m tests.test_concurrency

# Prueba de carga REPRODUCIBLE: usa el dataset exacto generado en el paso
# anterior (los mismos 50 000 usuarios / 100 000 intentos siempre)
python -m src.load_test --desde-archivo data/intentos_reserva.csv --hilos 50
```

## Demostración

1. Mostrar `RedisInsight` con las claves `evento:*` cargadas.
2. Correr `tests/test_concurrency.py` en vivo: dos clientes compitiendo,
   solo una reserva exitosa.
3. Crear una reserva con TTL corto y mostrar en RedisInsight cómo
   desaparece y el contador de disponibilidad se restaura solo.
4. Mostrar resultados de `load_test.py`.

## Diseño de claves

| Clave | Tipo | Propósito |
|---|---|---|
| `evento:{id}:info` | hash | Metadatos del evento |
| `evento:{id}:zona:{zona}:disponibilidad` | string (contador) | Inventario restante |
| `reserva:{id}` | hash | Detalle de la reserva (sin TTL) |
| `reserva:{id}:vigencia` | string con TTL | Disparador de expiración |
| `carrito:{usuario_id}` | set con TTL | Reservas activas del usuario |
| `ratelimit:{usuario_o_ip}` | contador con TTL | Control de intentos |

## Qué falta por completar (repartir entre el equipo)

- [ ] Paper técnico en formato IEEE
- [ ] Ampliar pruebas automatizadas (pytest) y agregarlas a CI si se desea
- [ ] Documentar qué pasa ante una caída del servicio (persistencia RDB/AOF,
      réplicas) — investigar y escribirlo con sus propias palabras
- [ ] Preparar la presentación tipo pitch a cliente
- [ ] Historial de commits repartido entre integrantes, con mensajes claros
