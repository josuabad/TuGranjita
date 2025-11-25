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
    - validate_unified(payload): Valida la respuesta contra el esquema unificado.
    - Endpoints GET /resumen, /resumen/{sensor_id}, /clientes, /clientes/detalles/{cliente_nombre}, /proveedores, /proveedores/detalles/{proveedor_nombre}: Exponen datos integrados y validados de CRM e IoT.

Endpoints HTTP definidos:
    - GET /resumen: Devuelve un resumen agregado de sensores y lecturas.
    - GET /resumen/{sensor_id}: Devuelve las últimas lecturas de un sensor específico.
    - GET /clientes: Lista clientes del CRM.
    - GET /clientes/detalles/{cliente_nombre}: Detalle de cliente por nombre.
    - GET /proveedores: Lista proveedores del CRM.
    - GET /proveedores/detalles/{proveedor_nombre}: Detalle de proveedor y sensores asociados.

---------------------------------------------------------------------------

HISTORICO DE CAMBIOS:
ISSUE         AUTOR              FECHA                   DESCRIPCION
--------      ---------          ---------------         ----------------------------------------------------------------------------------
I002          JAO                23-11-2025              Implementación de endpoints unificados y validaciones para integración CRM-IoT
I002          JAO                25-11-2025              Arreglos en la lógica aplicada de negocio y validación de datos

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
from dateutil import parser as date_parser

BASE_DIR = Path(__file__).resolve().parent
SCHEMA_FILE = BASE_DIR / "schemas" / "schemaUnificado.schema.json"

CRM_URL = os.environ.get("CRM_URL", "http://localhost:8001")
IOT_URL = os.environ.get("IOT_URL", "http://localhost:8002")
DEFAULT_TIMEOUT = float(os.environ.get("API_UNIFICADA_TIMEOUT", "5"))

app = FastAPI(title="API Unificada")


def load_unified_schema() -> Dict[str, Any]:
    """
    Load the unified JSON schema from file.

    Returns:
        dict: The unified JSON schema as a dictionary.

    Raises:
        RuntimeError: If there is an error reading or parsing the schema file.
    """
    try:
        with SCHEMA_FILE.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        raise RuntimeError(f"Error cargando schema unificado: {e}")


def call_service(url: str, params: Optional[Dict[str, Any]] = None) -> Any:
    """
    Make an HTTP GET request to an external service and return the JSON body.

    Args:
        url (str): The external service URL.
        params (dict, optional): Query parameters for the request.

    Returns:
        dict | list: The JSON content returned by the service.

    Raises:
        HTTPException: If a network error, timeout, or invalid response occurs.
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


def validate_unified(payload: Any) -> None:
    """
    Validate a payload against the unified JSON schema.

    Args:
        payload (Any): The data structure to validate.

    Raises:
        HTTPException: If validation against the schema fails.
    """
    schema = load_unified_schema()
    try:
        validate(instance=payload, schema=schema)
    except ValidationError as ve:
        raise HTTPException(
            status_code=500,
            detail=f"Respuesta no conforme al schema unificado: {ve.message}",
        )


@app.get("/resumen")
def resumen():
    """
    Return an aggregated summary of sensors and their latest readings from the IoT service.

    Returns:
        JSONResponse: HTTP response with the summary validated against the unified schema.

    Raises:
        HTTPException: If there is a communication or validation error.
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


@app.get("/resumen/{sensor_id}")
def resumen_sensor(sensor_id: str, q: int = Query(10, ge=1, le=100)):
    """
    Return the latest 'q' readings for the specified sensor by ID.

    Args:
        sensor_id (str): Sensor ID.
        q (int): Number of readings to return (default 10, range 1-100).

    Returns:
        JSONResponse: HTTP response with the sensor and its latest readings.

    Raises:
        HTTPException: If the sensor does not exist or a communication error occurs.
    """
    # Obtener información del sensor
    try:
        sensores_resp = call_service(f"{IOT_URL}/sensores")
        sensores = (
            sensores_resp.get("sensores")
            if isinstance(sensores_resp, dict) and "sensores" in sensores_resp
            else sensores_resp
        )
    except HTTPException:
        raise HTTPException(
            status_code=404, detail=f"Sensor '{sensor_id}' no encontrado"
        )

    sensor = None
    for s in sensores:
        if s.get("id") == sensor_id:
            sensor = s
            break

    if not sensor:
        raise HTTPException(
            status_code=404, detail=f"Sensor '{sensor_id}' no encontrado"
        )

    # Obtener lecturas del sensor
    lecturas = []
    try:
        lect_resp = call_service(
            f"{IOT_URL}/lecturas", params={"sensorId": sensor_id, "limit": 1000}
        )
        lecturas = (
            lect_resp.get("lecturas")
            if isinstance(lect_resp, dict) and "lecturas" in lect_resp
            else lect_resp
        )
    except HTTPException:
        lecturas = []

    # Ordenar por timestamp descendente (más recientes primero)
    try:
        lecturas.sort(
            key=lambda x: date_parser.isoparse(x.get("timestamp", "")), reverse=True
        )
    except Exception:
        # Si hay error en timestamp, devolver sin ordenar
        pass

    # Tomar las primeras q lecturas
    ultimas_lecturas = lecturas[:q]

    payload = {
        "type": "resumen_sensor",
        "data": {"sensor": sensor, "lecturas": ultimas_lecturas},
    }

    validate_unified(payload)

    return JSONResponse(payload)


@app.get("/clientes")
def clientes():
    """
    Retrieve records from the CRM and return only those of type 'cliente'.

    Returns:
        JSONResponse: HTTP response with the list of clients validated against the unified schema.

    Raises:
        HTTPException: If the CRM call fails or schema validation fails.
    """
    try:
        crm_resp = call_service(f"{CRM_URL}/clientes", params={"pageSize": 100})
        if isinstance(crm_resp, dict) and "data" in crm_resp:
            clientes = crm_resp.get("data")
        else:
            clientes = []
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=f"CRM error: {e.detail}")

    filtered = []
    for cliente in clientes:
        cliente: dict
        if cliente.get("tipo") == "cliente":
            filtered.append(
                {
                    "nombre": cliente.get("nombre"),
                    "correo_electronico": cliente.get("correo_electronico"),
                }
            )

    payload = {"type": "clientes", "data": filtered}

    # Validar contra el schema unificado
    validate_unified(payload)

    return JSONResponse(payload)


@app.get("/clientes/detalles/{cliente_nombre}")
def cliente_detalle_por_nombre(cliente_nombre: str):
    """
    Recupera información detallada de un cliente cuyo nombre coincide (case-insensitive) con el proporcionado.

    Args:
        cliente_nombre (str): Nombre del cliente a buscar.

    Returns:
        JSONResponse: JSON response with client details.

    Raises:
        HTTPException: If there is a CRM communication error or the client is not found.
    """
    try:
        crm_resp = call_service(f"{CRM_URL}/clientes", params={"q": cliente_nombre})
        if isinstance(crm_resp, dict) and "data" in crm_resp:
            cliente = crm_resp.get("data")
        else:
            raise HTTPException(
                status_code=404, detail=f"Cliente '{cliente_nombre}' no encontrado"
            )
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=f"CRM error: {e.detail}")

    payload = {"type": "cliente_detalle", "data": cliente}
    validate_unified(payload)
    return JSONResponse(payload)


@app.get("/proveedores")
def proveedores():
    """
    Retrieve records from the CRM and return only those of type 'proveedor'.

    Returns:
        JSONResponse: HTTP response with the list of providers validated against the unified schema.

    Raises:
        HTTPException: If the CRM call fails or schema validation fails.
    """
    try:
        crm_resp = call_service(f"{CRM_URL}/clientes", params={"pageSize": 100})
        if isinstance(crm_resp, dict) and "data" in crm_resp:
            proveedores = crm_resp.get("data")
        else:
            proveedores = []
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=f"CRM error: {e.detail}")

    filtered = []
    for proveedor in proveedores:
        proveedor: dict
        if proveedor.get("tipo") == "proveedor":
            filtered.append(
                {
                    "nombre": proveedor.get("nombre"),
                    "correo_electronico": proveedor.get("correo_electronico"),
                }
            )

    payload = {"type": "proveedores", "data": filtered}

    # Validar contra el schema unificado
    validate_unified(payload)

    return JSONResponse(payload)


@app.get("/proveedores/detalles/{proveedor_nombre}")
def proveedor_detalle_por_nombre(proveedor_nombre: str):
    """
    Retrieve detailed information for a provider by name, along with associated sensors.

    Args:
        proveedor_nombre (str): Name of the provider to search for.

    Returns:
        JSONResponse: JSON response with provider details and associated sensors.

    Raises:
        HTTPException: If there is a CRM error or the provider is not found.
    """
    try:
        crm_resp = call_service(f"{CRM_URL}/clientes", params={"q": proveedor_nombre})
        if isinstance(crm_resp, dict) and "data" in crm_resp:
            proveedor = crm_resp.get("data")
        else:
            raise HTTPException(
                status_code=404, detail=f"Proveedor '{proveedor_nombre}' no encontrado"
            )
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=f"CRM error: {e.detail}")

    # Obtener sensores asociados a este proveedor
    try:
        sensores_resp = call_service(f"{IOT_URL}/sensores")
        sensores = (
            sensores_resp.get("sensores")
            if isinstance(sensores_resp, dict) and "sensores" in sensores_resp
            else sensores_resp
        )
    except HTTPException:
        sensores = []

    # Asociar sensores por campo proveedor (ajustar el campo según el modelo de datos real)
    sensores_asociados = []
    sensores_proveedor = proveedor[0].get("transacciones_detalladas")
    for sensor in sensores:
        sensor: dict
        if sensor.get("id") in sensores_proveedor:
            sensores_asociados.append(sensor)

    payload = {
        "type": "proveedor_detalle_con_sensores",
        "data": {"proveedor": proveedor, "sensores_asociados": sensores_asociados},
    }

    validate_unified(payload)
    return JSONResponse(payload)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 4000)))
