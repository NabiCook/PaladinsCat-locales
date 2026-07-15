const path = require("node:path");
const localeModules = require("./locales/modules.json");

const projectId = Number(process.env.TOLGEE_PROJECT_ID);
const targetLocales = (
  process.env.TOLGEE_TARGET_LOCALES || process.env.TOLGEE_TARGET_LOCALE || ""
)
  .split(/[\s,]+/)
  .map((locale) => locale.trim())
  .filter(Boolean);

if (!Number.isInteger(projectId) || projectId <= 0) {
  throw new Error("Set TOLGEE_PROJECT_ID to the numeric project id shown in the Tolgee URL.");
}
if (process.argv.includes("pull") && targetLocales.length === 0) {
  throw new Error(
    "Set TOLGEE_TARGET_LOCALES (or TOLGEE_TARGET_LOCALE) before exporting translations into the repository."
  );
}

module.exports = {
  $schema: "https://docs.tolgee.io/cli-schema.json",
  projectId,
  apiUrl: process.env.TOLGEE_API_URL?.trim() || "http://127.0.0.1:8080",
  format: "JSON_ICU",
  strictNamespace: false,
  push: {
    files: localeModules.map((namespace) => ({
      path: path.resolve(__dirname, "locales", "en", `${namespace}.json`),
      language: "en",
      namespace,
    })),
    forceMode: "OVERRIDE",
    convertPlaceholdersToIcu: false
  },
  pull: {
    path: "./locales",
    fileStructureTemplate: "{languageTag}/{namespace}.{extension}",
    delimiter: "",
    languages: targetLocales,
    namespaces: localeModules,
    states: ["TRANSLATED", "REVIEWED"],
    emptyDir: false
  }
};
