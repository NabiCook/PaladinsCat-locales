# Contributing translations

Thank you for helping make PaladinsCat accessible in more languages.

## Rules

- Start from `locales/en.json` and edit values only.
- Keep JSON valid and use UTF-8 characters directly.
- Preserve placeholders such as `{name}` exactly when they appear.
- Submit one locale per pull request, using a BCP 47 filename such as `fr.json`,
  `pt-BR.json`, or `zh-CN.json`.
- You may submit a partial translation. Untranslated keys safely fall back to
  English in the website.
- Do not include scripts, application code, credentials, or unrelated files.

The automated check rejects unknown keys, empty strings, invalid locale
filenames, and non-string values. Maintainers review wording and terminology
before merging.
