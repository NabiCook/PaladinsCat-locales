#!/usr/bin/env node

import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
import { spawnSync } from "node:child_process";

const ACTIONS = new Set(["check", "export", "push-source", "validate"]);
const CREDENTIAL_KEYS = new Set([
  "TOLGEE_API_URL",
  "TOLGEE_PROJECT_ID",
  "TOLGEE_TARGET_LOCALE",
  "TOLGEE_TARGET_LOCALES",
  "TOLGEE_API_KEY",
]);

function fail(message) {
  console.error(`[tolgee-local] ${message}`);
  process.exit(1);
}

function parseArguments(argv) {
  const action = argv[0] || "check";
  if (!ACTIONS.has(action)) {
    fail(`Unknown action '${action}'. Use check, export, push-source, or validate.`);
  }

  let locales;
  for (let index = 1; index < argv.length; index += 1) {
    const argument = argv[index];
    if (argument === "--locales") {
      locales = argv[index + 1];
      if (!locales) fail("--locales requires a comma- or space-separated value.");
      index += 1;
      continue;
    }
    if (!["--allow-dirty", "--allow-source-push"].includes(argument)) {
      fail(`Unknown option '${argument}'.`);
    }
  }

  return {
    action,
    locales,
    allowDirty: argv.includes("--allow-dirty"),
    allowSourcePush: argv.includes("--allow-source-push"),
  };
}

function unquote(value) {
  if (value.length >= 2) {
    const first = value[0];
    const last = value[value.length - 1];
    if ((first === '"' && last === '"') || (first === "'" && last === "'")) {
      return value.slice(1, -1);
    }
  }
  return value;
}

function loadCredentials(filePath) {
  if (!existsSync(filePath)) return false;

  const lines = readFileSync(filePath, "utf8").split(/\r?\n/);
  for (const [lineIndex, rawLine] of lines.entries()) {
    const line = rawLine.trim();
    if (!line || line.startsWith("#")) continue;

    const separator = line.indexOf("=");
    if (separator <= 0) {
      fail(`Invalid credentials line ${lineIndex + 1} in ${filePath}.`);
    }
    const key = line.slice(0, separator).trim();
    if (!CREDENTIAL_KEYS.has(key)) {
      fail(`Unsupported credential '${key}' in ${filePath}.`);
    }
    const value = unquote(line.slice(separator + 1).trim());
    if (process.env[key] === undefined) process.env[key] = value;
  }
  return true;
}

function targetLocales() {
  const locales = (process.env.TOLGEE_TARGET_LOCALES || process.env.TOLGEE_TARGET_LOCALE || "")
    .split(/[\s,]+/)
    .map((locale) => locale.trim())
    .filter(Boolean);
  const invalid = locales.filter(
    (locale) => !/^[A-Za-z]{2,3}(?:-[A-Za-z0-9]{2,8})*$/.test(locale)
  );
  if (invalid.length > 0) fail(`Invalid locale tag(s): ${invalid.join(", ")}.`);
  return locales;
}

function run(command, args, options = {}) {
  const useWindowsNpmShell = process.platform === "win32" && command === "npm";
  const result = spawnSync(command, args, {
    cwd: resolve(import.meta.dirname, ".."),
    env: process.env,
    encoding: "utf8",
    // npm is a .cmd shim on Windows and requires cmd.exe. Git remains a direct
    // process so locale-derived path arguments are never interpreted by a shell.
    shell: useWindowsNpmShell,
    stdio: options.capture ? "pipe" : "inherit",
  });
  if (result.error) fail(result.error.message);
  if (result.status !== 0) process.exit(result.status ?? 1);
  return result.stdout || "";
}

function requireCredentials({ requireTargets = false } = {}) {
  const missing = ["TOLGEE_API_URL", "TOLGEE_PROJECT_ID", "TOLGEE_API_KEY"]
    .filter((key) => !process.env[key]?.trim());
  if (requireTargets && targetLocales().length === 0) missing.push("TOLGEE_TARGET_LOCALES");
  if (missing.length > 0) {
    fail(`Missing ${missing.join(", ")}. Copy .env.tolgee.example to .env.tolgee.local.`);
  }

  const projectId = Number(process.env.TOLGEE_PROJECT_ID);
  if (!Number.isInteger(projectId) || projectId <= 0) fail("TOLGEE_PROJECT_ID must be a positive integer.");
}

function assertTargetsClean(locales, allowDirty) {
  if (allowDirty) return;
  const paths = locales.map((locale) => `locales/${locale}`);
  const output = run("git", ["status", "--porcelain", "--", ...paths], { capture: true }).trim();
  if (output) {
    fail(
      `Target locale work is already dirty (${paths.join(", ")}). Preserve it first, or rerun with --allow-dirty after reviewing the risk.`
    );
  }
}

async function checkConnection() {
  requireCredentials({ requireTargets: true });
  const baseUrl = process.env.TOLGEE_API_URL.replace(/\/+$/, "");
  const projectId = Number(process.env.TOLGEE_PROJECT_ID);
  let response;
  try {
    response = await fetch(`${baseUrl}/v2/projects/${projectId}/stats`, {
      headers: { "X-API-Key": process.env.TOLGEE_API_KEY },
      signal: AbortSignal.timeout(15_000),
    });
  } catch (error) {
    fail(`Unable to reach ${baseUrl}: ${error.message}`);
  }
  if (!response.ok) fail(`Tolgee rejected the connection (HTTP ${response.status}).`);

  console.log(`[tolgee-local] Connected to ${baseUrl}, project ${projectId}.`);
  console.log(`[tolgee-local] Target locales: ${targetLocales().join(", ")}. API key loaded (value hidden).`);
}

const options = parseArguments(process.argv.slice(2));
const repoRoot = resolve(import.meta.dirname, "..");
const credentialFile = resolve(
  repoRoot,
  process.env.TOLGEE_CREDENTIAL_FILE || ".env.tolgee.local"
);
const loadedFile = loadCredentials(credentialFile);
if (options.locales) process.env.TOLGEE_TARGET_LOCALES = options.locales;

if (options.action !== "validate" && !loadedFile && !process.env.TOLGEE_API_KEY) {
  fail(`Credentials file not found: ${credentialFile}`);
}

switch (options.action) {
  case "check":
    await checkConnection();
    break;
  case "validate":
    run("npm", ["run", "validate"]);
    break;
  case "export": {
    requireCredentials({ requireTargets: true });
    assertTargetsClean(targetLocales(), options.allowDirty);
    run("npm", ["run", "tolgee:export"]);
    break;
  }
  case "push-source":
    requireCredentials();
    if (!options.allowSourcePush) {
      fail("Source push changes the shared Tolgee project. Rerun with --allow-source-push after reviewing the English diff.");
    }
    run("npm", ["run", "tolgee:push"]);
    break;
}
