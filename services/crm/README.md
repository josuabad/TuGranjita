# CRM Mini

## Contexto

Nuestra empresa (TuGranjita.com) va a desarrollar los sistemas tecnológicos de integración para una granja que actualmente está operando de manera muy rudimentaria y poco automatizada.

## Objetivo

Debemos pasar de las definiciones teóricas de la práctica 1 a una implementación mínima funcional.

Objetivo principal: Implementar 2 servicios REST reales: CRM e IoT, ambos simulados. La API unificada llegará en el siguiente tema; ahora hay que centrarse en que estos dos sistemas devuelven datos válidos y estables.

## Requisitos

- Rutas mínimas
  - GET /clientes
    - Query params: q (texto libre para buscar por nombre/email), page (nº de página, por defecto 1), pageSize (tamaño de página, por defecto 25; recomendable máximo 100).
    - Comportamiento: leer el fichero clientes.json, filtrar por coincidencia parcial (no sensible a mayúsculas) en nombre o email, paginar, validar cada cliente de la página con el schema y devolver { total, page, pageSize, data }.
    - Errores: 500 si algún elemento no cumple el schema; 400 si los parámetros no son numéricos o son inválidos.
  - GET /clientes/{id}.
    - Comportamiento: localizar el cliente por id, validarlo y devolverlo.
    - Errores: 404 si no existe; 500 si el objeto no valida.
- Parámetros: ?q=, ?page=, ?pageSize=, ?ubicacionId=.
- Códigos: 200, 404, 400.
- Reglas de validación: Siempre validar antes de responder: si cualquiera de los elementos de la página de resultados no valida, responder error. El schema debe comprobar tipos, obligatoriedad, y formatos (email, date-time, etc.).
- Consideraciones de implementación
  - Normalizar texto a minúsculas para la búsqueda.
  - Convertir page y pageSize a número y limitar rangos razonables.
  - Calcular start = (page - 1) \* pageSize y hacer slice sobre el array filtrado.
  - Compilar el schema una sola vez y reutilizar el validador.

## Python

### Uso

```bash
# Desde el directorio raíz
python -m uvicorn services.crm.main:app --host 127.0.0.1 --port 8001 --reload
```

### Dependencias Recomendadas

- `fastapi`: Para la definición de rutas.
- `uvicorn`: Servidor ASGI.
- `jsonschema`: Para la validación de objetos contra su JSON Schema.

## Node.js

### Uso

```bash
# Instalar las dependencias
npm install
# Ejecutar el servidor
npm run start
```

### Dependencias Recomendadas

- `express`: Para la definición de rutas.
- `ajv`: Para la validación de objetos contra su JSON Schema.


## Pruebas con CURL

- Obtener todos los clientes (200 OK)

```bash
curl -i http://localhost:8001/clientes
```

- Buscar clientes por nombre/correo (200 OK)

```bash
curl -i "http://localhost:8001/clientes?q=Soluciones%20Tecnológicas%20S.L."
```

- Paginación (200 OK)

```bash
curl -i "http://localhost:8001/clientes?page=2&pageSize=3"
```

- Buscar por ubicación (si implementas el filtro, actualmente no está en el código)

```bash
curl -i "http://localhost:8001/clientes?ubicacionId=Avda.%20de%20la%20Innovación,%2045,%2028005%20Madrid"
```

- Obtener cliente por ID (200 OK o 404 Not Found)

```bash
curl -i http://localhost:8001/clientes/C-1002
```

- Cliente no encontrado (404 Not Found)

```bash
curl -i http://localhost:8001/clientes/id_inexistente
```

- Parámetro inválido (400 Bad Request, por ejemplo, pageSize fuera de rango)

```bash
curl -i "http://localhost:8001/clientes?pageSize=200"
```
