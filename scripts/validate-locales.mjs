import { access, readdir, readFile } from "node:fs/promises";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

const localesDirectory = fileURLToPath(new URL("../locales/", import.meta.url));
const gameDirectory = fileURLToPath(new URL("../game-client/", import.meta.url));
const localeName = /^(?:[a-z]{2,3})(?:-[A-Z]{2})?$/;
const modules = JSON.parse(await readFile(join(localesDirectory, "modules.json"), "utf8"));
let hasErrors = false;

function parseCsv(text) {
  const rows = [];
  let row = [];
  let field = "";
  let quoted = false;
  for (let index = 0; index < text.length; index += 1) {
    const character = text[index];
    if (quoted) {
      if (character === '"' && text[index + 1] === '"') { field += '"'; index += 1; }
      else if (character === '"') quoted = false;
      else field += character;
    } else if (character === '"') {
      if (field.length > 0) throw new Error("Invalid quote placement");
      quoted = true;
    } else if (character === ",") {
      row.push(field); field = "";
    } else if (character === "\n") {
      row.push(field.endsWith("\r") ? field.slice(0, -1) : field);
      rows.push(row); row = []; field = "";
    } else field += character;
  }
  if (quoted) throw new Error("Unterminated quoted field");
  if (field.length > 0 || row.length > 0) {
    row.push(field.endsWith("\r") ? field.slice(0, -1) : field);
    rows.push(row);
  }
  return rows;
}

if (!Array.isArray(modules) || modules.some((module) => typeof module !== "string" || !/^[a-z][a-z0-9-]*(?:\/[a-z][a-z0-9-]*)*$/.test(module))) {
  console.error("locales/modules.json must contain valid locale module paths.");
  process.exit(1);
}

const englishKeys = new Set();
for (const module of modules) {
  const file = join(localesDirectory, "en", `${module}.json`);
  try {
    const english = JSON.parse(await readFile(file, "utf8"));
    for (const key of Object.keys(english)) englishKeys.add(key);
  } catch (error) {
    console.error(`${file}: missing or invalid English source module.`, error);
    hasErrors = true;
  }
}

const languageDirectories = (await readdir(localesDirectory, { withFileTypes: true }))
  .filter((entry) => entry.isDirectory())
  .map((entry) => entry.name);

for (const locale of languageDirectories) {
  if (!localeName.test(locale)) {
    console.error(`${locale}: use a BCP 47 locale directory, for example fr or pt-BR.`);
    hasErrors = true;
    continue;
  }

  for (const module of modules) {
    const file = join(localesDirectory, locale, `${module}.json`);
    try {
      await access(file);
    } catch {
      if (locale === "en") {
        console.error(`${file}: English must contain every locale module.`);
        hasErrors = true;
      }
      continue;
    }

    let messages;
    try {
      messages = JSON.parse(await readFile(file, "utf8"));
    } catch (error) {
      console.error(`${file}: invalid JSON.`, error);
      hasErrors = true;
      continue;
    }

    if (!messages || Array.isArray(messages) || typeof messages !== "object") {
      console.error(`${file}: a locale module must be a JSON object.`);
      hasErrors = true;
      continue;
    }

    for (const [key, value] of Object.entries(messages)) {
      if (!englishKeys.has(key)) {
        console.error(`${file}: unknown key \"${key}\".`);
        hasErrors = true;
      }
      if (typeof value !== "string" || value.trim().length === 0 || value.length > 1000) {
        console.error(`${file}: \"${key}\" must be a non-empty string of at most 1000 characters.`);
        hasErrors = true;
      }
    }
  }
}

for (const entry of await readdir(gameDirectory, { withFileTypes: true })) {
  if (!entry.isFile() || !entry.name.endsWith(".csv")) continue;
  const locale = entry.name.slice(0, -4);
  const file = join(gameDirectory, entry.name);
  if (!localeName.test(locale)) {
    console.error(`${file}: use a BCP 47 locale filename, for example fr.csv or pt-BR.csv.`);
    hasErrors = true;
    continue;
  }
  try {
    const rows = parseCsv((await readFile(file, "utf8")).replace(/^\uFEFF/, ""));
    if (rows[0]?.length !== 2 || rows[0][0] !== "message_id" || rows[0][1] !== "value") {
      throw new Error("header must be message_id,value");
    }
    const ids = new Set();
    for (const [index, row] of rows.slice(1).entries()) {
      if (row.length !== 2 || !/^\d+$/.test(row[0]) || !row[1]?.trim() || row[1].length > 8000 || row[1].includes("\uFFFD")) {
        throw new Error(`row ${index + 2} must contain a numeric message_id and a valid non-empty value of at most 8000 characters`);
      }
      if (ids.has(row[0])) throw new Error(`duplicate message_id ${row[0]}`);
      ids.add(row[0]);
    }
  } catch (error) {
    console.error(`${file}: invalid game translation CSV.`, error);
    hasErrors = true;
  }
}

if (hasErrors) process.exitCode = 1;
