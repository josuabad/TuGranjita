# Contratos API (CRM e IoT)

Este documento resume los contratos (endpoints, parámetros, respuestas) expuestos por los servicios incluidos en el repositorio y aporta ejemplos prácticos.

### Convenciones

- Todos los endpoints devuelven `application/json`.
- Los identificadores (`id`, `id_sensor`, `id_lectura`, `cliente_id`) son cadenas.

---

### CRM - Clientes

Base URL de ejemplo: `http://localhost:8001`

#### GET /clientes

Descripción: Lista clientes con soporte de búsqueda (q), paginación y filtro por `ubicacionId` (campo `direccion`).

Parámetros de consulta:

- `q` (string, opcional): búsqueda por nombre o correo.
- `page` (integer, opcional, default 1)
- `pageSize` (integer, opcional, default 25, max 100)
- `ubicacionId` (string, opcional)

Respuesta 200: objeto con propiedades `total`, `page`, `pageSize` y `data` (array de clientes).

Ejemplo (respuesta):

```json
{
  "total": 125,
  "page": 1,
  "pageSize": 25,
  "data": [
    {
      "id": "C-1001",
      "nombre": "Soluciones Tecnológicas S.L.",
      "direccion": "Avda. de la Innovación, 45, 28005 Madrid",
      "nif": "B87654321",
      "correo_electronico": "ventas@soluciones-tech.es",
      "numero_telefono": "+34911234567"
    }
  ]
}
```

#### GET /clientes/{cliente_id}

Descripción: Devuelve el cliente identificado por `cliente_id`.

Parámetros de ruta:

- `cliente_id` (string) - identificador del cliente.

Respuesta 200: objeto cliente.

Ejemplo (respuesta):

```json
{
  "id": "C-1001",
  "nombre": "Soluciones Tecnológicas S.L.",
  "direccion": "Avda. de la Innovación, 45, 28005 Madrid",
  "nif": "B87654321",
  "correo_electronico": "ventas@soluciones-tech.es",
  "numero_telefono": "+34911234567"
}
```

Respuesta 404:

```json
{ "detail": "Cliente no encontrado" }
```

---

### IoT - Sensores y Lecturas

Base URL de ejemplo: `http://localhost:8002`

#### GET /sensores

Descripción: Lista sensores. Se puede filtrar por `tipo` y `ubicacionId`.

Parámetros de consulta:

- `tipo` (string, opcional) - ejemplo: `temperatura`, `humedad`, `ph`, `movimiento`, `gps`, `otro`.
- `ubicacionId` (string, opcional) - cadena que se compara con el campo `ubicacion` del sensor.

Respuesta 200: array de objetos `Sensor`.

Ejemplo (respuesta):

```json
[
  {
    "id": "S-TEMP-OUT-01",
    "nombre": "Sensor de Temperatura Exterior",
    "tipo": "temperatura",
    "ubicacion": "Techo del Edificio A",
    "modelo": "DHT-22-Pro",
    "fabricante": "TechSense Co.",
    "unidad_medida": "C",
    "rango_medicion": "-40 a 80 C",
    "estado": "activo"
  }
]
```

#### GET /lecturas

Descripción: Devuelve lecturas de sensores. Permite filtrar por `sensorId`, `ubicacionId`, rango temporal (`from` y `to`) y limitar resultados con `limit`.

Parámetros de consulta:

- `sensorId` (string, opcional)
- `ubicacionId` (string, opcional)
- `from` (string, opcional) - fecha ISO (ej. `2025-10-27T11:00:00Z`)
- `to` (string, opcional) - fecha ISO
- `limit` (integer, opcional, default 100, max 1000)

Validaciones importantes implementadas en el servicio:

- `limit` debe estar entre 1 y 1000.
- Si se pasan `from` y `to`, `from` no puede ser posterior a `to`.

Respuesta 200: array de objetos `Lectura`.

Ejemplo (respuesta):

```json
[
  {
    "id_lectura": "L-001",
    "id_sensor": "S-TEMP-OUT-01",
    "valor": 19.5,
    "unidad": "C",
    "timestamp": "2025-10-27T11:00:00Z",
    "nivel_bateria": 92
  },
  {
    "id_lectura": "L-002",
    "id_sensor": "S-HUM-INT-02",
    "valor": 61.2,
    "unidad": "%RH",
    "timestamp": "2025-10-27T11:01:00Z",
    "nivel_bateria": 78
  }
]
```

---

### Esquemas (resumen)

- Cliente: fields `id` (string), `nombre` (string), `direccion` (string, opcional), `nif` (string), `correo_electronico` (email, opcional), `numero_telefono` (string, opcional). `id`, `nombre` y `nif` son obligatorios.
- Sensor: `id`, `nombre`, `tipo`, `ubicacion`, `modelo`, `fabricante`, `unidad_medida`, `rango_medicion`, `estado`. Campos obligatorios: `id`, `nombre`, `tipo`, `ubicacion`, `estado`.
- Lectura: `id_lectura`, `id_sensor`, `valor`, `unidad`, `timestamp` (ISO), `nivel_bateria` (0-100). Los primeros cinco son obligatorios.

---

### Cómo usar la OpenAPI

1. Abrir `app/docs/openapi.yaml` en un editor/visualizador (Swagger UI, Redoc o editor online como editor.swagger.io).
2. Para probar localmente con los servicios, arrancar los FastAPI apps (por ejemplo `uvicorn app.services.crm.main:app --reload --port 8000` y `uvicorn app.services.iot.main:app --reload --port 8000` en tapas separadas o adaptar puertos) y usar la URL `http://localhost:8000`.
