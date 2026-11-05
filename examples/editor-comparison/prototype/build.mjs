import { build } from 'esbuild';
import { mkdir, readFile, writeFile, readdir } from 'node:fs/promises';
import { resolve, dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { gzipSync } from 'node:zlib';
const here = dirname(fileURLToPath(import.meta.url));
const source = resolve(process.argv[2] || join(here, '../../..'));
const dist = join(here, 'dist');
await mkdir(dist, { recursive: true });
const schemas = {};
for (const kind of ['repository-governance', 'large-change']) {
  const schema = JSON.parse(await readFile(join(source, 'src/ergora/data/reference/platform/templates', kind, 'input.schema.json'), 'utf8'));
  schemas[kind] = schema.properties.input;
}
await writeFile(join(dist, 'schemas.json'), JSON.stringify(schemas));
const html = await readFile(join(here, 'index.html'), 'utf8');
const records = {};
for (const entry of ['native', 'flow', 'schema']) {
  const result = await build({
    absWorkingDir: here, entryPoints: [join(here, entry + '.jsx')],
    outfile: join(dist, entry + '.js'), bundle: true, minify: true,
    format: 'esm', target: 'es2022', metafile: true, legalComments: 'linked',
    define: { 'process.env.NODE_ENV': '"production"' },
    alias: { '@ergora/cytoscape': join(source, 'src/ergora/data/console/vendor/cytoscape.min.js'),
      '@ergora/api': join(source, 'src/ergora/data/console/api.js') },
  });
  await writeFile(join(dist, entry + '.html'), html.replaceAll('ENTRY', entry));
  const assets = {};
  for (const name of [entry+'.html', entry+'.js', entry+'.css', entry+'.js.LEGAL.txt', 'schemas.json']) {
    const raw = await readFile(join(dist, name));
    assets[name] = { bytes: raw.length, gzip_bytes: gzipSync(raw).length };
  }
  records[entry] = { assets, input_modules: Object.keys(result.metafile.inputs).length };
}
await writeFile(join(dist, 'build-sizes.json'), JSON.stringify({
  scope: 'Three independent complete entrypoints; each includes its shared CSS/schema. API payloads and HTTP compression are separate.', entries: records,
}, null, 2)+'\n');
console.log(JSON.stringify(records, null, 2));

const dependencyRoot = resolve(here, '..');
const lock = JSON.parse(await readFile(join(dependencyRoot, 'package-lock.json'), 'utf8'));
const notices = ['Cytoscape 3.33.1\n' + await readFile(join(source, 'src/ergora/data/console/vendor/CYTOSCAPE-LICENSE.txt'), 'utf8')];
for (const name of Object.keys(lock.packages).filter(name => name.startsWith('node_modules/'))) {
  const directory = join(dependencyRoot, name);
  let entries;
  try { entries = await readdir(directory); }
  catch (error) { if (error.code === 'ENOENT') continue; throw error; }
  const metadata = JSON.parse(await readFile(join(directory, 'package.json'), 'utf8'));
  const licenseFiles = entries.filter(file => /^(license|copying|notice)(\.|$)/i.test(file));
  const sections = await Promise.all(licenseFiles.map(file => readFile(join(directory, file), 'utf8')));
  if (metadata.name.startsWith('@esbuild/') && !sections.length) {
    sections.push(await readFile(join(dependencyRoot, 'node_modules/esbuild/LICENSE.md'), 'utf8'));
  }
  if (!sections.length) throw new Error('No distributable license text: ' + metadata.name);
  notices.push(metadata.name + ' ' + metadata.version + ' (' + metadata.license + ')\n' + sections.join('\n'));
}
await writeFile(join(dist, 'THIRD_PARTY_LICENSES.txt'), notices.join('\n\n====================\n\n'));
