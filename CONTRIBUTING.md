# Contributing translations

## Rules

- Create a branch from the current `main` branch.
- Edit target-language values only. Do not rename or add application keys.
- Keep JSON valid and use UTF-8 characters directly.
- Preserve placeholders such as `{name}`, `@@TOKEN@@`, `%s`, and `%1$s`.
- Use BCP 47 locale directories such as `fr`, `pt-BR`, or `zh-CN`.
- Partial modules are allowed; missing strings fall back to English.
- Do not include credentials, Tolgee data volumes, application code, or
  unrelated files.

Before committing, run:

```powershell
npm install
npm run validate
```

GitHub Actions repeats these checks for every pull request. It rejects invalid
module paths, unknown keys, empty or oversized strings, malformed Unicode,
changed placeholders, invalid CSV rows, and duplicate game message IDs.

## Tolgee workflow

Tolgee stores its working copy in its own database, so it does not edit Git
files continuously. For the shared project, a scheduled GitHub workflow uses
the checked-in Tolgee CLI configuration to bridge the two:

1. translate in the Tolgee web interface;
2. wait for the automation run, or start it from GitHub Actions;
3. review the generated `automation/tolgee-export` pull request;
4. merge it after validation passes.

The shared Tolgee endpoint must be reachable by GitHub-hosted runners. A
local-only Tolgee instance uses the GitHub Desktop fallback in
[the complete guide](docs/CONTRIBUTING_WITH_TOLGEE.md). Repository owners can
configure the web workflow with
[the automation guide](docs/TOLGEE_GITHUB_AUTOMATION.md).
