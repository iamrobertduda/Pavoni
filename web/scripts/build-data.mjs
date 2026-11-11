// data/*.yaml + build/manifest.json -> src/generated/data.json (validated with the JSON schemas).
import Ajv2020 from 'ajv/dist/2020.js';
import { load as yamlLoad } from 'js-yaml';
import { existsSync, mkdirSync, readFileSync, readdirSync, writeFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const repo = resolve(here, '..', '..');
const dataDir = join(repo, 'data');
const schemaDir = join(dataDir, 'schema');
const manifestPath = join(repo, 'build', 'manifest.json');
const out = join(here, '..', 'src', 'generated', 'data.json');

const ajv = new Ajv2020({ allErrors: true, strict: false });
for (const f of readdirSync(schemaDir)) ajv.addSchema(JSON.parse(readFileSync(join(schemaDir, f), 'utf8')));

function load(name, schema, fallback) {
  const doc = yamlLoad(readFileSync(join(dataDir, name), 'utf8')) ?? fallback;
  const validate = ajv.getSchema(`${schema}.schema.json`);
  if (!validate(doc)) {
    console.error(`${name}:`, ajv.errorsText(validate.errors, { separator: '\n  ' }));
    process.exit(1);
  }
  return doc;
}

const parts = load('parts.yaml', 'parts', []);
const assemblies = load('assemblies.yaml', 'assemblies', []);
const tools = load('tools.yaml', 'tools', []);
const views = load('views.yaml', 'views', { views: {}, sections: {} });
const dimensions = load('dimensions.yaml', 'dimensions', {});
const procedures = readdirSync(join(dataDir, 'procedures'))
  .filter((f) => f.endsWith('.yaml'))
  .sort()
  .map((f) => load(join('procedures', f), 'procedure', {}))
  .sort((a, b) => (a.order ?? 99) - (b.order ?? 99));

if (!existsSync(manifestPath)) {
  console.error('build/manifest.json fehlt - zuerst "make cad" ausführen');
  process.exit(1);
}
const manifest = JSON.parse(readFileSync(manifestPath, 'utf8'));

const result = {
  generated: manifest.generated,
  git: manifest.git,
  machine: dimensions.machine,
  parts,
  assemblies,
  tools,
  procedures,
  views: views.views,
  sections: views.sections,
  dims: manifest.dims,
  instances: manifest.instances,
  assemblyGeo: manifest.assemblies,
};
mkdirSync(dirname(out), { recursive: true });
writeFileSync(out, JSON.stringify(result));
console.log(`build-data: ${parts.length} Teile, ${Object.keys(manifest.instances).length} gebaute Instanzen, ${procedures.length} Anleitungen -> src/generated/data.json`);
