# API Unificada

Servicio que integra datos del CRM y del IoT y devuelve vistas unificadas.

Endpoints:

- `GET /clientes/detalle` - Devuelve lista de clientes enriquecidos con sensores y lecturas. Parámetro opcional `cliente_id`.
- `GET /resumen` - Devuelve resumen por ubicación con conteos y última lectura conocida.

Configuración (vars de entorno):

- `CRM_URL` (por defecto `http://localhost:3001`)
- `IOT_URL` (por defecto `http://localhost:3002`)
- `PORT` (por defecto `4000`)

Schema unificado en `schemas/unified.schema.json`.

Ejecutar:

```bash
pip install -r services/api-unificada/requirements.txt
uvicorn services.api-unificada.main:app --port 4000 --reload
```
