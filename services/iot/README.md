# Iot Mini

## Python

## Uso

```bash
# Desde el directorio raíz
python -m uvicorn services.iot.main:app --host 127.0.0.1 --port 8002 --reload
```

### Contexto

Nuestra empresa (TuGranjita.com) va a desarrollar los sistemas tecnológicos de integración para una granja que actualmente está operando de manera muy rudimentaria y poco automatizada.

### Objetivo

Debemos pasar de las definiciones teóricas de la práctica 1 a una implementación mínima funcional.

Objetivo principal: Implementar 2 servicios REST reales: CRM e IoT, ambos simulados. La API unificada llegará en el siguiente tema; ahora hay que centrarse en que estos dos sistemas devuelven datos válidos y estables.

### Requisitos

El objetivo principal es exponer listados de **sensores** y **lecturas** simulados con capacidad de **filtrado** y **validación**

#### 1. Tecnología y Configuración

- **Tecnología**: Implementado en **Python** utilizando el _framework_ **FastAPI**
- **Servidor**: Se recomienda usar **uvicorn**.
- **Ejecución local**: En un puerto distinto al del CRM, por ejemplo, **8002** si se usa Python.
- **Datos y Esquemas**:
  - **Datos**: Ficheros JSON estáticos en la carpeta `./services/iot/data/` (e.g., `sensores.json` y `lecturas.json`).
  - **Esquemas**: Ficheros JSON Schema en la carpeta `./schemas/` (e.g., `sensor.schema.json` y `lectura.schema.json`).

#### 2. Entidades Mínimas y Datos Semilla

El servicio debe exponer las entidades operativas (IoT) definidas:

- **Sensor**: `id`, `tipo` (tempedad, movimiento, gps...), `ubicacionId`.
- **Lectura**: `id`, `sensorId`, `valor`, `unidad`, `timestamp` (formato **ISO-8601**).
- **Datos Semilla**: Se recomienda disponer de **≥ 3 sensores** y **≥ 5 lecturas por sensor** para pruebas de filtros.

#### 3. Endpoints Mínimos Requeridos

El servicio debe implementar los siguientes _endpoints_ con las capacidades de filtrado especificadas:

| Ruta        | Método | Descripción                                                        | Requisitos de Query Params                                                                                   |
| :---------- | :----: | :----------------------------------------------------------------- | :----------------------------------------------------------------------------------------------------------- |
| `/sensores` | `GET`  | Devolver el listado de sensores desde `sensores.json`.             | (Opcional: `tipo` o `ubicacionId`).                                                                          |
| `/lecturas` | `GET`  | Cargar `lecturas.json` y devolver el listado filtrado y recortado. | `sensorId`, `ubicacionId`, `from` (ISO 8601), `to` (ISO 8601), `limit` (entero; por defecto 100, máx. 1000). |

#### 4. Reglas Funcionales y de Datos

- **Validación de Salida**: Todas las **lecturas** devueltas por el _endpoint_ deben **validarse** contra `lectura.schema.json` **antes de responder**.
- **Orden de Filtros**: Los filtros de `/lecturas` deben aplicarse en el siguiente orden estricto: `sensorId` → `ubicacionId` → `from` → `to`.
- **Manejo de Fechas**:
  - El campo `timestamp` debe usar el formato **ISO-8601 con zona horaria** (ej.: `2025-08-10T08:05:00Z`).
  - Las fechas `from`/`to` deben tratarse como objetos `datetime`, interpretando la `Z` como **UTC (`+00:00`)**.
- **Manejo de `limit`**: El resultado final debe recortarse a `limit` elementos.

#### 5. Gestión de Errores y Códigos HTTP

El servicio debe responder con el código HTTP correcto y un cuerpo de error en formato **JSON** (`{"error": "mensaje descriptivo"}`).

| Código HTTP | Causa              | Descripción                                                                                                                  |
| :---------: | :----------------- | :--------------------------------------------------------------------------------------------------------------------------- |
|   **200**   | Éxito              | Operación completada correctamente.                                                                                          |
|   **400**   | Solicitud inválida | Parámetros de consulta inválidos (ej. fechas mal formateadas o fuera de rango). Se debe rechazar la consulta si `from > to`. |
|   **500**   | Error interno      | Datos no conformes con el **JSON Schema** o error de lectura/IO.                                                             |

#### 6. Dependencias Recomendadas (Python)

- `fastapi`: Para la definición de rutas.
- `uvicorn`: Servidor ASGI.
- `jsonschema`: Para la validación de objetos contra su JSON Schema.
- `python-dateutil` (opcional) o utilidades estándar: Para parsear fechas ISO 8601 con zona horaria.

## Datos simulados JSON

- [lecturas.json](data/lecturas.json): Este archivo incluye 10 registros de diferentes tipos de sensores (Temperatura, Humedad, Presión, Gas y Luminosidad). He incluido el campo opcional nivel_bateria en la mayoría de las entradas (y lo omití intencionalmente en una, la número 8, para demostrar que es opcional), y me aseguré de que todos los timestamp estén en formato ISO 8601 (date-time).
- [sensores.json](data/sensores.json): Este nuevo archivo describe las características de varios sensores, utilizando los valores permitidos para los campos tipo y estado ("activo," "mantenimiento," "error," "inactivo").

### Pruebas con CURL

- Obtener todos los sensores (200)

```bash
curl -i http://localhost:8002/sensores
```

- Filtrar sensores por tipo (200)

```bash
curl -i "http://localhost:8002/sensores?tipo=temperatura"
```

- Filtrar sensores por ubicación (200)

```bash
curl -i "http://localhost:8002/sensores?ubicacionId=Sala%20de%20Servidores%201"
```

- Obtener todas las lecturas (200)

```bash
curl -i http://localhost:8002/lecturas
```

- Filtrar lecturas por sensorId (200)

```bash
curl -i "http://localhost:8002/lecturas?sensorId=S1"
```

- Filtrar lecturas por ubicacionId (200)

```bash
curl -i "http://localhost:8002/lecturas?ubicacionId=Tanque%20de%20Agua%20Potable%20P1"
```

- Filtrar lecturas por rango de fechas (200)

```bash
curl -i "http://localhost:8002/lecturas?from=2025-10-27T10:00:00Z&to=2025-10-27T12:00:00Z"
```

- Limitar el número de lecturas (200)

```bash
curl -i "http://localhost:8002/lecturas?limit=5"
```

- Error: límite fuera de rango (400)

```bash
curl -i "http://localhost:8002/lecturas?limit=0"
```

- Error: fecha inválida (400)

```bash
curl -i "http://localhost:8002/lecturas?from=fecha_invalida"
```

- Error: rango de fechas incorrecto (400)

```bash
curl -i "http://localhost:8000/lecturas?from=2025-12-31T23:59:59Z&to=2024-01-01T00:00:00Z"
```
