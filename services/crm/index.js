/* 
======================================================================================
Nombre:
services/crm/index.js

Descripcion: 
Este paquete implementa un servicio CRM (Customer Relationship Management) que expone endpoints HTTP para la gestión y consulta de clientes.
Agrupa funciones para la lectura, filtrado, validación y paginación de datos de clientes, asegurando el cumplimiento de esquemas JSON y la correcta validación de parámetros de entrada.

Detalle:
  - readJson(filePath): Lee y parsea un archivo JSON desde disco.
  - loadSchemas(): Carga y retorna el esquema JSON de ClienteProveedor.
  - loadData(): Carga y retorna los datos de clientes desde un archivo JSON.
  - parsePositiveInt(value, fallback): Parsea un valor como entero positivo, o retorna un valor por defecto.
  - isPositiveIntString(value): Verifica si una cadena representa un entero positivo.
  - isNonEmptyString(value): Verifica si una cadena no está vacía.

Endpoints HTTP definidos:
  - GET /clientes: Lista clientes con soporte de búsqueda, paginación y filtro por ubicación.
  - GET /clientes/:cliente_id: Recupera un cliente por su ID.

---------------------------------------------------------------------------

HISTORICO DE CAMBIOS:
ISSUE         AUTOR              FECHA                   DESCRIPCION
--------      ---------          ---------------         ----------------------------------------------------------------------------------
I002          JAO                23-11-2025              Modificaciones para validación y paginación en el endpoint /clientes

======================================================================================
*/

const express = require("express");
const fs = require("fs");
const path = require("path");
const Ajv2020 = require("ajv/dist/2020");
const addFormats = require("ajv-formats");

const app = express();

const BASE_DIR = path.resolve(__dirname, "..", "..");
const SCHEMAS_DIR = path.join(BASE_DIR, "schemas");
const DATA_DIR = path.join(__dirname, "data");

/**
 * Lee y parsea un archivo JSON desde disco.
 * @param {string} filePath - Ruta al archivo JSON.
 * @returns {any} Objeto resultante del parseo JSON.
 * @throws {Error} Error con propiedad status=500 si ocurre un error de lectura o parseo.
 */
function readJson(filePath) {
  try {
    const raw = fs.readFileSync(filePath, "utf8");
    return JSON.parse(raw);
  } catch (e) {
    const err = new Error(`Error leyendo ${filePath}: ${e.message}`);
    err.status = 500;
    throw err;
  }
}

/**
 * Carga y retorna los esquemas JSON necesarios (ClienteProveedor).
 * @returns {{lecturaSchema: Object}} Objeto con los esquemas cargados.
 * @throws {Error} Propaga errores de lectura desde readJson.
 */
function loadSchemas() {
  const lecturaSchema = readJson(
    path.join(SCHEMAS_DIR, "ClienteProveedor.schema.json")
  );
  return { lecturaSchema };
}

/**
 * Carga y retorna los datos de clientes desde el directorio de datos.
 * @returns {Array<Object>} Lista de clientes.
 * @throws {Error} Propaga errores de lectura desde readJson.
 */
function loadData() {
  const clientes = readJson(path.join(DATA_DIR, "clientes.json"));
  return clientes;
}

// Ajv como validador de esquemas
const ajv = new Ajv2020({ strict: false, allErrors: true });
addFormats(ajv);
const { lecturaSchema } = loadSchemas();
const validateLectura = ajv.compile(lecturaSchema);

function parsePositiveInt(value, fallback) {
  const n = Number.parseInt(value, 10);
  return Number.isFinite(n) && n > 0 ? n : fallback;
}

/**
 * Comprueba si una cadena representa un entero positivo (sin signo).
 * @param {any} value - Valor a comprobar.
 * @returns {boolean} True si es una cadena que representa un entero positivo.
 */
function isPositiveIntString(value) {
  if (typeof value !== "string") return false;
  return /^[1-9]\d*$/.test(value);
}

/**
 * Comprueba si un valor es una cadena no vacía (trimmed).
 * @param {any} value - Valor a comprobar.
 * @returns {boolean} True si es una cadena no vacía.
 */
function isNonEmptyString(value) {
  return typeof value === "string" && value.trim() !== "";
}

/**
 * Handler GET /clientes
 * Lista clientes con soporte de búsqueda (q), paginación (page,pageSize) y filtro por ubicacionId.
 * Valida parámetros de query y cada cliente contra el esquema antes de devolver la página.
 */
app.get("/clientes", (req, res) => {
  const q = typeof req.query.q === "string" ? req.query.q : undefined;
  const ubicacionId =
    typeof req.query.ubicacionId === "string"
      ? req.query.ubicacionId
      : undefined;

  // Validaciones adicionales: devolver 400 si los parámetros presentes no cumplen formato esperado
  if (req.query.q !== undefined && !isNonEmptyString(req.query.q)) {
    return res.status(400).json({ detail: "Parámetro q inválido" });
  }
  if (req.query.ubicacionId !== undefined && req.query.ubicacionId === "") {
    return res.status(400).json({ detail: "Parámetro ubicacionId inválido" });
  }

  // validar page (si viene)
  if (
    req.query.page !== undefined &&
    !isPositiveIntString(String(req.query.page))
  ) {
    return res.status(400).json({ detail: "Parámetro page inválido" });
  }

  // validar pageSize (si viene): debe ser entero positivo y <= 100 -> si no, 400
  if (req.query.pageSize !== undefined) {
    if (!isPositiveIntString(String(req.query.pageSize))) {
      return res.status(400).json({ detail: "Parámetro pageSize inválido" });
    }
    const ps = Number.parseInt(String(req.query.pageSize), 10);
    if (ps > 100) {
      return res
        .status(400)
        .json({ detail: "Parámetro pageSize inválido: máximo 100" });
    }
  }

  const page = parsePositiveInt(req.query.page, 1);
  const pageSizeRaw = parsePositiveInt(req.query.pageSize, 25);
  const pageSize = Math.min(Math.max(pageSizeRaw, 1), 100);

  if (page < 1 || pageSize < 1 || pageSize > 100) {
    return res
      .status(400)
      .json({ detail: "Parámetros de paginación inválidos" });
  }

  let clients;
  try {
    clients = loadData();
  } catch (e) {
    return res
      .status(500)
      .json({ detail: `Error leyendo datos: ${e.message}` });
  }

  let filtered = clients;

  if (q) {
    const qLower = q.toLowerCase();
    filtered = filtered.filter((c) => {
      const nombre = (c && c.nombre) || "";
      const correo = (c && c.correo_electronico) || "";
      return (
        nombre.toLowerCase().includes(qLower) ||
        correo.toLowerCase().includes(qLower)
      );
    });
  }

  if (ubicacionId) {
    filtered = filtered.filter(
      (c) =>
        String(c && c.direccion !== undefined ? c.direccion : "") ===
        String(ubicacionId)
    );
  }

  const total = filtered.length;
  const start = (page - 1) * pageSize;
  const end = start + pageSize;
  const pageData = filtered.slice(start, end);

  try {
    for (const l of pageData) {
      const ok = validateLectura(l);
      if (!ok) {
        const first =
          (validateLectura.errors && validateLectura.errors[0]) || {};
        const msg = first.message || "no conforme";
        throw new Error(`Lectura no conforme al schema: ${msg}`);
      }
    }
  } catch (e) {
    return res.status(500).json({ detail: e.message });
  }

  return res.json({ total, page, pageSize, data: pageData });
});

/**
 * Handler GET /clientes/:cliente_id
 * Devuelve un cliente por su id. Valida el parámetro de ruta y el objeto cliente contra el esquema.
 */
app.get("/clientes/:cliente_id", (req, res) => {
  // validar parámetro de ruta
  const clienteId = req.params.cliente_id;
  if (!isNonEmptyString(clienteId)) {
    return res.status(400).json({ detail: "Parámetro cliente_id inválido" });
  }

  let clients;
  try {
    clients = loadData();
  } catch (e) {
    return res
      .status(500)
      .json({ detail: `Error leyendo datos: ${e.message}` });
  }

  for (const client of clients) {
    if (client && client.id === clienteId) {
      try {
        const ok = validateLectura(client);
        if (!ok) {
          const first =
            (validateLectura.errors && validateLectura.errors[0]) || {};
          const msg = first.message || "no conforme";
          throw new Error(`Lectura no conforme al schema: ${msg}`);
        }
      } catch (e) {
        return res.status(500).json({ detail: e.message });
      }
      return res.json(client);
    }
  }

  return res.status(404).json({ detail: "Cliente no encontrado" });
});

// const PORT = process.env.PORT ? Number(process.env.PORT) : 8000;
const PORT = 3001;
app.listen(PORT, () => {
  console.log(`CRM corriendo en http://localhost:${PORT}`);
});
