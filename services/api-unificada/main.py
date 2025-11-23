"""
======================================================================================
Nombre:
services/api-unificada/main.py

Descripcion:
Este paquete implementa la API Unificada que expone endpoints HTTP para la consulta integrada de clientes (CRM) y sensores/lecturas IoT.
Incluye funciones para la obtención, enriquecimiento y validación de datos provenientes de servicios externos (CRM e IoT), asegurando el cumplimiento de un esquema JSON unificado.

Detalle:
    - load_unified_schema(): Carga el esquema JSON unificado para validar las respuestas.
    - call_service(url, params): Realiza llamadas HTTP a servicios externos con manejo de errores y timeout.
    - enrich_client_with_iot(client): Enriquecer los datos de un cliente con información de sensores y lecturas IoT asociadas a su ubicación.
    - validate_unified(payload): Valida la respuesta contra el esquema unificado.
    - Endpoint GET /clientes/detalle: Devuelve detalles de clientes enriquecidos con información IoT.
    - Endpoint GET /resumen: Devuelve un resumen agregado por ubicación de clientes, sensores y últimas lecturas.

Endpoints HTTP definidos:
    - GET /clientes/detalle: Recupera clientes (uno o todos) y los enriquece con sensores y lecturas IoT.
    - GET /resumen: Devuelve un resumen por ubicación con conteos de clientes, sensores y última lectura.

---------------------------------------------------------------------------

HISTORICO DE CAMBIOS:
ISSUE         AUTOR              FECHA                   DESCRIPCION
--------      ---------          ---------------         ----------------------------------------------------------------------------------
I002          JAO                23-11-2025              Implementación de endpoints unificados y validaciones para integración CRM-IoT

======================================================================================
"""

from typing import Any, Dict, List, Optional
import os
import requests
from requests.exceptions import RequestException, Timeout
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
import json
from pathlib import Path
from jsonschema import validate, ValidationError

BASE_DIR = Path(__file__).resolve().parent
SCHEMA_FILE = BASE_DIR / "schemas" / "schemaUnificado.schema.json"

CRM_URL = os.environ.get("CRM_URL", "http://localhost:8001")
IOT_URL = os.environ.get("IOT_URL", "http://localhost:8002")
DEFAULT_TIMEOUT = float(os.environ.get("API_UNIFICADA_TIMEOUT", "3"))

app = FastAPI(title="API Unificada")


def load_unified_schema() -> Dict[str, Any]:
    """
    Carga y devuelve el esquema JSON unificado desde SCHEMA_FILE.

    Returns:
        Dict[str, Any]: El esquema JSON como diccionario.

    Raises:
        RuntimeError: Si ocurre un error al leer o parsear el archivo de esquema.
    """
    try:
        with SCHEMA_FILE.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        raise RuntimeError(f"Error cargando schema unificado: {e}")


def call_service(url: str, params: Optional[Dict[str, Any]] = None) -> Any:
    """
    Realiza una petición HTTP GET al servicio indicado y devuelve el cuerpo parseado como JSON.

    Args:
        url (str): URL del servicio externo.
        params (Optional[Dict[str, Any]]): Parámetros de consulta opcionales.

    Returns:
        Any: El contenido JSON devuelto por el servicio.

    Raises:
        HTTPException: Convierte errores de requests en HTTPException para manejo por FastAPI.
    """
    try:
        resp = requests.get(url, params=params, timeout=DEFAULT_TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except Timeout:
        raise HTTPException(status_code=504, detail=f"Timeout contacting {url}")
    except RequestException as e:
        # convert to HTTPException for upper-level handling
        raise HTTPException(status_code=502, detail=f"Error contacting {url}: {e}")


# def enrich_client_with_iot(client: Dict[str, Any]) -> Dict[str, Any]:
#     """
#     Enriquecer los datos de un cliente con sensores y últimas lecturas asociadas a su ubicación.

#     La función:
#       - Extrae la 'direccion' del cliente como ubicacion.
#       - Consulta el servicio IoT para obtener sensores de esa ubicación.
#       - Para cada sensor obtiene las últimas lecturas (limitadas).
#       - Devuelve un diccionario con la estructura {'client': client, 'ubicacionId': ..., 'sensores': [...]}.

#     Args:
#         client (Dict[str, Any]): Objeto cliente proveniente del CRM.

#     Returns:
#         Dict[str, Any]: Cliente enriquecido con información IoT y posibles indicadores de error.
#     """
#     ubicacion = client.get("direccion")
#     result = {"client": client, "ubicacionId": ubicacion, "sensores": []}

#     if not ubicacion:
#         return result

#     # Obtener sensores para la ubicación
#     try:
#         sensores_resp = call_service(
#             f"{IOT_URL}/sensores", params={"ubicacionId": ubicacion}
#         )
#         sensores = (
#             sensores_resp.get("sensores")
#             if isinstance(sensores_resp, dict)
#             else sensores_resp
#         )
#     except HTTPException:
#         # IoT no disponible -> devolver cliente con sensores vacíos y anotar error
#         result["iot_error"] = "no_response"
#         return result

#     # Para cada sensor, obtener últimas lecturas (limitadas)
#     for s in sensores:
#         sensor_id = s.get("id") or s.get("id_sensor")
#         lecturas = []
#         if sensor_id:
#             try:
#                 lecturas_resp = call_service(
#                     f"{IOT_URL}/lecturas", params={"sensorId": sensor_id, "limit": 5}
#                 )
#                 lecturas = (
#                     lecturas_resp.get("lecturas")
#                     if isinstance(lecturas_resp, dict)
#                     else lecturas_resp
#                 )
#             except HTTPException:
#                 lecturas = []
#         result["sensores"].append({"sensor": s, "lecturas": lecturas})

#     return result


def validate_unified(payload: Any) -> None:
    """
    Valida un payload contra el esquema JSON unificado cargado por load_unified_schema.

    Args:
        payload (Any): Estructura de datos a validar.

    Raises:
        HTTPException: Si la validación JSON Schema falla, se lanza HTTPException 500 con detalle.
    """
    schema = load_unified_schema()
    try:
        validate(instance=payload, schema=schema)
    except ValidationError as ve:
        raise HTTPException(
            status_code=500,
            detail=f"Respuesta no conforme al schema unificado: {ve.message}",
        )


# @app.get("/clientes/detalle")
# def clientes_detalle(cliente_id: Optional[str] = Query(None)):
#     """
#     Endpoint GET /clientes/detalle.

#     Recupera uno o todos los clientes desde el CRM y los enriquece con información IoT.
#     Parámetros:
#       - cliente_id (opcional): Si se proporciona, se devuelve solo ese cliente.

#     Returns:
#         JSONResponse: Payload con tipo 'detalle' y la lista de clientes enriquecidos.

#     Raises:
#         HTTPException: Re-lanza errores provenientes del CRM o validación de esquema.
#     """
#     # Obtener clientes del CRM
#     try:
#         if cliente_id:
#             crm_data = call_service(f"{CRM_URL}/clientes/{cliente_id}")
#             clients = [crm_data]
#         else:
#             crm_resp = call_service(f"{CRM_URL}/clientes")
#             # CRM puede devolver {data: [...]} o lista directa
#             clients = (
#                 crm_resp.get("data")
#                 if isinstance(crm_resp, dict) and "data" in crm_resp
#                 else crm_resp
#             )
#     except HTTPException as e:
#         raise HTTPException(status_code=e.status_code, detail=f"CRM error: {e.detail}")

#     enriched = []
#     for c in clients:
#         try:
#             enriched.append(enrich_client_with_iot(c))
#         except Exception as e:
#             enriched.append({"client": c, "error": str(e)})

#     payload = {"type": "detalle", "data": enriched}

#     # Validar
#     validate_unified(payload)

#     return JSONResponse(payload)


@app.get("/resumen")
def resumen():
    """Construye y devuelve un resumen agregado de sensores y sus últimas lecturas.

    Consulta el servicio IoT para obtener la lista de sensores y, para cada sensor,
    obtiene las lecturas asociadas. Compone un payload con la forma:
        {"type": "resumen", "data": [{"sensor": <sensor>, "lecturas": [...]}, ...]}

    Antes de devolver la respuesta valida el payload contra el esquema unificado.

    Returns:
        JSONResponse: Respuesta HTTP con el payload validado.

    Raises:
        HTTPException: Propaga errores de comunicación con los servicios externos
                       (por ejemplo, CRM o IoT) y errores de validación del esquema.
    """
    try:
        sensores_resp = call_service(f"{IOT_URL}/sensores")
        sensores = (
            sensores_resp.get("sensores")
            if isinstance(sensores_resp, dict) and "sensores" in sensores_resp
            else sensores_resp
        )
    except HTTPException:
        sensores = []

    data: List[Dict[str, Any]] = []

    for s in sensores:
        sensor_id = s.get("id") or s.get("id_sensor")
        lecturas: List[Any] = []
        if sensor_id:
            try:
                lect_resp = call_service(
                    f"{IOT_URL}/lecturas", params={"sensorId": sensor_id}
                )
                lecturas = (
                    lect_resp.get("lecturas")
                    if isinstance(lect_resp, dict) and "lecturas" in lect_resp
                    else lect_resp
                )
            except HTTPException:
                lecturas = []

        data.append({"sensor": s, "lecturas": lecturas})

    payload = {"type": "resumen", "data": data}

    validate_unified(payload)

    return JSONResponse(payload)


@app.get("/clientes")
def clientes():
    """Recupera registros desde el CRM y devuelve sólo aquellos de tipo 'cliente'.

    Llama al endpoint del CRM para obtener la lista completa de registros. Filtra
    los elementos cuyo campo 'tipo' (comparado case-insensitive) sea 'cliente'
    y construye una lista con los campos seleccionados:
        {"nombre": ..., "correo_electronico": ...}

    Compone un payload con {"type": "clientes", "data": [...]}, lo valida contra
    el esquema unificado y devuelve la respuesta.

    Returns:
        JSONResponse: Respuesta HTTP con el payload validado.

    Raises:
        HTTPException: Si la llamada al CRM falla o si la validación del esquema falla.
    """
    try:
        crm_resp = call_service(f"{CRM_URL}/clientes")
        clients = (
            crm_resp.get("data")
            if isinstance(crm_resp, dict) and "data" in crm_resp
            else crm_resp
        )
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=f"CRM error: {e.detail}")

    if not isinstance(clients, list):
        clients = []

    filtered = [
        {"nombre": c.get("nombre"), "correo_electronico": c.get("correo_electronico")}
        for c in clients
        if (c.get("tipo") or "").lower() == "cliente"
    ]

    payload = {"type": "clientes", "data": filtered}

    # Validar contra el schema unificado
    validate_unified(payload)

    return JSONResponse(payload)


@app.get("/proovedores")
def proovedores():
    """Recupera registros desde el CRM y devuelve sólo aquellos de tipo 'proveedor'.

    Llama al endpoint del CRM para obtener la lista completa de registros. Filtra
    los elementos cuyo campo 'tipo' (comparado case-insensitive) sea 'proveedor'
    y construye una lista con los campos seleccionados:
        {"nombre": ..., "correo_electronico": ...}

    Compone un payload con {"type": "proovedores", "data": [...]}, lo valida contra
    el esquema unificado y devuelve la respuesta.

    Returns:
        JSONResponse: Respuesta HTTP con el payload validado.

    Raises:
        HTTPException: Si la llamada al CRM falla o si la validación del esquema falla.
    """
    try:
        crm_resp = call_service(f"{CRM_URL}/clientes")
        clients = (
            crm_resp.get("data")
            if isinstance(crm_resp, dict) and "data" in crm_resp
            else crm_resp
        )
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=f"CRM error: {e.detail}")

    if not isinstance(clients, list):
        clients = []

    filtered = [
        {"nombre": c.get("nombre"), "correo_electronico": c.get("correo_electronico")}
        for c in clients
        if (c.get("tipo") or "").lower() == "proveedor"
    ]

    payload = {"type": "proovedores", "data": filtered}

    # Validar contra el schema unificado
    validate_unified(payload)

    return JSONResponse(payload)


@app.get("/clientes/detalles/{cliente_nombre}")
def cliente_detalle_por_nombre(cliente_nombre: str):
    """
    Recupera información detallada de un cliente cuyo `nombre` coincida con el nombre proporcionado (ignorando mayúsculas/minúsculas).

    Args:
        cliente_nombre (str): El nombre del cliente a buscar.

    Returns:
        JSONResponse: Una respuesta JSON que contiene la información detallada del cliente.

    Raises:
        HTTPException: Si ocurre un error al comunicarse con el servicio CRM.
        HTTPException: Si no se encuentra ningún cliente con el nombre especificado.

    Este endpoint consulta el servicio CRM para obtener todos los clientes, realiza una búsqueda insensible a mayúsculas/minúsculas de un cliente cuyo `nombre` coincida con `cliente_nombre`, y devuelve los detalles del cliente si se encuentra.
    """
    try:
        crm_resp = call_service(f"{CRM_URL}/clientes")
        clients = (
            crm_resp.get("data")
            if isinstance(crm_resp, dict) and "data" in crm_resp
            else crm_resp
        )
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=f"CRM error: {e.detail}")

    if not isinstance(clients, list):
        clients = []

    match = None
    for c in clients:
        nombre = c.get("nombre") or ""
        if nombre.lower() == cliente_nombre.lower():
            match = c
            break

    if not match:
        raise HTTPException(
            status_code=404, detail=f"Cliente '{cliente_nombre}' no encontrado"
        )

    payload = {"type": "cliente_detalle", "data": match}
    validate_unified(payload)
    return JSONResponse(payload)


@app.get("/proovedores/detalles/{proveedor_nombre}")
def proveedor_detalle_por_nombre(proveedor_nombre: str):
    """
    Recupera información detallada de un proveedor por su nombre.

    Esta función consulta el servicio CRM para obtener una lista de clientes, filtra aquellos de tipo "proveedor",
    y busca un proveedor cuyo nombre coincida con el `proveedor_nombre` proporcionado (ignorando mayúsculas/minúsculas).
    Si se encuentra, valida y devuelve los detalles del proveedor en el formato de respuesta unificada de la API.
    Si no se encuentra, o si ocurre un error al comunicarse con el CRM, se lanza una HTTPException.

    Args:
        proveedor_nombre (str): El nombre del proveedor a buscar.

    Returns:
        JSONResponse: Una respuesta JSON que contiene los detalles del proveedor.

    Raises:
        HTTPException: Si ocurre un error con el servicio CRM o si el proveedor no es encontrado.
    """
    try:
        crm_resp = call_service(f"{CRM_URL}/clientes")
        clients = (
            crm_resp.get("data")
            if isinstance(crm_resp, dict) and "data" in crm_resp
            else crm_resp
        )
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=f"CRM error: {e.detail}")

    if not isinstance(clients, list):
        clients = []

    match = None
    for c in clients:
        nombre = c.get("nombre") or ""
        if (c.get("tipo") or "").lower() != "proveedor":
            continue
        if nombre.lower() == proveedor_nombre.lower():
            match = c
            break

    if not match:
        raise HTTPException(
            status_code=404, detail=f"Proveedor '{proveedor_nombre}' no encontrado"
        )

    payload = {"type": "proveedor_detalle", "data": match}
    validate_unified(payload)
    return JSONResponse(payload)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 4000)))
