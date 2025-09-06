#!/usr/bin/env node
import fs from "node:fs/promises";
import path from "node:path";
import $RefParser from "@apidevtools/json-schema-ref-parser";
import { fileURLToPath } from "node:url";
import { schemaVersion } from "./lib/version.mjs";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, "..");
const SCHEMA_DIR = path.join(ROOT, "jsonschema");
const OUT_DIR = path.join(ROOT, "typescript", "tmp", "bundled");
await fs.mkdir(OUT_DIR, { recursive: true });

// Map canonical HTTP $id → local file in jsonschema/
const BASE = `https://schemas.synesthetic.dev/${schemaVersion()}/`;
const synIdResolver = {
  order: 1,
  canRead(file) {
    return typeof file.url === "string" && file.url.startsWith(BASE);
  },
  async read(file) {
    const name = decodeURIComponent(file.url.slice(BASE.length)); // e.g. "control.schema.json"
    const p = path.join(SCHEMA_DIR, name);
    return fs.readFile(p, "utf8");
  },
};

const files = (await fs.readdir(SCHEMA_DIR))
  .filter((f) => f.endsWith(".schema.json"))
  .sort();

for (const f of files) {
  const abs = path.join(SCHEMA_DIR, f);

  const bundled = await $RefParser.bundle(abs, {
    resolve: {
      // never hit the network
      http: false,
      // support normal local refs like "./control.schema.json"
      file: { order: 2 },
      // register our custom resolver by name
      syn_id: synIdResolver,
    },
  });

  // Workaround: json-schema-ref-parser percent-encodes "$" in JSON Pointer fragments
  // (e.g. "#/.../%24defs/..."). Some downstream tools (datamodel-code-generator)
  // expect plain "$defs" fragments. Normalize refs in the bundled output.
  const decodeRefFragments = (obj) => {
    if (!obj || typeof obj !== 'object') return;
    for (const [k, v] of Object.entries(obj)) {
      if (k === '$ref' && typeof v === 'string' && v.startsWith('#')) {
        obj[k] = v.replaceAll('%24', '$');
      } else if (v && typeof v === 'object') {
        decodeRefFragments(v);
      }
    }
  };
  decodeRefFragments(bundled);

  const out = path.join(OUT_DIR, f);
  await fs.writeFile(out, JSON.stringify(bundled, null, 2) + "\n");
  console.log(`bundled: ${f} → ${path.relative(ROOT, out)}`);
}
