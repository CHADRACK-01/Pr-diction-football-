const fs = require("fs");
const path = require("path");

const root = path.resolve(__dirname, "..");
const features = new Map();

const sourcePath = path.join(root, "core", "catalog", "catalogue_fonctionnalites.py");
const source = fs.readFileSync(sourcePath, "utf8");
const basePattern = /\("(\d+)"\s*,\s*"([^"]+)"\s*,\s*"([^"]+)"\s*,\s*"([^"]+)"\)/g;
for (const match of source.matchAll(basePattern)) {
  const id = Number(match[1]);
  features.set(id, {
    id,
    name: match[2],
    group: match[3],
    status: match[4],
    source: "core/catalog/catalogue_fonctionnalites.py",
  });
}

const docs = [
  "docs/03_Fonctionnalites_138_a_274.txt",
  "docs/04_Fonctionnalites_275_a_411.txt",
  "docs/05_Fonctionnalites_412_a_547.txt",
  "docs/06_Fonctionnalites_548_a_624.txt",
  "docs/07_Fonctionnalites_625_a_700.txt",
];

for (const relative of docs) {
  const text = fs.readFileSync(path.join(root, relative), "utf8");
  for (const line of text.split(/\r?\n/)) {
    const match = line.match(/^\s*(\d{3})\s*(?:[.]|[—-])\s*(.+)$/);
    if (!match) continue;
    const id = Number(match[1]);
    let name = match[2].replace(/:.*/, "").trim();
    if (name.length > 180) name = name.slice(0, 180).trim();
    if (!features.has(id)) {
      features.set(id, {
        id,
        name,
        group: "Extension",
        status: "a_implanter",
        source: relative,
      });
    }
  }
}

const completeIds = new Set([
  138,139,149,150,163,164,165,168,179,182,186,187,188,189,190,193,
  413,414,416,417,418,422,423,424,432,433,434,435,436,437,438,439,
  444,445,446,447,448,449,450,455,456,464,465,466,467,625,627,628,
  631,632,633,634,635,637,638,639,640,641,642,643,645,646,647,648,649,
]);

for (const id of completeIds) {
  if (features.has(id)) features.get(id).status = "complete";
}

const missing = [];
for (let id = 1; id <= 700; id++) {
  if (!features.has(id)) missing.push(id);
}
if (missing.length) throw new Error(`Fonctionnalités manquantes: ${missing.join(", ")}`);

const items = Array.from({ length: 700 }, (_, index) => features.get(index + 1));

const lines = [
  "# Inventaire officiel des 700 fonctionnalités",
  "",
  "Source unique avant implémentation : catalogue central + fichiers documentaires 138-700.",
  "",
  "| ID | Fonctionnalité | Groupe | Statut | Source |",
  "|---:|---|---|---|---|",
];
for (const item of items) {
  const name = item.name.replace(/\|/g, "\\|");
  const group = item.group.replace(/\|/g, "\\|");
  lines.push(`| ${item.id} | ${name} | ${group} | ${item.status} | ${item.source} |`);
}

fs.writeFileSync(path.join(root, "docs", "700_FONCTIONNALITES.md"), lines.join("\n") + "\n", "utf8");
fs.writeFileSync(path.join(root, "docs", "700_FONCTIONNALITES.json"), JSON.stringify(items, null, 2) + "\n", "utf8");

console.log(`Inventaire 1-700 généré : ${items.length} fonctionnalités`);
