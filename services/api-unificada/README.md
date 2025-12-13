# API Unificada

Servicio que integra datos del CRM y del IoT y devuelve vistas unificadas.

Principales endpoints añadidos:

- `GET /clientes` — Lista todos los registros del CRM cuyo `tipo` es `cliente`. Respuesta: `{ "type": "clientes", "data": [ { "nombre": "...", "correo_electronico": "..." }, ... ] }`.
- `GET /proveedores` — Lista todos los registros del CRM cuyo `tipo` es `proveedor`. Respuesta: `{ "type": "proveedores", "data": [ { "nombre": "...", "correo_electronico": "..." }, ... ] }`.
- `GET /clientes/detalles/{cliente_nombre}` — Devuelve toda la información del cliente cuyo `nombre` coincide exactamente (case-insensitive). Respuesta: `{ "type": "cliente_detalle", "data": { ... objeto cliente completo ... } }`.
- `GET /proveedores/detalles/{proveedor_nombre}` — Devuelve toda la información del proveedor por nombre (case-insensitive), incluyendo sensores asociados. Respuesta: `{ "type": "proveedor_detalle_con_sensores", "data": { "proveedor": {...}, "sensores_asociados": [...] } }`.
- `GET /resumen` — Devuelve resumen por ubicación con sensores y lecturas.
- `GET /resumen/{sensor_id}?q={numero}` — Devuelve las últimas 'q' lecturas del sensor especificado por su ID. Parámetro 'q' es entero entre 1 y 100 (por defecto 10). Respuesta: `{ "type": "resumen_sensor", "data": { "sensor": {...}, "lecturas": [...] } }`.

Notas sobre comportamiento:

- Las búsquedas por nombre usan coincidencia exacta sin distinguir mayúsculas/minúsculas (case-insensitive). Actualmente no realizan búsqueda parcial.
- La ruta para proveedores usa la ortografía `proveedores` (como está implementada en el servicio).

Variables de entorno (valores por defecto acorde al código):

- `CRM_URL` (por defecto `http://localhost:8001`)
- `IOT_URL` (por defecto `http://localhost:8002`)
- `PORT` (por defecto `4000`)
- `API_UNIFICADA_TIMEOUT` (segundos, por defecto `5`)

Schema unificado: `schemas/schemaUnificado.schema.json` — el servicio valida las respuestas unificadas contra este schema.

Ejecutar localmente:

```bash
pip install -r requirements.txt
python -m uvicorn services.api-unificada.main:app --host 0.0.0.0 --port 4000 --reload
```

Ejemplos de uso (PowerShell / curl):

```bash
# Listar clientes (solo nombre y correo)
curl "http://localhost:4000/clientes"

# Listar proveedores (solo nombre y correo)
curl "http://localhost:4000/proveedores"

# Detalle de cliente por nombre (URL-encode si contiene espacios)
curl "http://localhost:4000/clientes/detalles/Acme%20Suministros%20S.L."

# Detalle de proveedor por nombre
curl "http://localhost:4000/proveedores/detalles/GlobalTech%20Proveedores"

# Resumen de sensores y lecturas
curl "http://localhost:4000/resumen"

# Últimas 5 lecturas del sensor S-TEMP-OUT-01
curl "http://localhost:4000/resumen/S-TEMP-OUT-01?q=5"
```

Si necesitas que la búsqueda por nombre sea parcial, acepte aliases o corrija la ortografía de la ruta `/proveedores` a `/proveedores`, puedo implementarlo.
