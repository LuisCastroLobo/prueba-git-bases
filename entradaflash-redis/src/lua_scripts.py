# Scripts Lua: Redis los ejecuta de forma ATÓMICA (todo o nada, sin que otra
# operación se intercale en medio), que es como se cumple el requisito de
# "al menos una operación atómica para controlar concurrencia" del caso.

RESERVE_LUA = """
-- KEYS[1] = clave de disponibilidad  (evento:{id}:zona:{zona}:disponibilidad)
-- KEYS[2] = clave hash de la reserva (reserva:{id})
-- KEYS[3] = clave 'vigencia' que dispara la expiración (reserva:{id}:vigencia)
-- ARGV[1] = cantidad de entradas solicitadas
-- ARGV[2] = id del usuario
-- ARGV[3] = ttl en segundos para la reserva temporal

local disponible = redis.call('GET', KEYS[1])
if disponible == false then
    return -1 -- la zona/evento no existe
end

disponible = tonumber(disponible)
local cantidad = tonumber(ARGV[1])

if disponible < cantidad then
    return 0 -- no hay suficiente inventario
end

redis.call('DECRBY', KEYS[1], cantidad)

redis.call('HSET', KEYS[2],
    'usuario', ARGV[2],
    'zona_key', KEYS[1],
    'cantidad', cantidad,
    'estado', 'pendiente'
)

redis.call('SET', KEYS[3], '1', 'EX', ARGV[3])

return 1
"""

CONFIRM_LUA = """
-- KEYS[1] = clave hash de la reserva
-- KEYS[2] = clave 'vigencia'
local estado = redis.call('HGET', KEYS[1], 'estado')
if estado == false then
    return -1 -- la reserva ya no existe (probablemente expiró)
end
if estado == 'confirmada' then
    return 0
end

redis.call('HSET', KEYS[1], 'estado', 'confirmada')
redis.call('DEL', KEYS[2]) -- quitamos el disparador de expiración: ya es firme
return 1
"""

CANCEL_LUA = """
-- KEYS[1] = clave hash de la reserva
-- KEYS[2] = clave 'vigencia'
local estado = redis.call('HGET', KEYS[1], 'estado')
if estado == false then
    return -1
end
if estado == 'cancelada' or estado == 'confirmada' then
    return 0
end

local zona_key = redis.call('HGET', KEYS[1], 'zona_key')
local cantidad = tonumber(redis.call('HGET', KEYS[1], 'cantidad'))
redis.call('INCRBY', zona_key, cantidad)
redis.call('HSET', KEYS[1], 'estado', 'cancelada')
redis.call('DEL', KEYS[2])
return 1
"""
