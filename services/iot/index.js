const express = require('express');
const fs = require('fs');
const path = require('path');
const Ajv2020 = require('ajv/dist/2020');
const addFormats = require('ajv-formats');

const app = express();

const BASE_DIR = path.resolve(__dirname, '..', '..');
const SCHEMAS_DIR = path.join(BASE_DIR, 'schemas');
const DATA_DIR = path.join(__dirname, 'data');

function readJson(filePath) {
  try {
    const raw = fs.readFileSync(filePath, 'utf8');
    return JSON.parse(raw);
  } catch (e) {
    const err = new Error(`Error leyendo ${filePath}: ${e.message}`);
    err.status = 500;
    throw err;
  }
}

function loadSchemas() {
  const lecturaSchema = readJson(path.join(SCHEMAS_DIR, 'LecturaSensor.schema.json'));
  const sensorSchema = readJson(path.join(SCHEMAS_DIR, 'SensorIoT.schema.json'));
  return { lecturaSchema, sensorSchema };
}

function loadData() {
  const sensores = readJson(path.join(DATA_DIR, 'sensores.json'));
  const lecturas = readJson(path.join(DATA_DIR, 'lecturas.json'));
  return { sensores, lecturas };
}

function parseIsoDatetime(value) {
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) {
    const err = new Error(`Fecha ISO inválida: ${value}`);
    err.status = 400;
    throw err;
  }
  return d;
}

// Ajv como validador de esquemas
const ajv = new Ajv2020({ strict: false, allErrors: true });
addFormats(ajv);
const { lecturaSchema } = loadSchemas();
const validateLectura = ajv.compile(lecturaSchema);

app.get('/sensores', (req, res) => {
  const tipo = typeof req.query.tipo === 'string' ? req.query.tipo : undefined;
  const ubicacionId = typeof req.query.ubicacionId === 'string' ? req.query.ubicacionId : undefined;

  let sensores;
  try {
    ({ sensores } = loadData());
  } catch (e) {
    const status = e.status || 500;
    return res.status(status).json({ detail: e.message });
  }

  let results = sensores;
  if (tipo !== undefined) {
    results = results.filter((s) => s && s.tipo === tipo);
  }
  if (ubicacionId !== undefined) {
    results = results.filter((s) => s && s.ubicacion === ubicacionId);
  }

  const total = results.length;
  const response = {
    status: 'success',
    message: 'Sensores recuperados correctamente',
    params: { tipo, ubicacionId },
    total,
    sensores: results,
  };
  return res.json(response);
});

app.get('/lecturas', (req, res) => {
  const sensorId = typeof req.query.sensorId === 'string' ? req.query.sensorId : undefined;
  const ubicacionId = typeof req.query.ubicacionId === 'string' ? req.query.ubicacionId : undefined;
  const limitRaw = Number.parseInt(String(req.query.limit ?? '100'), 10);
  const limit = Number.isFinite(limitRaw) ? limitRaw : 100;

  if (limit <= 0 || limit > 1000) {
    return res.status(400).json({ detail: "'limit' debe ser entero entre 1 y 1000" });
  }

  let sensores;
  let lecturas;
  try {
    ({ sensores, lecturas } = loadData());
  } catch (e) {
    const status = e.status || 500;
    return res.status(status).json({ detail: e.message });
  }

  let filtered = lecturas;
  if (sensorId !== undefined) {
    filtered = filtered.filter((l) => l && l.id_sensor === sensorId);
  }

  if (ubicacionId !== undefined) {
    const sensorUbicMap = {};
    for (const s of sensores) {
      sensorUbicMap[s && s.id] = s && s.ubicacion;
    }
    filtered = filtered.filter((l) => sensorUbicMap[l && l.id_sensor] === ubicacionId);
  }

  const fromStr = typeof req.query.from === 'string' ? req.query.from : undefined;
  const toStr = typeof req.query.to === 'string' ? req.query.to : undefined;

  let dtFrom = undefined;
  let dtTo = undefined;
  try {
    if (fromStr !== undefined) dtFrom = parseIsoDatetime(fromStr);
    if (toStr !== undefined) dtTo = parseIsoDatetime(toStr);
  } catch (e) {
    const status = e.status || 400;
    return res.status(status).json({ detail: e.message });
  }

  if (dtFrom !== undefined && dtTo !== undefined && dtFrom > dtTo) {
    return res.status(400).json({ detail: "'from' no puede ser mayor que 'to'" });
  }

  if (dtFrom !== undefined) {
    const tmp = [];
    for (const l of filtered) {
      try {
        const ts = parseIsoDatetime(l && l.timestamp);
        if (ts >= dtFrom) tmp.push(l);
      } catch (e) {
        return res
          .status(500)
          .json({ detail: `Timestamp inválido en lectura ${l && l.id_lectura}` });
      }
    }
    filtered = tmp;
  }

  if (dtTo !== undefined) {
    const tmp = [];
    for (const l of filtered) {
      try {
        const ts = parseIsoDatetime(l && l.timestamp);
        if (ts <= dtTo) tmp.push(l);
      } catch (e) {
        return res
          .status(500)
          .json({ detail: `Timestamp inválido en lectura ${l && l.id_lectura}` });
      }
    }
    filtered = tmp;
  }

  const total = filtered.length;
  const toReturn = filtered.slice(0, limit);

  try {
    for (const l of toReturn) {
      const ok = validateLectura(l);
      if (!ok) {
        const first = (validateLectura.errors && validateLectura.errors[0]) || {};
        const msg = first.message || 'no conforme';
        throw new Error(`Lectura no conforme al schema: ${msg}`);
      }
    }
  } catch (e) {
    return res.status(500).json({ detail: e.message });
  }

  const response = {
    status: 'success',
    message: 'Lecturas recuperadas correctamente',
    params: {
      sensorId,
      ubicacionId,
      from: fromStr,
      to: toStr,
      limit,
    },
    total,
    lecturas: toReturn,
  };
  return res.json(response);
});

const PORT = process.env.PORT ? Number(process.env.PORT) : 8000;
app.listen(PORT, () => {
  // eslint-disable-next-line no-console
  console.log(`IoT corriendo en http://localhost:${PORT}`);
});


