# PaladinsCat community translations

This repository contains community-maintained text for PaladinsCat. It contains
translation JSON only; the PaladinsCat application source is kept in a separate
private repository.

## Contribute a translation

The recommended workflow uses a private Tolgee instance on your own computer.
It provides progress tracking, search, translation memory, batch operations,
untranslated filters, and an approval-gated PaladinsCat submission helper:

- **[Complete Tolgee setup and contributor guide](docs/CONTRIBUTING_WITH_TOLGEE.md)**
- [Docker-only Tolgee reference](docs/SELF_HOSTED_TOLGEE.md)

For a small direct GitHub contribution:

1. Copy an English module such as `locales/en/ui/navigation.json` to the same
   path under your locale, for example `locales/de/ui/navigation.json`.
2. Translate values only. Do not rename or add keys.
3. Open a pull request with the JSON file.

The website loads approved locale files directly from this repository and falls
back to English whenever a string is not yet translated. See
[CONTRIBUTING.md](CONTRIBUTING.md) for formatting and review rules. The detailed
guide also covers the Paladins game-client catalog, placeholder safety,
repeated-phrase batch processing, and the administrator approval flow.

For the format-neutral catalog, approval, and submission architecture, see the
[federated translation platform design](docs/TRANSLATION_PLATFORM.md).

## Repository layout

- `locales/modules.json` lists every module used by the website.
- `locales/en/<area>.json` files are the English source key lists.
- `locales/<locale>/<area>.json` files are community translations.
- `.github/workflows/validate-locales.yml` validates every pull request.

No private application code, credentials, infrastructure files, or production
configuration belong in this repository.
