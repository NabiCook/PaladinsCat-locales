#!/usr/bin/env node

import crypto from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";

const CONFIG_NAME = ".paladinscat-l10n.json";
const DEFAULT_API_BASE = "https://paladinscat.com/api";
const DEFAULT_TOLGEE_URL = "http://127.0.0.1:8080";
const IMPORT_CHUNK_SIZE = 500;

export function parseArgs(argv) {
  const positional = [];
  const options = {};
  for (let index = 0; index < argv.length; index += 1) {
    const value = argv[index];
    if (!value.startsWith("--")) {
      positional.push(value);
      continue;
    }
    const equals = value.indexOf("=");
    if (equals > 2) {
      options[value.slice(2, equals)] = value.slice(equals + 1);
      continue;
    }
    const name = value.slice(2);
    const next = argv[index + 1];
    if (next !== undefined && !next.startsWith("--")) {
      options[name] = next;
      index += 1;
    } else {
      options[name] = true;
    }
  }
  return { command: positional.shift() ?? "help", positional, options };
}

function required(value, message) {
  if (value === undefined || value === null || String(value).trim() === "") throw new Error(message);
  return String(value).trim();
}

function normalizeUrl(value) {
  return value.replace(/\/+$/, "");
}

function configPath(options = {}) {
  return path.resolve(String(options.config || CONFIG_NAME));
}

async function loadConfig(options = {}) {
  const file = configPath(options);
  try {
    return { file, value: JSON.parse(await fs.readFile(file, "utf8")) };
  } catch (error) {
    if (error?.code === "ENOENT") throw new Error(`No ${CONFIG_NAME} found. Run paladinscat-l10n init first.`);
    throw error;
  }
}

async function saveConfig(file, value) {
  await fs.writeFile(file, `${JSON.stringify(value, null, 2)}\n`, { encoding: "utf8", mode: 0o600 });
}

async function responseBody(response) {
  const text = await response.text();
  if (!text) return null;
  try { return JSON.parse(text); } catch { return text; }
}

async function request(url, init = {}) {
  const response = await fetch(url, init);
  const body = await responseBody(response);
  if (!response.ok) {
    const message = body?.error?.message || body?.message || (typeof body === "string" ? body.slice(0, 500) : response.statusText);
    throw new Error(`${response.status} ${message}`);
  }
  return { response, body };
}

export function checksumUnits(units) {
  const canonical = [...units]
    .sort((left, right) => left.namespace.localeCompare(right.namespace) || left.key.localeCompare(right.key))
    .map((unit) => [unit.namespace, unit.key, unit.source, unit.target, unit.context ?? ""]);
  return `sha256:${crypto.createHash("sha256").update(JSON.stringify(canonical), "utf8").digest("hex")}`;
}

function verifyBundle(bundle, headers) {
  if (bundle?.schemaVersion !== 1 || !Array.isArray(bundle.units)) throw new Error("PaladinsCat returned an unsupported catalog bundle");
  if (bundle.keyCount !== bundle.units.length) throw new Error("Catalog key count does not match its payload");
  const calculated = checksumUnits(bundle.units);
  if (calculated !== bundle.checksum) throw new Error("Catalog checksum validation failed");
  const headerChecksum = headers.get("x-paladinscat-bundle-checksum");
  if (headerChecksum && headerChecksum !== calculated) throw new Error("Catalog checksum header does not match its payload");
}

async function fetchBundle(config) {
  const url = new URL(`${config.apiBase}/localization/v1/catalogs/${encodeURIComponent(config.catalog)}/export`);
  url.searchParams.set("locale", config.locale);
  url.searchParams.set("format", "json");
  const { response, body } = await request(url);
  verifyBundle(body, response.headers);
  return body;
}

function chunks(values, size) {
  const output = [];
  for (let index = 0; index < values.length; index += size) output.push(values.slice(index, index + size));
  return output;
}

export function toTolgeeImportKeys(bundle) {
  return bundle.units.map((unit) => {
    const translations = {
      en: { text: unit.source, resolution: "OVERRIDE" },
    };
    if (unit.target) translations[bundle.targetLanguage] = { text: unit.target, resolution: "EXPECT_NO_CONFLICT" };
    return { name: unit.key, namespace: unit.namespace, translations };
  });
}

async function tolgeeImport(config, bundle, apiKey) {
  const keys = toTolgeeImportKeys(bundle);
  let imported = 0;
  for (const group of chunks(keys, IMPORT_CHUNK_SIZE)) {
    const { body } = await request(
      `${config.tolgeeUrl}/v2/projects/${encodeURIComponent(config.tolgeeProjectId)}/single-step-import-resolvable`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-API-Key": apiKey },
        body: JSON.stringify({ keys: group, overrideMode: "RECOMMENDED", errorOnUnresolvedConflict: false }),
      },
    );
    const unresolved = Array.isArray(body?.unresolvedConflicts) ? body.unresolvedConflicts.length : 0;
    imported += group.length;
    process.stdout.write(`Imported ${imported}/${keys.length} keys${unresolved ? ` (${unresolved} target conflicts kept local)` : ""}\n`);
  }
}

async function tolgeeTranslations(config, apiKey) {
  const rows = [];
  let page = 0;
  while (true) {
    const url = new URL(`${config.tolgeeUrl}/v2/projects/${encodeURIComponent(config.tolgeeProjectId)}/translations`);
    url.searchParams.append("languages", "en");
    url.searchParams.append("languages", config.locale);
    url.searchParams.set("page", String(page));
    url.searchParams.set("size", "1000");
    const { body } = await request(url, { headers: { "X-API-Key": apiKey } });
    const current = body?._embedded?.keys;
    if (!Array.isArray(current)) throw new Error("Tolgee returned an unsupported translations response");
    rows.push(...current);
    const totalPages = Number(body?.page?.totalPages ?? 0);
    if (current.length === 0 || (totalPages > 0 && page + 1 >= totalPages) || (totalPages === 0 && current.length < 1000)) break;
    page += 1;
  }
  return rows;
}

export function toSubmissionUnits(rows, bundle) {
  const source = new Map(bundle.units.map((unit) => [`${unit.namespace}\u0000${unit.key}`, unit.source]));
  const translations = [];
  for (const row of rows) {
    const namespace = row.keyNamespace ?? "";
    const key = row.keyName;
    const id = `${namespace}\u0000${key}`;
    if (!source.has(id)) continue;
    const localSource = row.translations?.en?.text ?? "";
    if (localSource !== source.get(id)) throw new Error(`Tolgee source differs from PaladinsCat for ${namespace}:${key}; run pull again`);
    const target = row.translations?.[bundle.targetLanguage];
    if (!target?.text || !["TRANSLATED", "REVIEWED"].includes(target.state)) continue;
    translations.push({ namespace, key, text: target.text });
  }
  return translations;
}

async function commandInit(options) {
  const catalog = required(options.catalog, "--catalog is required (website or game-client)");
  const locale = required(options.locale, "--locale is required");
  const projectId = Number(required(options["project-id"], "--project-id is required"));
  if (!Number.isInteger(projectId) || projectId <= 0) throw new Error("--project-id must be a positive integer");
  const file = configPath(options);
  const value = {
    schemaVersion: 1,
    apiBase: normalizeUrl(String(options["api-base"] || DEFAULT_API_BASE)),
    catalog,
    locale,
    tolgeeUrl: normalizeUrl(String(options["tolgee-url"] || DEFAULT_TOLGEE_URL)),
    tolgeeProjectId: projectId,
  };
  await saveConfig(file, value);
  process.stdout.write(`Saved ${file}\nSecrets were not stored. Set TOLGEE_API_KEY and PALADINSCAT_CONTRIBUTION_TOKEN in your shell.\n`);
}

async function commandCatalogs(options) {
  const apiBase = normalizeUrl(String(options["api-base"] || DEFAULT_API_BASE));
  const { body } = await request(`${apiBase}/localization/v1/catalogs`);
  for (const catalog of body.catalogs ?? []) {
    process.stdout.write(`${catalog.id}\t${catalog.available ? "available" : "unavailable"}\t${catalog.name}${catalog.unavailableReason ? ` — ${catalog.unavailableReason}` : ""}\n`);
  }
}

async function commandProgress(options) {
  const loaded = await loadConfig(options);
  const { body } = await request(`${loaded.value.apiBase}/localization/v1/progress?catalog=${encodeURIComponent(loaded.value.catalog)}`);
  process.stdout.write(`Catalog: ${body.catalog} (${body.totalKeys} keys, revision ${body.revision})\n`);
  for (const language of body.languages ?? []) {
    process.stdout.write(`${language.locale}\t${language.percent}%\t${language.approvedKeys}/${body.totalKeys}\t${language.pendingSubmissions} pending\t${language.staleSubmissions ?? 0} stale\n`);
  }
}

async function commandPull(options) {
  const loaded = await loadConfig(options);
  const apiKey = required(process.env.TOLGEE_API_KEY, "Set TOLGEE_API_KEY to a Tolgee project API key");
  const bundle = await fetchBundle(loaded.value);
  await tolgeeImport(loaded.value, bundle, apiKey);
  loaded.value.baseRevision = bundle.revision;
  loaded.value.bundleChecksum = bundle.checksum;
  loaded.value.lastPulledAt = new Date().toISOString();
  await saveConfig(loaded.file, loaded.value);
  process.stdout.write(`Pull complete: ${bundle.keyCount} keys at ${bundle.revision}\n`);
}

async function commandSubmit(options) {
  const loaded = await loadConfig(options);
  const apiKey = required(process.env.TOLGEE_API_KEY, "Set TOLGEE_API_KEY to a Tolgee project API key");
  const contributionToken = required(process.env.PALADINSCAT_CONTRIBUTION_TOKEN, "Set PALADINSCAT_CONTRIBUTION_TOKEN to a scoped PaladinsCat localization token");
  const baseRevision = required(loaded.value.baseRevision, "Run pull before submitting");
  const bundle = await fetchBundle(loaded.value);
  if (bundle.revision !== baseRevision) throw new Error(`Catalog changed from ${baseRevision} to ${bundle.revision}; run pull and review the changes before submitting`);
  const rows = await tolgeeTranslations(loaded.value, apiKey);
  const translations = toSubmissionUnits(rows, bundle);
  if (translations.length === 0) throw new Error("Tolgee has no TRANSLATED or REVIEWED target strings to submit");
  const { body } = await request(`${loaded.value.apiBase}/localization/v1/submissions`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${contributionToken}` },
    body: JSON.stringify({
      catalog: loaded.value.catalog,
      locale: loaded.value.locale,
      baseRevision,
      translations,
    }),
  });
  loaded.value.lastSubmissionId = body.id;
  loaded.value.lastSubmittedAt = new Date().toISOString();
  await saveConfig(loaded.file, loaded.value);
  process.stdout.write(`Submitted ${body.keyCount} keys as ${body.id}; status: ${body.status}\n`);
}

async function commandStatus(options, positional) {
  const loaded = await loadConfig(options);
  const contributionToken = required(process.env.PALADINSCAT_CONTRIBUTION_TOKEN, "Set PALADINSCAT_CONTRIBUTION_TOKEN to a scoped PaladinsCat localization token");
  const submissionId = positional[0] || loaded.value.lastSubmissionId;
  required(submissionId, "Provide a submission id or submit once first");
  const { body } = await request(`${loaded.value.apiBase}/localization/v1/submissions/${encodeURIComponent(submissionId)}`, {
    headers: { Authorization: `Bearer ${contributionToken}` },
  });
  process.stdout.write(`${JSON.stringify(body, null, 2)}\n`);
}

function help() {
  process.stdout.write(`PaladinsCat localization sync\n\nCommands:\n  catalogs [--api-base URL]\n  init --catalog website --locale de --project-id 1 [--tolgee-url URL] [--api-base URL]\n  pull\n  progress\n  submit\n  status [submission-id]\n\nEnvironment variables:\n  TOLGEE_API_KEY                    Local Tolgee project API key\n  PALADINSCAT_CONTRIBUTION_TOKEN    Scoped token created on PaladinsCat\n\nThe config file stores project coordinates and source revisions only. It never stores secrets.\n`);
}

export async function main(argv = process.argv.slice(2)) {
  const { command, positional, options } = parseArgs(argv);
  if (command === "init") return commandInit(options);
  if (command === "catalogs") return commandCatalogs(options);
  if (command === "pull") return commandPull(options);
  if (command === "progress") return commandProgress(options);
  if (command === "submit") return commandSubmit(options);
  if (command === "status") return commandStatus(options, positional);
  if (command === "help" || command === "--help" || command === "-h") return help();
  throw new Error(`Unknown command ${command}`);
}

if (process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href) {
  main().catch((error) => {
    process.stderr.write(`Error: ${error instanceof Error ? error.message : String(error)}\n`);
    process.exitCode = 1;
  });
}
