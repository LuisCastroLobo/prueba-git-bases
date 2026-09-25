# EntradaFlash CR: Una Solución Clave-Valor sobre Redis para Control de Concurrencia en Ventas de Alta Demanda

> NOTA PARA EL EQUIPO: Este es un ESQUELETO. Cada sección trae instrucciones
> en cursiva sobre qué debe contener. Bórrenlas conforme vayan escribiendo el
> contenido real. Para el documento final, usen la plantilla oficial IEEE de
> dos columnas (búsquenla como "IEEE Conference Template" en Overleaf o
> Word) — este archivo es para organizar las ideas primero.

**Autores:** [Nombres de los integrantes del Grupo 1], Escuela de Estadística,
Universidad de Costa Rica

**Resumen (Abstract):**
*3-5 líneas: qué problema resuelve EntradaFlash CR, qué tecnología usaron
(Redis) y por qué, y el hallazgo principal de sus pruebas (ej. throughput
alcanzado, latencia promedio, y que no hubo sobreventa).*

**Palabras clave:** NoSQL, Redis, Clave-Valor, Concurrencia, TTL

---

## I. Introducción y problema

*Describan el contexto de EntradaFlash CR: qué le pasa a la empresa hoy
(bloqueos, sobreventa, carritos lentos), por qué es un problema de negocio
real, y qué consecuencias tiene no resolverlo (pérdida de clientes,
reputación, ventas fallidas). Cierren explicando brevemente qué propone
este paper.*

## II. Fundamentos del modelo Clave-Valor

*Aquí va la investigación técnica pedida en el enunciado. Cubran:*
- *Qué es un almacén clave-valor y en qué se diferencia de un RDBMS*
- *Arquitectura general (in-memory, shared-nothing, etc.)*
- *Modelo de datos: cómo se estructuran claves y valores*
- *Consistencia: qué garantiza Redis (por defecto, consistencia fuerte en
  un solo nodo; eventual en modo cluster/réplicas)*
- *Escalabilidad: vertical vs. horizontal, sharding en Redis Cluster*
- *Mecanismo de consulta: comandos directos por clave, no hay "queries"
  tipo SQL*
- *Ventajas y limitaciones generales del modelo*
- *Casos de uso típicos (caching, sesiones, colas, rate limiting, leaderboards)*

*Citen fuentes reales (documentación oficial de Redis, papers académicos,
libros) — recuerden que "toda fuente consultada deberá citarse
correctamente".*

## III. Tecnología seleccionada: Redis

*Justifiquen por qué Redis específicamente (y no otro producto clave-valor)
es adecuado para este caso: TTL nativo, operaciones atómicas, estructuras
de datos ricas (hash, set), pub/sub para keyspace notifications, licencia
open source, comunidad y documentación. Mencionen la versión usada.*

## IV. Modelo y arquitectura de la solución

*Expliquen su diseño de claves (pueden reutilizar la tabla del README),
por qué separaron `reserva:{id}` de `reserva:{id}:vigencia`, cómo
manejan el TTL, y el diagrama de arquitectura general (cliente -> servicio
de reservas -> Redis -> listener de expiración).*

*Incluyan un diagrama (pueden hacerlo en draw.io o similar).*

## V. Implementación

*Describan las decisiones técnicas relevantes:*
- *Por qué usaron scripts Lua para las operaciones atómicas (y no
  transacciones MULTI/EXEC, o al revés — comparen brevemente)*
- *Cómo funciona el mecanismo de expiración con keyspace notifications*
- *Cómo implementaron el rate limiting*
- *Estructura del repositorio y stack usado (Python, redis-py)*

## VI. Pruebas

*Documenten:*
- *La prueba de concurrencia (dos clientes compitiendo por la última
  entrada) — resultado esperado vs. obtenido*
- *La metodología de la prueba de carga (cuántos usuarios simulados,
  cuántos intentos, cuántos hilos, qué máquina/hardware usaron)*
- *Cómo generaron los datos de forma reproducible*

## VII. Resultados

*Aquí van tablas y capturas REALES de lo que obtuvieron al correr
`load_test.py` en su máquina: throughput, latencia p50/p95/p99, tasa de
éxito/rechazo. No basta con decir "fue rápido" — necesitan números.*

*Ejemplo de tabla a llenar con sus datos reales:*

| Métrica | Valor obtenido |
|---|---|
| Intentos totales | |
| Reservas exitosas | |
| Rechazadas (sin stock) | |
| Throughput (intentos/seg) | |
| Latencia p50 (ms) | |
| Latencia p95 (ms) | |
| Latencia p99 (ms) | |

## VIII. Limitaciones

*Sean honestos: ¿qué no cubre esta solución? Por ejemplo: no hay
autenticación real de usuarios, el listener de expiración es un único
proceso (punto único de falla), no se probó con Redis en modo cluster,
etc.*

## IX. Conclusiones

*Resuman si Redis cumplió el objetivo, qué aprendieron sobre el modelo
clave-valor aplicado a este caso, y si lo usarían en producción.*

## Referencias

*Formato IEEE: [1] Autor, "Título," Fuente, año. Incluyan como mínimo la
documentación oficial de Redis y 2-3 fuentes académicas o técnicas
adicionales.*

## Anexos

- Enlace al repositorio: [URL de su GitHub]
