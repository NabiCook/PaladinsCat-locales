# Contributing translations

Thank you for helping make PaladinsCat accessible in more languages.

## Rules

- Start from an English module in `locales/en/` and edit values only.
- Keep JSON valid and use UTF-8 characters directly.
- Preserve placeholders such as `{name}` exactly when they appear.
- Submit one locale/module per pull request, using a BCP 47 directory such as
  `fr`, `pt-BR`, or `zh-CN`.
- You may submit a partial translation. Untranslated keys safely fall back to
  English in the website.
- Do not include scripts, application code, credentials, or unrelated files.

The automated check rejects unknown keys, empty strings, invalid locale
filenames, and non-string values. Maintainers review wording and terminology
before merging.

## Recommended Tolgee workflow

You may run Tolgee privately on your own computer. PaladinsCat does not need
network access to your instance. The companion CLI verifies source checksums,
imports the selected catalog, and submits completed strings to an administrator
queue without giving contributors direct write access to GitHub.

See:

- [Complete Tolgee setup and contributor guide](docs/CONTRIBUTING_WITH_TOLGEE.md)
- [Local Tolgee Docker setup](docs/SELF_HOSTED_TOLGEE.md)
