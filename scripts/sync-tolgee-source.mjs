#!/usr/bin/env node

import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
import { spawnSync } from "node:child_process";

const repoRoot = resolve(import.meta.dirname, "..");
const credentialFile = resolve(
  repoRoot,
  process.env.TOLGEE_CREDENTIAL_FILE || ".env.tolgee.local",
);
const apply = process.argv.slice(2).includes("--apply");
const allowLocalChanges = process.argv.slice(2).includes("--allow-local-changes");
const unknownArguments = process.argv.slice(2)
  .filter((argument) => !["--apply", "--allow-local-changes"].includes(argument));
const credentialKeys = new Set([
  "TOLGEE_API_URL",
  "TOLGEE_PROJECT_ID",
  "TOLGEE_TARGET_LOCALE",
  "TOLGEE_TARGET_LOCALES",
  "TOLGEE_API_KEY",
]);

function fail(message) {
  console.error(`[tolgee-sync] ${message}`);
  process.exit(1);
}

function run(command, args, { capture = false } = {}) {
  const result = spawnSync(command, args, {
    cwd: repoRoot,
    env: process.env,
    encoding: "utf8",
    shell: process.platform === "win32" && command === "npm",
    stdio: capture ? "pipe" : "inherit",
  });
  if (result.error) fail(result.error.message);
  if (result.status !== 0) process.exit(result.status ?? 1);
  return result.stdout?.trim() || "";
}

function loadCredentials() {
  if (!existsSync(credentialFile)) {
    fail(`Credentials file not found: ${credentialFile}`);
  }

  for (const rawLine of readFileSync(credentialFile, "utf8").split(/\r?\n/)) {
    const line = rawLine.trim();
    if (!line || line.startsWith("#")) continue;
    const separator = line.indexOf("=");
    const key = line.slice(0, separator).trim();
    const rawValue = line.slice(separator + 1).trim();
    const value = rawValue.replace(/^(?:"|')|(?:"|')$/g, "");
    if (separator <= 0 || !credentialKeys.has(key)) {
      fail(`Invalid credentials entry in ${credentialFile}.`);
    }
    if (process.env[key] === undefined) process.env[key] = value;
  }

  const missing = ["TOLGEE_API_URL", "TOLGEE_PROJECT_ID", "TOLGEE_API_KEY"]
    .filter((key) => !process.env[key]?.trim());
  if (missing.length > 0) fail(`Missing ${missing.join(", ")}.`);
}

function flattenMessages(value, prefix = "") {
  return Object.entries(value).flatMap(([key, child]) => {
    const name = prefix ? `${prefix}.${key}` : key;
    return child && typeof child === "object" && !Array.isArray(child)
      ? flattenMessages(child, name)
      : [name];
  });
}

function assertCleanCurrentCheckout() {
  run("git", ["fetch", "--prune"]);
  const dirty = run("git", ["status", "--porcelain", "--", "locales"], { capture: true });
  if (dirty && !allowLocalChanges) {
    fail("Canonical locale files have uncommitted changes; commit or stash them before syncing Tolgee.");
  }
  if (dirty && allowLocalChanges) {
    console.log("[tolgee-sync] Using validated local canonical locale changes.");
    return;
  }

  const head = run("git", ["rev-parse", "HEAD"], { capture: true });
  const upstream = run("git", ["rev-parse", "@{upstream}"], { capture: true });
  if (head !== upstream) {
    fail("Current checkout does not match its upstream; pull or push the canonical locale commit first.");
  }
}

function canonicalKeys() {
  const modules = JSON.parse(readFileSync(resolve(repoRoot, "locales", "modules.json"), "utf8"));
  return new Set(modules.flatMap((namespace) => {
    const source = JSON.parse(readFileSync(resolve(repoRoot, "locales", "en", `${namespace}.json`), "utf8"));
    return flattenMessages(source).map((name) => `${namespace}\u0000${name}`);
  }));
}

async function fetchTolgeeKeys() {
  const apiUrl = process.env.TOLGEE_API_URL.replace(/\/+$/, "");
  const projectId = Number(process.env.TOLGEE_PROJECT_ID);
  const headers = { "X-API-Key": process.env.TOLGEE_API_KEY };
  const keys = [];

  for (let page = 0; ; page += 1) {
    const response = await fetch(
      `${apiUrl}/v2/projects/${projectId}/keys?size=500&sort=id,asc&page=${page}`,
      { headers, signal: AbortSignal.timeout(15_000) },
    );
    if (!response.ok) fail(`Tolgee rejected the key check (HTTP ${response.status}).`);
    const payload = await response.json();
    keys.push(...payload._embedded.keys);
    if (page >= payload.page.totalPages - 1) break;
  }

  return keys;
}

async function reportParity() {
  const expected = canonicalKeys();
  const actualKeys = await fetchTolgeeKeys();
  const actual = new Set(actualKeys.map((key) => `${key.namespace || ""}\u0000${key.name}`));
  const missing = [...expected].filter((key) => !actual.has(key));
  const stale = [...actual].filter((key) => !expected.has(key));

  console.log(`[tolgee-sync] Canonical English keys: ${expected.size}. Tolgee keys: ${actual.size}.`);
  console.log(`[tolgee-sync] Missing from Tolgee: ${missing.length}. Stale in Tolgee: ${stale.length}.`);
  if (missing.length > 0) {
    console.log(`[tolgee-sync] Missing samples: ${missing.slice(0, 5).map((key) => key.replace("\u0000", "::")).join(", ")}`);
  }
  return { missing, stale };
}

if (unknownArguments.length > 0) {
  fail("Usage: npm run tolgee:sync-source -- [--apply] [--allow-local-changes]");
}

loadCredentials();
assertCleanCurrentCheckout();
run("npm", ["run", "validate"]);

if (!apply) {
  await reportParity();
  console.log("[tolgee-sync] Dry run only. Rerun with --apply to push canonical English source strings.");
  process.exit(0);
}

run("npm", ["run", "tolgee:local", "--", "push-source", "--allow-source-push"]);
const { missing } = await reportParity();
if (missing.length > 0) fail("Tolgee source push completed but canonical keys are still missing.");
console.log("[tolgee-sync] Tolgee now contains every canonical English key.");
