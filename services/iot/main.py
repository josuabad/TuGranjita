"""
======================================================================================
Nombre:
services/iot/main.py

Descripcion:
Este paquete implementa un servicio IoT (Internet of Things) que expone endpoints HTTP para la gestión y consulta de sensores y lecturas de sensores.
Incluye funciones para la lectura, filtrado, validación y paginación de datos de sensores y lecturas, asegurando el cumplimiento de esquemas JSON y la correcta validación de parámetros de entrada.

Detalle:
    - _load_json_file(path: Path): Lee y carga un archivo JSON desde el disco.
    - load_schemas(): Carga y cachea los esquemas JSON de lectura y sensor.
    - load_data(): Carga y cachea los datos de sensores y lecturas.
    - parse_iso_datetime(value: str): Parsea una cadena ISO a objeto datetime.
    - get_sensores(tipo: Optional[str], ubicacionId: Optional[str]): Endpoint GET /sensores, filtra y valida sensores.
    - get_lecturas(sensorId: Optional[str], ubicacionId: Optional[str], from_: Optional[str], to: Optional[str], limit: int): Endpoint GET /lecturas, filtra, valida y pagina lecturas.

Endpoints HTTP definidos:
    - GET /sensores: Recupera y filtra sensores según parámetros de consulta (tipo, ubicacionId).
    - GET /lecturas: Recupera y filtra lecturas según parámetros de consulta (sensorId, ubicacionId, from, to, limit), incluyendo validación de fechas y paginación.

---------------------------------------------------------------------------

HISTORICO DE CAMBIOS:
ISSUE         AUTOR              FECHA                   DESCRIPCION
--------      ---------          ---------------         ----------------------------------------------------------------------------------
I002          JAO                23-11-2025              Implementación de endpoints y validaciones para sensores y lecturas IoT

======================================================================================
"""

from typing import List, Optional
import json
from pathlib import Path
from functools import lru_cache
from uvicorn import run
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
import jsonschema
from dateutil import parser as date_parser


BASE_DIR = Path(__file__).resolve().parents[2]
SCHEMAS_DIR = BASE_DIR / "schemas"
DATA_DIR = Path(__file__).resolve().parents[0] / "data"

app = FastAPI(title="IoT Service")


def _load_json_file(path: Path):
    """
    Lee y carga un archivo JSON desde disco.

    Args:
        path (Path): Ruta al archivo JSON.

    Returns:
        Any: Contenido parseado del archivo JSON.

    Raises:
        RuntimeError: Si falla la lectura o el parseo del archivo.
    """
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        raise RuntimeError(f"Error leyendo {path}: {e}")


@lru_cache(maxsize=1)
def load_schemas():
    """
    Carga y cachea los esquemas JSON utilizados para validar lecturas y sensores.

    Returns:
        tuple: (lectura_schema, sensor_schema) ambos como diccionarios Python.

    Raises:
        RuntimeError: Si falla la lectura de alguno de los archivos de esquema.
    """
    lectura_schema = _load_json_file(SCHEMAS_DIR / "LecturaSensor.schema.json")
    sensor_schema = _load_json_file(SCHEMAS_DIR / "SensorIoT.schema.json")
    return lectura_schema, sensor_schema


@lru_cache(maxsize=1)
def load_data():
    """
    Carga y cachea los datos de sensores y lecturas desde el directorio DATA_DIR.

    Returns:
        tuple: (sensores, lecturas) donde cada elemento es la lista correspondiente.

    Raises:
        RuntimeError: Si falla la lectura de los archivos de datos.
    """
    sensores = _load_json_file(DATA_DIR / "sensores.json")
    lecturas = _load_json_file(DATA_DIR / "lecturas.json")
    return sensores, lecturas


def parse_iso_datetime(value: str):
    """
    Parsea una cadena de fecha ISO a un objeto datetime.

    Args:
        value (str): Cadena en formato ISO (por ejemplo "2025-11-23T12:34:56Z").

    Returns:
        datetime: Objeto datetime correspondiente.

    Raises:
        ValueError: Si la cadena no es una fecha ISO válida.
    """
    try:
        # dateutil.isoparse handles Z as UTC
        return date_parser.isoparse(value)
    except Exception:
        raise ValueError(f"Fecha ISO inválida: {value}")


@app.get("/sensores")
def get_sensores(
    tipo: Optional[str] = Query(None), ubicacionId: Optional[str] = Query(None)
):
    """
    Endpoint GET /sensores: recupera sensores filtrando por tipo y/o ubicacionId,
    valida cada sensor contra el schema correspondiente y devuelve la lista.

    Args:
        tipo (Optional[str]): Filtro por tipo de sensor.
        ubicacionId (Optional[str]): Filtro por id de ubicación.

    Returns:
        JSONResponse: Respuesta con estructura {status, message, params, total, sensores}.

    Raises:
        HTTPException: 500 en caso de errores de lectura o validación.
    """
    try:
        sensores, _ = load_data()
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

    results = sensores
    if tipo is not None:
        results = [s for s in results if s.get("tipo") == tipo]
    if ubicacionId is not None:
        # match against the 'ubicacion' field
        results = [s for s in results if s.get("ubicacion") == ubicacionId]

    _, sensor_schema = load_schemas()
    format_checker = jsonschema.FormatChecker()

    # Validate each lectura to be returned against schema
    try:
        for l in results:
            jsonschema.validate(
                instance=l, schema=sensor_schema, format_checker=format_checker
            )
    except jsonschema.ValidationError as e:
        # return 500 if any reading doesn't conform
        raise HTTPException(
            status_code=500, detail=f"Lectura no conforme al schema: {e.message}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    total = len(results)
    response = {
        "status": "success",
        "message": "Sensores recuperados correctamente",
        "params": {"tipo": tipo, "ubicacionId": ubicacionId},
        "total": total,
        "sensores": results,
    }

    return JSONResponse(content=response)


@app.get("/lecturas")
def get_lecturas(
    sensorId: Optional[str] = Query(None),
    ubicacionId: Optional[str] = Query(None),
    from_: Optional[str] = Query(None, alias="from"),
    to: Optional[str] = Query(None),
    limit: int = Query(100),
):
    """
    Endpoint GET /lecturas: devuelve lecturas filtradas por sensorId, ubicacionId,
    rango temporal (from/to) y con límite de resultados. Realiza validaciones
    de formato de fecha y de esquema JSON para cada lectura devuelta.

    Args:
        sensorId (Optional[str]): Filtro por id de sensor.
        ubicacionId (Optional[str]): Filtro por id de ubicación.
        from_ (Optional[str]): Fecha ISO mínima (alias 'from').
        to (Optional[str]): Fecha ISO máxima.
        limit (int): Límite de lecturas a devolver (1..1000).

    Returns:
        JSONResponse: Respuesta con estructura {status, message, params, total, lecturas}.

    Raises:
        HTTPException: 400 por parámetros inválidos, 500 por errores de lectura/validación.
    """
    # Validate limit
    if limit <= 0 or limit > 1000:
        raise HTTPException(
            status_code=400, detail="'limit' debe ser entero entre 1 y 1000"
        )

    try:
        sensores, lecturas = load_data()
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

    lectura_schema, _ = load_schemas()
    format_checker = jsonschema.FormatChecker()

    # Apply filters in order: sensorId -> ubicacionId -> from -> to
    filtered = lecturas

    if sensorId is not None:
        filtered = [l for l in filtered if l.get("id_sensor") == sensorId]

    if ubicacionId is not None:
        # need to map sensor id to ubicacion via sensores list
        sensor_ubic_map = {s.get("id"): s.get("ubicacion") for s in sensores}
        filtered = [
            l
            for l in filtered
            if sensor_ubic_map.get(l.get("id_sensor")) == ubicacionId
        ]

    # Parse from/to if present
    dt_from = None
    dt_to = None
    try:
        if from_ is not None:
            dt_from = parse_iso_datetime(from_)
        if to is not None:
            dt_to = parse_iso_datetime(to)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if dt_from is not None and dt_to is not None and dt_from > dt_to:
        raise HTTPException(
            status_code=400, detail="'from' no puede ser mayor que 'to'"
        )

    if dt_from is not None:
        tmp = []
        for l in filtered:
            try:
                ts = parse_iso_datetime(l.get("timestamp"))
            except Exception:
                # timestamp in data invalid -> treat as server error
                raise HTTPException(
                    status_code=500,
                    detail=f"Timestamp inválido en lectura {l.get('id_lectura')}",
                )
            if ts >= dt_from:
                tmp.append(l)
        filtered = tmp

    if dt_to is not None:
        tmp = []
        for l in filtered:
            try:
                ts = parse_iso_datetime(l.get("timestamp"))
            except Exception:
                raise HTTPException(
                    status_code=500,
                    detail=f"Timestamp inválido en lectura {l.get('id_lectura')}",
                )
            if ts <= dt_to:
                tmp.append(l)
        filtered = tmp

    # Trim to limit
    to_return = filtered[:limit]

    # Validate each lectura to be returned against schema
    try:
        for l in to_return:
            jsonschema.validate(
                instance=l, schema=lectura_schema, format_checker=format_checker
            )
    except jsonschema.ValidationError as e:
        # return 500 if any reading doesn't conform
        raise HTTPException(
            status_code=500, detail=f"Lectura no conforme al schema: {e.message}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    total = len(filtered)
    response = {
        "status": "success",
        "message": "Lecturas recuperadas correctamente",
        "params": {
            "sensorId": sensorId,
            "ubicacionId": ubicacionId,
            "from": from_,
            "to": to,
            "limit": limit,
        },
        "total": total,
        "lecturas": to_return,
    }

    return JSONResponse(content=response)


if __name__ == "__main__":
    run(app)
