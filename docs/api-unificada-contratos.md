# Contratos API Unificada

Este documento describe los contratos (endpoints, parámetros, respuestas) expuestos por el servicio API Unificada, que integra datos de CRM y IoT.

### Convenciones

- Todos los endpoints devuelven `application/json`.
- Las respuestas están validadas contra un esquema JSON unificado.
- Los identificadores son cadenas.
- Base URL de ejemplo: `http://localhost:4000`

---

## Endpoints

### GET /resumen

Descripción: Devuelve un resumen agregado de sensores y sus últimas lecturas desde el servicio IoT.

Respuesta 200: Objeto JSON con `type: "resumen"` y `data` como array de objetos con sensor y lecturas.

Ejemplo (respuesta):

```json
{
  "type": "resumen",
  "data": [
    {
      "sensor": {
        "id": "S-TEMP-OUT-01",
        "nombre": "Sensor de Temperatura Exterior",
        "tipo": "temperatura",
        "ubicacion": "Techo del Edificio A",
        "modelo": "DHT-22-Pro",
        "fabricante": "TechSense Co.",
        "unidad_medida": "C",
        "rango_medicion": "-40 a 80 C",
        "estado": "activo"
      },
      "lecturas": [
        {
          "id_lectura": "L-001",
          "id_sensor": "S-TEMP-OUT-01",
          "valor": 19.5,
          "unidad": "C",
          "timestamp": "2025-10-27T11:00:00Z",
          "nivel_bateria": 92
        }
      ]
    }
  ]
}
```

Errores: 502 si error de comunicación con IoT.

---

### GET /resumen/{sensor_id}

Descripción: Devuelve las últimas 'q' lecturas del sensor especificado por su ID.

Parámetros de ruta:

- `sensor_id` (string) - Identificador del sensor.

Parámetros de consulta:

- `q` (integer, opcional, default 10, min 1, max 100) - Número de lecturas a devolver.

Respuesta 200: Objeto JSON con `type: "resumen_sensor"` y `data` con sensor y lecturas.

Ejemplo (respuesta):

```json
{
  "type": "resumen_sensor",
  "data": {
    "sensor": {
      "id": "S-TEMP-OUT-01",
      "nombre": "Sensor de Temperatura Exterior",
      "tipo": "temperatura",
      "ubicacion": "Techo del Edificio A",
      "modelo": "DHT-22-Pro",
      "fabricante": "TechSense Co.",
      "unidad_medida": "C",
      "rango_medicion": "-40 a 80 C",
      "estado": "activo"
    },
    "lecturas": [
      {
        "id_lectura": "L-001",
        "id_sensor": "S-TEMP-OUT-01",
        "valor": 19.5,
        "unidad": "C",
        "timestamp": "2025-10-27T11:00:00Z",
        "nivel_bateria": 92
      }
    ]
  }
}
```

Respuesta 404: Si el sensor no existe.

```json
{ "detail": "Sensor 'S-TEMP-OUT-01' no encontrado" }
```

Errores: 502 si error de comunicación con IoT.

---

### GET /clientes

Descripción: Recupera registros desde el CRM y devuelve sólo aquellos de tipo 'cliente'.

Respuesta 200: Objeto JSON con `type: "clientes"` y `data` como array de objetos con nombre y correo_electronico.

Ejemplo (respuesta):

```json
{
  "type": "clientes",
  "data": [
    {
      "nombre": "Soluciones Tecnológicas S.L.",
      "correo_electronico": "ventas@soluciones-tech.es"
    }
  ]
}
```

Errores: 502 si error de comunicación con CRM.

---

### GET /clientes/detalles/{cliente_nombre}

Descripción: Recupera información detallada de un cliente cuyo nombre coincide (case-insensitive) con el proporcionado.

Parámetros de ruta:

- `cliente_nombre` (string) - Nombre del cliente a buscar.

Respuesta 200: Objeto JSON con `type: "cliente_detalle"` y `data` con detalles del cliente.

Ejemplo (respuesta):

```json
{
  "type": "cliente_detalle",
  "data": {
    "id": "C-1001",
    "nombre": "Soluciones Tecnológicas S.L.",
    "direccion": "Avda. de la Innovación, 45, 28005 Madrid",
    "nif": "B87654321",
    "correo_electronico": "ventas@soluciones-tech.es",
    "numero_telefono": "+34911234567"
  }
}
```

Respuesta 404: Si el cliente no es encontrado.

```json
{ "detail": "Cliente 'Soluciones Tecnológicas S.L.' no encontrado" }
```

Errores: 502 si error de comunicación con CRM.

---

### GET /proveedores

Descripción: Recupera registros desde el CRM y devuelve sólo aquellos de tipo 'proveedor'.

Respuesta 200: Objeto JSON con `type: "proveedores"` y `data` como array de objetos con nombre y correo_electronico.

Ejemplo (respuesta):

```json
{
  "type": "proveedores",
  "data": [
    {
      "nombre": "Proveedor Ejemplo S.L.",
      "correo_electronico": "contacto@proveedor.com"
    }
  ]
}
```

Errores: 502 si error de comunicación con CRM.

---

### GET /proveedores/detalles/{proveedor_nombre}

Descripción: Recupera información detallada de un proveedor por su nombre, junto con sensores asociados.

Parámetros de ruta:

- `proveedor_nombre` (string) - Nombre del proveedor a buscar.

Respuesta 200: Objeto JSON con `type: "proveedor_detalle_con_sensores"` y `data` con proveedor y sensores asociados.

Ejemplo (respuesta):

```json
{
  "type": "proveedor_detalle_con_sensores",
  "data": {
    "proveedor": {
      "id": "P-1001",
      "nombre": "Proveedor Ejemplo S.L.",
      "direccion": "Calle Ejemplo, 10, 28001 Madrid",
      "nif": "A12345678",
      "correo_electronico": "contacto@proveedor.com",
      "numero_telefono": "+34911234567"
    },
    "sensores_asociados": [
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
  }
}
```

Respuesta 404: Si el proveedor no es encontrado.

```json
{ "detail": "Proveedor 'Proveedor Ejemplo S.L.' no encontrado" }
```

Errores: 502 si error de comunicación con CRM o IoT.

---

### Esquemas de Respuesta

Las respuestas siguen un esquema JSON unificado definido en `services/api-unificada/schemas/schemaUnificado.schema.json`. Cada respuesta incluye un campo `type` que indica el tipo de respuesta y `data` con los datos correspondientes.

Tipos de respuesta:

- `resumen`: Array de objetos {sensor, lecturas}
- `resumen_sensor`: Objeto {sensor, lecturas}
- `clientes`: Array de objetos {nombre, correo_electronico}
- `cliente_detalle`: Objeto o array con detalles del cliente
- `proveedores`: Array de objetos {nombre, correo_electronico}
- `proveedor_detalle_con_sensores`: Objeto {proveedor, sensores_asociados}

---

### Configuración y Variables de Entorno

- `CRM_URL`: URL del servicio CRM (default: http://localhost:8001)
- `IOT_URL`: URL del servicio IoT (default: http://localhost:8002)
- `API_UNIFICADA_TIMEOUT`: Timeout en segundos para llamadas externas (default: 5)
- `PORT`: Puerto en el que corre el servicio (default: 4000)</content>
  <parameter name="filePath">/home/josu/ucjc/integracion/TuGranjita-T3/docs/api-unificada-contratos.md
