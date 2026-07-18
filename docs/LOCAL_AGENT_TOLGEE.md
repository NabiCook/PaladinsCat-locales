# Local-agent connection to Tolgee

Local agents use the official Tolgee CLI through this repository's checked-in
configuration. They do not call the retired PaladinsCat localization API and
they do not receive GitHub App credentials.

GitHub-hosted runners cannot connect to this machine's `127.0.0.1:8080`.
Therefore the repository's scheduled hosted-export job remains disabled and
local agents perform the export before publishing a Git branch.

The current local project defaults are:

- Tolgee API: `http://127.0.0.1:8080`
- project ID: `6`
- normal target locale: `ko`
- canonical source language: `en`

## 1. Start and verify Tolgee

Start the local Tolgee Docker service described in
[SELF_HOSTED_TOLGEE.md](SELF_HOSTED_TOLGEE.md), then open
`http://127.0.0.1:8080` in a browser. Project `6` must exist and contain Korean
as a target language.

## 2. Create a project API key

In Tolgee, open the user menu in the upper-right corner, choose **Project API
keys**, and create a key restricted to project `6`.

For an agent that only exports translations, grant the minimum scopes needed
to view project keys and translations. A maintainer that pushes canonical
English sources needs key/translation editing permission; use a separate key
where practical and give it an expiration date.

Prefer a project API key (`tgpak_…`) over a personal access token because the
project key is restricted to one project and supports scoped permissions.

## 3. Store local credentials

From the repository root:

```powershell
Copy-Item .env.tolgee.example .env.tolgee.local
notepad .env.tolgee.local
```

Replace `replace-with-a-project-api-key` with the generated key. The resulting
file should contain:

```dotenv
TOLGEE_API_URL=http://127.0.0.1:8080
TOLGEE_PROJECT_ID=6
TOLGEE_TARGET_LOCALES=ko
TOLGEE_API_KEY=tgpak_replace_me
```

On a shared Windows machine, optionally restrict the file to the current user:

```powershell
icacls .env.tolgee.local /inheritance:r /grant:r "$($env:USERNAME):(R,W)"
```

`.env.tolgee.local`, `.tolgeerc*`, and the legacy `tolgeerc.json` are ignored
by Git. Never paste their values into an agent prompt, commit, terminal log, or
pull request. Environment variables supplied by a secure agent runner override
values from the file. A runner may select a different file by setting
`TOLGEE_CREDENTIAL_FILE`.

The existing legacy `tolgeerc.json` has an `apiKey` field and uses nonstandard
field names. Keep it uncommitted. If that field is populated, migrate to
`.env.tolgee.local`, rotate the old key, and remove the legacy file when its
helper scripts are retired.

## 4. Install and check the connection

```powershell
npm ci
npm run tolgee:local -- check
```

The check calls Tolgee's project statistics endpoint, reports only the API URL,
project ID, and locale tags, and never prints the API key.

## 5. Agent-safe commands

Validate without connecting to Tolgee:

```powershell
npm run tolgee:local -- validate
```

Export `TRANSLATED` and `REVIEWED` Korean values into the repository:

```powershell
npm run tolgee:local -- export
```

The export refuses to run if `locales/ko` already contains uncommitted work.
This protects another agent's or translator's preview. Preserve or commit that
work first. Only after inspecting the existing diff may an operator override
the guard:

```powershell
npm run tolgee:local -- export --allow-dirty
```

Override the configured locale for one run:

```powershell
npm run tolgee:local -- export --locales fr
```

Pushing English source strings changes Tolgee and is maintainer-only. The
wrapper requires a second explicit flag:

```powershell
npm run tolgee:local -- push-source --allow-source-push
```

To validate that the checked-out repository matches its upstream, validate the
English catalog, push it, and verify every canonical key in one command, use:

```powershell
npm run tolgee:sync-source -- --apply
```

On Windows, the same guarded sync is available as
`Sync-TolgeeSource.ps1` in the repository root. Right-click it and choose
**Run with PowerShell**, or run it from a terminal. It does not commit or push
to GitHub. It works from any clone: by default it syncs the canonical English
files already in that clone to the configured Tolgee project.

```powershell
.\Sync-TolgeeSource.ps1
```

To also copy a nearby PaladinsCat frontend catalog first, keep repositories as
sibling directories named `PaladinsCat` and `PaladinsCat-locales`. On another
layout, supply the frontend path once per run or set it in your user
environment:

```powershell
.\Sync-TolgeeSource.ps1 -FrontendDir 'D:\work\PaladinsCat\src\frontend'
$env:PALADINSCAT_FRONTEND_DIR = 'D:\work\PaladinsCat\src\frontend'
```

Use `-CheckOnly` for the read-only report. The launcher pauses at completion so
Explorer's **Run with PowerShell** window stays visible; use `-NoPause` for
terminal or automation use.

Omit `--apply` for a read-only parity report. The command refuses dirty
canonical locale files or an out-of-date checkout and reports stale Tolgee-only
keys without deleting them.

## 6. Git rules for agents

1. Run `git status --short` before connecting or exporting.
2. Create a branch from current `main`; never export directly on `main`.
3. Touch only the requested locale paths.
4. Run `npm run validate` and inspect `git diff` after export.
5. Never stage `.env*`, `.tolgeerc*`, `tolgeerc.json`, generated diagnostics,
   or another agent's work.
6. Commit the intended locale files, push the branch, and create one GitHub
   pull request. GitHub is the only approval gate.

## Credential rotation

Regenerate or revoke a local-agent key when it is exposed, when an agent no
longer needs access, or at its planned expiration. Update only
`.env.tolgee.local` or the secure runner environment. No PaladinsCat VPS change
is required.
