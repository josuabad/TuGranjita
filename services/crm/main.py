from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse
import json
from jsonschema import validate, ValidationError
from pathlib import Path
from uvicorn import run
from starlette.status import HTTP_400_BAD_REQUEST
from fastapi.exceptions import RequestValidationError

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "clientes.json"
SCHEMA_FILE = BASE_DIR.parent.parent / "schemas" / "ClienteProveedor.schema.json"

app = FastAPI(title="CRM Mini (clientes)")


def load_clients() -> List[Dict[str, Any]]:
    # Carga y devuelve la lista de clientes desde el JSON
    with DATA_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def load_schema() -> Dict[str, Any]:
    # Carga y devuelve el esquema JSON desde el archivo
    with SCHEMA_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def validate_client(obj: Dict[str, Any]) -> None:
    # Valida un objeto cliente contra el esquema JSON
    schema = load_schema()
    validate(instance=obj, schema=schema)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=HTTP_400_BAD_REQUEST,
        content={"detail": exc.errors(), "body": exc.body},
    )


@app.get("/clientes")
def get_clientes(
    q: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    pageSize: int = Query(25, ge=1, le=100),
    ubicacionId: Optional[str] = Query(None),
):
    # Listar clientes con búsqueda, paginación y filtro por ubicación

    try:
        clients = load_clients()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error leyendo datos: {e}")

    # Filtering by search
    if q:
        q_lower = q.lower()

        def matches(c):
            nombre = c.get("nombre", "") or ""
            correo = c.get("correo_electronico", "") or ""
            return q_lower in nombre.lower() or q_lower in correo.lower()

        filtered = [c for c in clients if matches(c)]
    else:
        filtered = clients

    # Filtering by ubicacionId
    if ubicacionId:
        filtered = [
            c for c in filtered if str(c.get("direccion", "")) == str(ubicacionId)
        ]

    total = len(filtered)

    # Pagination
    start = (page - 1) * pageSize
    end = start + pageSize
    page_data = filtered[start:end]

    # Validate each client in page
    try:
        for client in page_data:
            validate_client(client)
    except ValidationError as ve:
        raise HTTPException(
            status_code=500, detail=f"Objeto inválido según schema: {ve.message}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error validando objetos: {e}")

    return JSONResponse(
        {"total": total, "page": page, "pageSize": pageSize, "data": page_data}
    )


@app.get("/clientes/{cliente_id}")
def get_cliente(cliente_id: str):
    try:
        clients = load_clients()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error leyendo datos: {e}")

    for client in clients:
        if client.get("id") == cliente_id:
            # Validate single client
            try:
                validate_client(client)
            except ValidationError as ve:
                raise HTTPException(
                    status_code=500,
                    detail=f"Objeto inválido según schema: {ve.message}",
                )
            except Exception as e:
                raise HTTPException(
                    status_code=500, detail=f"Error validando objeto: {e}"
                )
            return client

    raise HTTPException(status_code=404, detail="Cliente no encontrado")


def validate_all_clients() -> int:
    """
    Helper for quick sanity check: validates all clients and returns the count validated.
    Raises ValidationError on first invalid client.
    """
    clients = load_clients()
    for c in clients:
        validate_client(c)
    return len(clients)


if __name__ == "__main__":
    run(app)
