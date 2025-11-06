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
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        raise RuntimeError(f"Error leyendo {path}: {e}")


@lru_cache(maxsize=1)
def load_schemas():
    lectura_schema = _load_json_file(SCHEMAS_DIR / "lectura.schema.json")
    sensor_schema = _load_json_file(SCHEMAS_DIR / "sensor.schema.json")
    return lectura_schema, sensor_schema


@lru_cache(maxsize=1)
def load_data():
    sensores = _load_json_file(DATA_DIR / "sensores.json")
    lecturas = _load_json_file(DATA_DIR / "lecturas.json")
    return sensores, lecturas


def parse_iso_datetime(value: str):
    try:
        # dateutil.isoparse handles Z as UTC
        return date_parser.isoparse(value)
    except Exception:
        raise ValueError(f"Fecha ISO inválida: {value}")


@app.get("/sensores")
def get_sensores(
    tipo: Optional[str] = Query(None), ubicacionId: Optional[str] = Query(None)
):
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

    return JSONResponse(content=results)


@app.get("/lecturas")
def get_lecturas(
    sensorId: Optional[str] = Query(None),
    ubicacionId: Optional[str] = Query(None),
    from_: Optional[str] = Query(None, alias="from"),
    to: Optional[str] = Query(None),
    limit: int = Query(100),
):
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

    return JSONResponse(content=to_return)


if __name__ == "__main__":
    run(app)
