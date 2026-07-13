import { readdir, readFile } from "node:fs/promises";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

const localesDirectory = fileURLToPath(new URL("../locales/", import.meta.url));
const localeName = /^(?:[a-z]{2,3})(?:-[A-Z]{2})?\.json$/;
const english = JSON.parse(await readFile(join(localesDirectory, "en.json"), "utf8"));
const englishKeys = new Set(Object.keys(english));
const files = (await readdir(localesDirectory)).filter((file) => file.endsWith(".json"));
let hasErrors = false;

for (const file of files) {
  if (!localeName.test(file)) {
    console.error(`${file}: use a BCP 47 locale filename, for example fr.json or pt-BR.json.`);
    hasErrors = true;
    continue;
  }

  let locale;
  try {
    locale = JSON.parse(await readFile(join(localesDirectory, file), "utf8"));
  } catch (error) {
    console.error(`${file}: invalid JSON.`, error);
    hasErrors = true;
    continue;
  }

  if (!locale || Array.isArray(locale) || typeof locale !== "object") {
    console.error(`${file}: a locale must be a JSON object.`);
    hasErrors = true;
    continue;
  }

  for (const [key, value] of Object.entries(locale)) {
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

if (hasErrors) process.exitCode = 1;
