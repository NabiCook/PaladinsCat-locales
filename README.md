# PaladinsCat community translations

This repository contains community-maintained text for PaladinsCat. It contains
translation JSON only; the PaladinsCat application source is kept in a separate
private repository.

## Contribute a translation

1. Copy an English module such as `locales/en/ui/navigation.json` to the same
   path under your locale, for example `locales/de/ui/navigation.json`.
2. Translate values only. Do not rename or add keys.
3. Open a pull request with the JSON file.

The website loads approved locale files directly from this repository and falls
back to English whenever a string is not yet translated. See
[CONTRIBUTING.md](CONTRIBUTING.md) for formatting and review rules. Contributors
who prefer a translation-management interface may use a
[private Tolgee instance](docs/CONTRIBUTING_WITH_TOLGEE.md) on their own
computer.

For the planned format-neutral catalog and submission API, see the
[federated translation platform plan](docs/TRANSLATION_PLATFORM.md).

## Repository layout

- `locales/modules.json` lists every module used by the website.
- `locales/en/<area>.json` files are the English source key lists.
- `locales/<locale>/<area>.json` files are community translations.
- `.github/workflows/validate-locales.yml` validates every pull request.

No private application code, credentials, infrastructure files, or production
configuration belong in this repository.
