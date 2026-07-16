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
files continuously. The current project is local-only, so a guarded local
agent uses the checked-in Tolgee CLI configuration to bridge the two:

1. translate in the Tolgee web interface;
2. export from a clean translation branch with `npm run tolgee:local -- export`;
3. publish the branch and create a GitHub pull request;
4. merge it after validation passes.

See the [local-agent guide](docs/LOCAL_AGENT_TOLGEE.md). If Tolgee is later
hosted at a URL reachable by GitHub runners, repository owners can opt into the
scheduled workflow with the
[hosted automation guide](docs/TOLGEE_GITHUB_AUTOMATION.md).
