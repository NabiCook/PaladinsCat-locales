import { access, readdir, readFile } from "node:fs/promises";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

const localesDirectory = fileURLToPath(new URL("../locales/", import.meta.url));
const localeName = /^(?:[a-z]{2,3})(?:-[A-Z]{2})?$/;
const modules = JSON.parse(await readFile(join(localesDirectory, "modules.json"), "utf8"));
let hasErrors = false;

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

if (hasErrors) process.exitCode = 1;
