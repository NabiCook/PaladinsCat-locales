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

## Optional Tolgee workflow

You may run Tolgee privately on your own computer, import the English modules,
and export your target-language JSON before opening the pull request. PaladinsCat
does not need network access to your Tolgee instance.

See:

- [Contributing with Tolgee](docs/CONTRIBUTING_WITH_TOLGEE.md)
- [Local Tolgee Docker setup](docs/SELF_HOSTED_TOLGEE.md)
