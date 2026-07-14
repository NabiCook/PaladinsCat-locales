import assert from "node:assert/strict";
import test from "node:test";
import { checksumUnits, parseArgs, toSubmissionUnits, toTolgeeImportKeys } from "./paladinscat-l10n.mjs";

const bundle = {
  schemaVersion: 1,
  catalog: "website",
  sourceLanguage: "en",
  targetLanguage: "de",
  revision: "abc",
  keyCount: 1,
  checksum: "",
  units: [{ namespace: "ui/navigation", key: "nav.home", source: "Home", target: "Startseite" }],
};

test("parseArgs accepts values and equals syntax", () => {
  assert.deepEqual(parseArgs(["init", "--catalog", "website", "--locale=de"]), {
    command: "init",
    positional: [],
    options: { catalog: "website", locale: "de" },
  });
});

test("Tolgee import preserves namespace and both languages", () => {
  assert.deepEqual(toTolgeeImportKeys(bundle), [{
    name: "nav.home",
    namespace: "ui/navigation",
    translations: {
      en: { text: "Home", resolution: "OVERRIDE" },
      de: { text: "Startseite", resolution: "EXPECT_NO_CONFLICT" },
    },
  }]);
});

test("submission includes only translated or reviewed values with matching source", () => {
  const rows = [{
    keyName: "nav.home",
    keyNamespace: "ui/navigation",
    translations: {
      en: { text: "Home", state: "REVIEWED" },
      de: { text: "Start", state: "TRANSLATED" },
    },
  }];
  assert.deepEqual(toSubmissionUnits(rows, bundle), [{ namespace: "ui/navigation", key: "nav.home", text: "Start" }]);
});

test("checksum is deterministic regardless of input order", () => {
  const units = [
    { namespace: "b", key: "2", source: "B", target: "", context: "" },
    { namespace: "a", key: "1", source: "A", target: "", context: "" },
  ];
  assert.equal(checksumUnits(units), checksumUnits([...units].reverse()));
});
