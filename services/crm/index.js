const express = require('express');
const fs = require('fs');
const path = require('path');
const Ajv = require('ajv');
const addFormats = require('ajv-formats');

const app = express();

const BASE_DIR = __dirname;
const DATA_FILE = path.join(BASE_DIR, 'data', 'clientes.json');
const SCHEMA_FILE = path.resolve(BASE_DIR, '..', '..', 'schemas', 'ClienteProveedor.schema.json');

function loadClients() {
  const raw = fs.readFileSync(DATA_FILE, 'utf8');
  return JSON.parse(raw);
}

function loadSchema() {
  const raw = fs.readFileSync(SCHEMA_FILE, 'utf8');
  return JSON.parse(raw);
}

// Ajv como validador de esquemas
const ajv = new Ajv({ allErrors: true, strict: false });
addFormats(ajv);
const schema = loadSchema();
const validate = ajv.compile(schema);

function validateClient(obj) {
  const ok = validate(obj);
  if (!ok) {
    const first = (validate.errors && validate.errors[0]) || {};
    const where = first.instancePath || 'objeto';
    const message = first.message || 'inválido';
    const err = new Error(`Objeto inválido según schema: ${where} ${message}`);
    err.status = 500;
    throw err;
  }
}

function parsePositiveInt(value, fallback) {
  const n = Number.parseInt(value, 10);
  return Number.isFinite(n) && n > 0 ? n : fallback;
}

app.get('/clientes', (req, res) => {
  const q = typeof req.query.q === 'string' ? req.query.q : undefined;
  const ubicacionId = typeof req.query.ubicacionId === 'string' ? req.query.ubicacionId : undefined;
  const page = parsePositiveInt(req.query.page, 1);
  const pageSizeRaw = parsePositiveInt(req.query.pageSize, 25);
  const pageSize = Math.min(Math.max(pageSizeRaw, 1), 100);

  if (page < 1 || pageSize < 1 || pageSize > 100) {
    return res.status(400).json({ detail: 'Parámetros de paginación inválidos' });
  }

  let clients;
  try {
    clients = loadClients();
  } catch (e) {
    return res.status(500).json({ detail: `Error leyendo datos: ${e.message}` });
  }

  let filtered = clients;

  if (q) {
    const qLower = q.toLowerCase();
    filtered = filtered.filter((c) => {
      const nombre = (c && c.nombre) || '';
      const correo = (c && c.correo_electronico) || '';
      return nombre.toLowerCase().includes(qLower) || correo.toLowerCase().includes(qLower);
    });
  }

  if (ubicacionId) {
    filtered = filtered.filter((c) => String(c && c.direccion !== undefined ? c.direccion : '') === String(ubicacionId));
  }

  const total = filtered.length;
  const start = (page - 1) * pageSize;
  const end = start + pageSize;
  const pageData = filtered.slice(start, end);

  try {
    for (const client of pageData) {
      validateClient(client);
    }
  } catch (e) {
    const detail = e && e.message ? e.message : 'Error validando objetos';
    return res.status(500).json({ detail });
  }

  return res.json({ total, page, pageSize, data: pageData });
});

app.get('/clientes/:cliente_id', (req, res) => {
  let clients;
  try {
    clients = loadClients();
  } catch (e) {
    return res.status(500).json({ detail: `Error leyendo datos: ${e.message}` });
  }

  const clienteId = req.params.cliente_id;
  for (const client of clients) {
    if (client && client.id === clienteId) {
      try {
        validateClient(client);
      } catch (e) {
        const detail = e && e.message ? e.message : 'Error validando objeto';
        return res.status(500).json({ detail });
      }
      return res.json(client);
    }
  }

  return res.status(404).json({ detail: 'Cliente no encontrado' });
});

const PORT = process.env.PORT ? Number(process.env.PORT) : 8000;
app.listen(PORT, () => {
  console.log(`CRM corriendo en http://localhost:${PORT}`);
});




