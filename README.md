# PaladinsCat community translations

This repository contains community-maintained text for PaladinsCat. It contains
translation JSON only; the PaladinsCat application source is kept in a separate
private repository.

## Contribute a translation

1. Copy `locales/en.json` to a locale filename such as `de.json` or `pt-BR.json`.
2. Translate values only. Do not rename, remove, or add keys.
3. Open a pull request with the JSON file.

The website loads approved locale files directly from this repository and falls
back to English whenever a string is not yet translated. See
[CONTRIBUTING.md](CONTRIBUTING.md) for formatting and review rules.

## Repository layout

- `locales/en.json` is the source key list.
- `locales/<locale>.json` files are community translations.
- `.github/workflows/validate-locales.yml` validates every pull request.

No private application code, credentials, infrastructure files, or production
configuration belong in this repository.
