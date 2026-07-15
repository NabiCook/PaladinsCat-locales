import { readFile, rm, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

const localesRoot = fileURLToPath(new URL("../locales/", import.meta.url));
const modules = JSON.parse(await readFile(join(localesRoot, "modules.json"), "utf8"));
const targetLocales = (
  process.env.TOLGEE_TARGET_LOCALES || process.env.TOLGEE_TARGET_LOCALE || ""
)
  .split(/[\s,]+/)
  .map((locale) => locale.trim())
  .filter(Boolean);

if (targetLocales.length === 0) {
  throw new Error("Set TOLGEE_TARGET_LOCALES before sanitizing a Tolgee export.");
}

for (const locale of targetLocales) {
  if (locale === "en") continue;

  for (const module of modules) {
    const sourceFile = join(localesRoot, "en", `${module}.json`);
    const targetFile = join(localesRoot, locale, `${module}.json`);
    const source = JSON.parse(await readFile(sourceFile, "utf8"));

    let translated;
    try {
      translated = JSON.parse(await readFile(targetFile, "utf8"));
    } catch (error) {
      if (error?.code === "ENOENT") continue;
      throw error;
    }

    const sanitized = Object.fromEntries(
      Object.entries(translated)
        .filter(([key, value]) => Object.hasOwn(source, key) && typeof value === "string" && value.trim())
        .sort(([left], [right]) => left.localeCompare(right)),
    );

    if (Object.keys(sanitized).length === 0) {
      await rm(targetFile);
    } else {
      await writeFile(targetFile, `${JSON.stringify(sanitized, null, 2)}\n`, "utf8");
    }
  }
}
