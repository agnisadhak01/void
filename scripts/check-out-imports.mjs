import fs from 'fs';
import path from 'path';

const root = path.resolve('out');
const entry = path.join(root, 'vs/workbench/workbench.desktop.main.js');
const missing = new Map(); // missingPath -> importerPath
const visited = new Set();

function check(file, importer = null) {
	file = file.replace(/\\/g, '/');
	const key = file;
	if (visited.has(key)) return;
	visited.add(key);
	if (!fs.existsSync(file)) {
		if (!missing.has(file)) missing.set(file, new Set());
		if (importer) missing.get(file).add(importer);
		return;
	}
	const text = fs.readFileSync(file, 'utf8');
	const importRe = /(?:from|import)\s+['"](\.\.?\/[^'"]+)['"]/g;
	for (const m of text.matchAll(importRe)) {
		const rel = m[1];
		if (!rel.endsWith('.js')) continue;
		check(path.resolve(path.dirname(file), rel).replace(/\\/g, '/'), file);
	}
}

check(entry);
console.log('visited', visited.size);
console.log('missing', missing.size);
for (const [miss, importers] of missing) {
	console.log('\nMISSING:', miss);
	for (const imp of importers) console.log('  imported by:', imp);
}
