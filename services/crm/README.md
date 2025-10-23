# CRM

## Uso

Dev:

```bash
# Desde el directorio raíz
fastapi dev services/crm/main.py

# O con Uvicorn
uvicorn services/crm/main:app --host 0.0.0.0 --port 8001 --reload
```

Prod:

```bash
# Desde el directorio raíz
fastapi run services/crm/main.py

# O con Uvicorn
uvicorn services/crm/main:app --host 0.0.0.0 --port 8001
```

### Probar endpoints

```bash
# listar
curl "http://127.0.0.1:8001/clientes"

# búsqueda y paginación
curl "http://127.0.0.1:8001/clientes?q=soluciones&page=1&pageSize=10"

# obtener por id
curl "http://127.0.0.1:8001/clientes/C-1001"
```

## Notas

Los últimos 5 clientes no clumplen las validaciones definidas

```json
[
  {
    "id": "C-I01",
    "nombre": "Falta NIF S.A."
    // ❌ Razón: Falta el campo obligatorio "nif"
  },
  {
    "id": "C-I02",
    "nombre": "Tipo Incorrecto Co.",
    "direccion": "C/ Falsa, 123",
    "nif": "B12345678",
    "numero_telefono": 910111213 // ❌ Razón: "numero_telefono" es un número (debe ser un string)
  },
  {
    "id": "C-I03",
    "nombre": "Formato Email Inválido",
    "nif": "A98765432",
    "correo_electronico": "contacto[at]ejemplo.com" // ❌ Razón: No cumple el formato "email" (falta el '@' principal)
  },
  {
    "id": "C-I04",
    "nombre": "Teléfono Demasiado Corto",
    "nif": "Z00000000",
    "numero_telefono": "123456" // ❌ Razón: No cumple el patrón (mínimo 7 caracteres)
  },
  {
    "id": 105, // ❌ Razón: "id" es un número (debe ser un string)
    "nombre": "ID es Número Corp.",
    "nif": "X11223344"
  }
]
```
