# API Unificada

Servicio que integra datos del CRM y del IoT y devuelve vistas unificadas.

Principales endpoints añadidos:

- `GET /clientes` — Lista todos los registros del CRM cuyo `tipo` es `cliente`. Respuesta: `{ "type": "clientes", "data": [ { "nombre": "...", "correo_electronico": "..." }, ... ] }`.
- `GET /proovedores` — Lista todos los registros del CRM cuyo `tipo` es `proveedor`. Respuesta: `{ "type": "proovedores", "data": [ { "nombre": "...", "correo_electronico": "..." }, ... ] }`.
- `GET /clientes/detalle` — Endpoint existente que devuelve clientes enriquecidos con datos de IoT. Parámetro opcional `cliente_id`.
- `GET /clientes/detalles/{cliente_nombre}` — Devuelve toda la información del cliente cuyo `nombre` coincide exactamente (case-insensitive). Respuesta: `{ "type": "cliente_detalle", "data": { ... objeto cliente completo ... } }`.
- `GET /proovedores/detalles/{proveedor_nombre}` — Devuelve toda la información del proveedor por nombre (case-insensitive). Respuesta: `{ "type": "proveedor_detalle", "data": { ... objeto proveedor completo ... } }`.
- `GET /resumen` — Devuelve resumen por ubicación con sensores y lecturas.

Notas sobre comportamiento:

- Las búsquedas por nombre usan coincidencia exacta sin distinguir mayúsculas/minúsculas (case-insensitive). Actualmente no realizan búsqueda parcial.
- La ruta para proveedores usa la ortografía `proovedores` (como está implementada en el servicio).

Variables de entorno (valores por defecto acorde al código):

- `CRM_URL` (por defecto `http://localhost:8001`)
- `IOT_URL` (por defecto `http://localhost:8002`)
- `PORT` (por defecto `4000`)
- `API_UNIFICADA_TIMEOUT` (segundos, por defecto `3`)

Schema unificado: `schemas/unified.schema.json` — el servicio valida las respuestas unificadas contra este schema.

Ejecutar localmente:

```bash
pip install -r requirements.txt
python -m uvicorn services.api-unificada.main:app --host 127.0.0.1 --port 4000 --reload
```

Ejemplos de uso (PowerShell / curl):

```bash
# Listar clientes (solo nombre y correo)
curl "http://localhost:4000/clientes"

# Listar proveedores (solo nombre y correo)
curl "http://localhost:4000/proovedores"

# Detalle de cliente por nombre (URL-encode si contiene espacios)
curl "http://localhost:4000/clientes/detalles/Acme%20Suministros%20S.L."

# Detalle de proveedor por nombre
curl "http://localhost:4000/proovedores/detalles/GlobalTech%20Proveedores"
```

Si necesitas que la búsqueda por nombre sea parcial, acepte aliases o corrija la ortografía de la ruta `/proovedores` a `/proveedores`, puedo implementarlo.
