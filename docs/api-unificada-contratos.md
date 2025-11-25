# Contratos API Unificada

Este documento describe los contratos (endpoints, parámetros, respuestas) expuestos por la API Unificada, que integra datos de los servicios CRM e IoT.

### Convenciones

- Todos los endpoints devuelven `application/json`.
- Las respuestas están validadas contra un esquema JSON unificado.
- Los identificadores son cadenas.
- Base URL de ejemplo: `http://localhost:4000`

---

## Endpoints

### GET /resumen

Descripción: Devuelve un resumen agregado de sensores y sus últimas lecturas desde el servicio IoT.

Parámetros: Ninguno.

Respuesta 200: Objeto con `type: "resumen"` y `data` como array de objetos con sensor y lecturas.

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

### GET /clientes

Descripción: Recupera la lista de clientes desde el CRM.

Parámetros: Ninguno.

Respuesta 200: Objeto con `type: "clientes"` y `data` como array de clientes con nombre y correo.

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

### GET /clientes/detalles/{cliente_nombre}

Descripción: Devuelve detalles de un cliente por nombre (búsqueda case-insensitive).

Parámetros de ruta:

- `cliente_nombre` (string): Nombre del cliente.

Respuesta 200: Objeto con `type: "cliente_detalle"` y `data` con detalles del cliente.

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

Respuesta 404:

```json
{ "detail": "Cliente 'nombre' no encontrado" }
```

### GET /proveedores

Descripción: Recupera la lista de proveedores desde el CRM.

Parámetros: Ninguno.

Respuesta 200: Objeto con `type: "proveedores"` y `data` como array de proveedores con nombre y correo.

Ejemplo (respuesta):

```json
{
  "type": "proveedores",
  "data": [
    {
      "nombre": "Proveedor Ejemplo S.L.",
      "correo_electronico": "contacto@proveedor.es"
    }
  ]
}
```

### GET /proveedores/detalles/{proveedor_nombre}

Descripción: Devuelve detalles de un proveedor por nombre, incluyendo sensores asociados.

Parámetros de ruta:

- `proveedor_nombre` (string): Nombre del proveedor.

Respuesta 200: Objeto con `type: "proveedor_detalle_con_sensores"` y `data` con proveedor y sensores asociados.

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
      "correo_electronico": "contacto@proveedor.es",
      "numero_telefono": "+34919876543"
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

Respuesta 404:

```json
{ "detail": "Proveedor 'nombre' no encontrado" }
```

---

## Esquema Unificado

Las respuestas están validadas contra el esquema JSON definido en `services/api-unificada/schemas/schemaUnificado.schema.json`. El esquema permite diferentes tipos de respuestas basadas en el campo `type`.
