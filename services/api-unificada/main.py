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
    Carga el esquema JSON unificado desde el archivo de esquema.

    Returns:
        dict: El esquema JSON como diccionario.

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
    Realiza una petición HTTP GET al servicio externo especificado y devuelve el cuerpo como JSON.

    Args:
        url (str): URL del servicio externo.
        params (dict, opcional): Parámetros de consulta para la petición.

    Returns:
        dict | list: El contenido JSON devuelto por el servicio.

    Raises:
        HTTPException: Si ocurre un error de red, timeout o respuesta inválida.
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
    Valida un payload contra el esquema JSON unificado.

    Args:
        payload (Any): Estructura de datos a validar.

    Raises:
        HTTPException: Si la validación contra el esquema falla.
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
    Devuelve un resumen agregado de sensores y sus últimas lecturas desde el servicio IoT.

    Returns:
        JSONResponse: Respuesta HTTP con el resumen validado contra el esquema unificado.

    Raises:
        HTTPException: Si ocurre un error de comunicación con servicios externos o de validación.
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
    Devuelve las últimas 'q' lecturas del sensor especificado por su ID.

    Args:
        sensor_id (str): ID del sensor.
        q (int): Número de lecturas a devolver (1-100, por defecto 10).

    Returns:
        JSONResponse: Respuesta HTTP con el sensor y sus últimas lecturas.

    Raises:
        HTTPException: Si el sensor no existe o ocurre un error de comunicación.
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
    Recupera registros desde el CRM y devuelve sólo aquellos de tipo 'cliente'.

    Returns:
        JSONResponse: Respuesta HTTP con la lista de clientes validada contra el esquema unificado.

    Raises:
        HTTPException: Si la llamada al CRM falla o si la validación del esquema falla.
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
        JSONResponse: Respuesta JSON con los detalles del cliente.

    Raises:
        HTTPException: Si ocurre un error al comunicarse con el CRM o si el cliente no es encontrado.
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
    Recupera registros desde el CRM y devuelve sólo aquellos de tipo 'proveedor'.

    Returns:
        JSONResponse: Respuesta HTTP con la lista de proveedores validada contra el esquema unificado.

    Raises:
        HTTPException: Si la llamada al CRM falla o si la validación del esquema falla.
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
    Recupera información detallada de un proveedor por su nombre, junto con sensores asociados.

    Args:
        proveedor_nombre (str): Nombre del proveedor a buscar.

    Returns:
        JSONResponse: Respuesta JSON con los detalles del proveedor y sensores asociados.

    Raises:
        HTTPException: Si ocurre un error con el CRM o si el proveedor no es encontrado.
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
