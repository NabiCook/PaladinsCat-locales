# Contributing translations

## Rules

- Create a branch from the current `main` branch.
- Edit target-language values only. Do not rename or add application keys.
- Keep JSON valid and use UTF-8 characters directly.
- Preserve placeholders such as `{name}`, `@@TOKEN@@`, `%s`, and `%1$s`.
- Use BCP 47 locale directories such as `fr`, `pt-BR`, or `zh-CN`.
- Partial modules are allowed; missing strings fall back to English.
- Do not include Weblate credentials, exports, application code, or unrelated
  files.

Before committing, run:

```powershell
npm install
npm run validate
```

GitHub Actions repeats these checks for every pull request. It rejects invalid
module paths, unknown keys, empty or oversized strings, malformed Unicode,
changed placeholders, invalid CSV rows, and duplicate game message IDs.

## Weblate workflow

Weblate is the normal translation workspace at
[translate.paladinscat.com](https://translate.paladinscat.com). It synchronizes with this
repository and opens a GitHub pull request for reviewed translation changes.

1. sign in at [translate.paladinscat.com](https://translate.paladinscat.com)
   and choose your language;
2. submit translations; language reviewers approve wording in Weblate;
3. Weblate opens or updates its GitHub pull request;
4. review the diff and merge only after the validation check passes.

GitHub `main` remains the source of truth and release approval boundary.
Weblate must not push directly to `main`.

## Local Git fallback

When Weblate is unavailable, clone the repository, create a branch, edit only
target-language values, run `npm run validate`, and open a normal pull request.
This route has the same validation and review requirements.
