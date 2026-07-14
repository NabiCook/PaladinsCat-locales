# Contributing to PaladinsCat with Tolgee

This guide explains how to run a private Tolgee instance, load a PaladinsCat
catalog, translate efficiently, and send the result to the PaladinsCat review
queue. Your Tolgee server remains on your computer. PaladinsCat never connects
to it and never receives its administrator credentials or database.

The automated workflow is approval-gated:

```text
PaladinsCat-locales on GitHub
            |
            | signed catalog + source revision
            v
     PaladinsCat catalog API
            |
            | pull (outbound from the contributor's computer)
            v
       paladinscat-l10n CLI <----> contributor-owned Tolgee
            |
            | translated strings + source revision
            v
      pending admin review
            |
            | administrator approval only
            v
        GitHub pull request
```

Submitting never edits GitHub directly. A contribution remains `pending` until
a PaladinsCat administrator approves it. Approval creates a normal pull request
that still has to pass repository validation and maintainer review.

## Supported catalogs and languages

Use a separate Tolgee project for each catalog:

| Catalog | Suggested project name | Key strategy | Placeholder mode |
|---|---|---|---|
| `website` | `PaladinsCat Website` | Existing application key inside a module namespace | Tolgee ICU enabled |
| `game-client` | `Paladins Game Client` | `msg.<message_id>` inside `game-client` | Tolgee ICU disabled |

The current automated API accepts `de`, `es`, `fr`, `pl`, `pt-BR`, `ru`, `tr`,
and `zh-CN`. Tolgee can contain other languages, but the PaladinsCat submission
API will reject them until the backend allowlist and repository layout support
them.

## Requirements

- Docker Desktop or Docker Engine with Compose v2
- Git
- Node.js 20 or newer
- A clone of this repository
- About 4 GB of memory available to Docker; the game-client catalog is large
- A PaladinsCat account when using the automated submission queue

Clone the repository:

```powershell
git clone https://github.com/NabiCook/PaladinsCat-locales.git
cd PaladinsCat-locales
node --version
```

There are currently no npm dependencies to install. The repository scripts use
Node.js directly.

## 1. Run a private Tolgee instance

Create a directory outside the Git repository, such as
`C:\tolgee-paladinscat`, and place these two files in it.

`docker-compose.yml`:

```yaml
services:
  tolgee:
    image: tolgee/tolgee:latest
    restart: unless-stopped
    ports:
      - "127.0.0.1:8080:8080"
    env_file:
      - .env
    volumes:
      - tolgee-data:/data

volumes:
  tolgee-data:
```

`.env`:

```dotenv
TOLGEE_AUTHENTICATION_ENABLED=true
TOLGEE_AUTHENTICATION_INITIAL_USERNAME=admin
TOLGEE_AUTHENTICATION_INITIAL_PASSWORD=replace-with-a-long-random-password
TOLGEE_AUTHENTICATION_JWT_SECRET=replace-with-a-different-64-character-random-secret
TOLGEE_AUTHENTICATION_REGISTRATIONS_ALLOWED=false
```

Important details:

- Keep the port bound to `127.0.0.1`. Do not expose an unconfigured Tolgee
  instance on `0.0.0.0` or forward port 8080 from your router.
- `/data` contains the embedded PostgreSQL database, screenshots, avatars, and
  generated instance secrets. Mounting a volume somewhere else does not
  preserve the instance.
- Do not commit `.env` or reuse either secret elsewhere.
- For a long-lived instance, pin a tested Tolgee release instead of upgrading
  `latest` without a backup.

Start Tolgee:

```powershell
cd C:\tolgee-paladinscat
docker compose up -d
docker compose ps
```

Open <http://127.0.0.1:8080> and sign in as `admin`. After the first successful
sign-in, change the administrator password in Tolgee and remove
`TOLGEE_AUTHENTICATION_INITIAL_PASSWORD` from `.env`.

For more Docker and backup notes, see
[SELF_HOSTED_TOLGEE.md](SELF_HOSTED_TOLGEE.md).

## 2. Create a Tolgee project

Create only the project for the catalog you intend to translate. You can add
several target languages to one project, but each CLI configuration submits one
catalog and one target language at a time.

### Website project

1. Create a project named `PaladinsCat Website`.
2. Set English (`en`) as the base language.
3. Add your target language using its exact BCP 47 tag.
4. In **Project settings** → **Advanced**, enable **Use namespaces**.
5. Leave branching disabled.
6. Enable suggestions and protect reviewed translations if those settings are
   available in your Tolgee version.
7. Keep Tolgee ICU placeholder support enabled.

Website namespaces mirror the source module paths, for example:

```text
ui/navigation
pages/home
game/items
```

Keys such as `nav.home` remain literal keys. Do not rename them or enable an
import option that converts the dot into a nested key path.

### Game-client project

1. Create a separate project named `Paladins Game Client`.
2. Set English (`en`) as the base language.
3. Add your target language.
4. Enable **Use namespaces** and leave branching disabled.
5. Disable Tolgee ICU placeholder visualization for this project.

The game catalog uses a single `game-client` namespace and stable keys such as:

```text
msg.42189
msg.100026
```

The numeric `message_id` is the serialization identity. Repeated source keys
such as `item_name` are context only and must never replace the `msg.<id>` key.

## 3. Create a least-privilege Tolgee project API key

Open the user menu in the upper-right corner and select **Project API keys**,
then choose **Add**. Select the project and give the key an expiration date.

The sync helper needs these scopes:

```text
keys.view
keys.create
keys.edit
translations.view
translations.edit
translations.state-edit
```

Do not grant administrator, member-management, screenshot, deletion, webhook,
or organization scopes. A project API key is restricted to one Tolgee project;
create a separate key if you use both catalogs.

Copy the value when Tolgee displays it. The value may not be shown again unless
you regenerate the key.

## 4. Create a PaladinsCat contribution token

Sign in to PaladinsCat and open the localization page. Create a contributor CLI
token and copy the `pcl10n_...` value when it is displayed. This token is for
submitting catalog translations only; it is not a Tolgee credential and it
does not grant GitHub access.

If the localization page does not offer token creation, first check whether the
catalog API is deployed:

```powershell
npm run l10n -- catalogs
```

If this returns HTTP 404, use the
[manual GitHub fallback](#manual-github-fallback) until the PaladinsCat backend
release containing the localization API is live.

## 5. Initialize the sync helper

The project ID is the number in the Tolgee project URL:

```text
http://127.0.0.1:8080/projects/123/translations
                                   ^^^
```

Initialize a Website configuration for German:

```powershell
cd C:\path\to\PaladinsCat-locales
npm run l10n -- init `
  --catalog website `
  --locale de `
  --project-id 123 `
  --tolgee-url http://127.0.0.1:8080
```

This creates `.paladinscat-l10n.json`. It contains project coordinates and
source revisions only and is ignored by Git.

For another catalog or locale, keep a separate ignored configuration:

```powershell
New-Item -ItemType Directory -Path .paladinscat-l10n -Force

npm run l10n -- init `
  --catalog game-client `
  --locale de `
  --project-id 456 `
  --tolgee-url http://127.0.0.1:8080 `
  --config .paladinscat-l10n/game-client-de.json
```

Replace `de`, `123`, and `456` with your target language and project IDs.

## 6. Set credentials for the current shell

The helper reads both secrets from environment variables. It never writes them
to its configuration file.

PowerShell:

```powershell
$env:TOLGEE_API_KEY = "tgpak_..."
$env:PALADINSCAT_CONTRIBUTION_TOKEN = "pcl10n_..."
```

Bash or zsh:

```bash
export TOLGEE_API_KEY='tgpak_...'
export PALADINSCAT_CONTRIBUTION_TOKEN='pcl10n_...'
```

Use the Tolgee key belonging to the project selected by the config file. Do not
place either value in `.env`, `.paladinscat-l10n.json`, a shell script, a commit,
an issue, or a screenshot.

## 7. Pull the current catalog into Tolgee

Website/default config:

```powershell
npm run l10n -- pull
npm run l10n -- progress
```

Named game-client config:

```powershell
npm run l10n -- pull --config .paladinscat-l10n/game-client-de.json
npm run l10n -- progress --config .paladinscat-l10n/game-client-de.json
```

`pull` performs several safety checks before and during import:

1. downloads the selected source and approved target catalog;
2. verifies the key count and SHA-256 checksum;
3. preserves the catalog namespace and stable key;
4. imports English as the authoritative source language;
5. imports any already-approved target strings without overwriting unexpected
   local target conflicts;
6. records the exact source revision used for the next submission.

Run `pull` before starting a new contribution and again whenever the source
catalog changes. For the large game-client project, the first import can take
several minutes.

## 8. Translate efficiently in Tolgee

Open **Translations** and display English beside your target language.

### See overall progress and remaining work

Use the translation-state filter for your target language:

- **Untranslated** shows work that remains.
- **Translated** shows completed translator work awaiting or not requiring a
  second review.
- **Reviewed** shows strings that received final translator-side review.

The `npm run l10n -- progress` command reports approved repository progress and
the number of pending or stale PaladinsCat submissions. Tolgee progress can be
ahead of repository progress until an administrator approves and merges the
submission.

### Batch repeated phrases safely

Tolgee search and translation memory are the fastest way to handle repeated
client phrases:

1. Search the English column for the exact phrase or a distinctive prefix.
2. Translate one representative key manually and save it.
3. Verify placeholders and surrounding context.
4. Keep the search/filter active and select the matching rows.
5. Use **Select all** to select all currently filtered matches, not the entire
   project.
6. Use **Pre-translate by TM** for exact translation-memory matches, or apply a
   reviewed translation only to rows whose complete English source is truly
   identical.
7. Inspect the results, then mark the intended target strings Translated or
   Reviewed.
8. Reapply the target-language **Untranslated** filter to expose everything
   that remains.

For example, 1,000 strings beginning with `This item is` may have different
endings. Search finds the group, but do not paste one complete translation over
all 1,000 unless the entire English value is identical. Translation memory can
reuse exact phrases while presenting similar phrases as suggestions for human
review.

### Batch-operation selection rule

After applying a search, namespace, tag, or state filter, selecting one row and
then choosing **Select all** selects all keys matching the active filters. Check
the displayed match count before running any batch operation.

### Placeholder and formatting rules

Preserve every placeholder exactly:

```text
{name}
@@target_name@@
%s
%1$s
```

- Do not add, remove, rename, translate, or reorder placeholders unless the
  source format explicitly permits reordering.
- Preserve line breaks, markup, escaped characters, and command names.
- For the game-client project, edit in code mode when needed. ICU visualization
  is intentionally disabled because native game tokens are not Tolgee ICU.
- Do not translate strings marked developer-only, internal-only, or otherwise
  non-translatable.

The PaladinsCat server validates keys, lengths, source revisions, placeholders,
and duplicate units again when a submission is received.

## 9. Submit for administrator approval

The helper includes every non-empty target translation in the selected project
and language whose Tolgee state is `TRANSLATED` or `REVIEWED`. Check those state
filters before submitting so drafts are not included accidentally.

Website/default config:

```powershell
npm run l10n -- submit
npm run l10n -- status
```

Named config:

```powershell
npm run l10n -- submit --config .paladinscat-l10n/game-client-de.json
npm run l10n -- status --config .paladinscat-l10n/game-client-de.json
```

A successful submission reports an ID and the status `pending`. At this point:

- no locale file has changed;
- no DAT file has been created;
- no GitHub pull request exists;
- an administrator can inspect, reject, or approve the contribution.

On approval, PaladinsCat re-downloads the current catalog, rechecks the source
revision and placeholders, and creates a GitHub pull request. A source change
causes the submission to become `needs_rebase` instead of silently applying it
to different text.

If that happens, run `pull`, inspect the affected Tolgee rows, and submit again.

## Manual GitHub fallback

Use this path when the PaladinsCat catalog API is not yet deployed or is
temporarily unavailable.

### Website

1. Fork this repository and clone your fork.
2. Start Tolgee and create the Website project described above.
3. Import each English JSON file listed in `locales/modules.json` separately.
4. Set the module path as its namespace, such as `ui/navigation`.
5. Keep keys flat; `nav.home` must remain `nav.home`.
6. Translate and review the target language.
7. Export flat JSON by language and namespace.
8. Place the files under `locales/<locale>/<namespace>.json`.
9. Validate and test:

   ```powershell
   npm run validate
   npm run test:l10n
   ```

10. Commit only the target-language JSON files and open a pull request.

### Game client

Approved game translations are stored as UTF-8 CSV files:

```text
game-client/de.csv
game-client/fr.csv
```

Each contains only `message_id,value`. Do not replace the numeric ID with a
repeated source key. The decoded English source catalog is supplied through the
catalog API; game binaries, XOR keys, and decrypted DAT files do not belong in
this repository.

After a reviewed CSV is merged, the desktop GameDecoder serialization workflow
can build a client DAT file. The PaladinsCat web server never decrypts or
serializes game binaries.

## Updating, stopping, and backing up Tolgee

Stop without deleting data:

```powershell
docker compose stop
```

Start again:

```powershell
docker compose start
```

Before an upgrade, export important target languages from Tolgee and back up
the `/data` volume. `docker compose down` keeps named volumes;
`docker compose down --volumes` permanently deletes them.

Do not upgrade a working instance and delete its old volume in the same step.
Verify that projects, key counts, languages, and API keys survived before
removing any rollback copy.

## Troubleshooting

| Symptom | Cause and action |
|---|---|
| `404` from `paladinscat.com/api/localization/...` | The localization backend is not deployed. Use the manual fallback. |
| `namespace_cannot_be_used_when_feature_is_disabled` | Enable **Use namespaces** in the Tolgee project, then run `pull` again. |
| `Tolgee source differs from PaladinsCat` | English was edited locally or the source changed. Do not overwrite it manually; run `pull` and review the change. |
| `Catalog changed ... run pull` | The recorded source revision is stale. Pull, review, and resubmit. |
| `Tolgee has no TRANSLATED or REVIEWED target strings` | Translate a non-empty target value and mark its state Translated or Reviewed. |
| `401` from Tolgee | The project API key is wrong, expired, or belongs to another project. Regenerate a least-privilege key. |
| `401` from PaladinsCat | The contribution token is wrong, expired, or revoked. Create a new scoped token while signed in. |
| Existing target conflict during `pull` | Tolgee kept an unexpected local target instead of overwriting it. Compare it with the approved repository text before deciding which version is correct. |
| Game-client editor is slow | Give Docker more memory, show only English and one target language, and work with namespace/state/search filters. |
| Submission is `needs_rebase` | The source changed before approval. Pull the new catalog and submit a replacement. |

## Security checklist

- Keep Tolgee on loopback unless you intentionally configure TLS, authentication,
  firewall rules, backups, and updates for a shared server.
- Use a project API key instead of a personal access token.
- Grant only the six scopes listed in this guide.
- Give each project its own expiring key and rotate it periodically.
- Keep Tolgee and PaladinsCat tokens in environment variables or a proper secret
  manager, never Git.
- Never upload `.env`, `.paladinscat-l10n*`, Tolgee volumes, database dumps,
  private keys, DAT files, XOR material, or decrypted game binaries.
- Do not configure a Tolgee webhook pointing at PaladinsCat. The local helper
  initiates all exchange requests and works behind NAT.

## References

- [Tolgee: running with Docker](https://docs.tolgee.io/platform/self_hosting/running_with_docker)
- [Tolgee: project API keys](https://docs.tolgee.io/platform/account_settings/api_keys_and_pat_tokens)
- [Tolgee: editing translations](https://docs.tolgee.io/platform/projects_and_organizations/editing_translations)
- [Tolgee: translation memory](https://docs.tolgee.io/platform/translation_process/translation_memory)
- [Tolgee: batch operations](https://docs.tolgee.io/platform/translation_keys/batch_operations)
- [PaladinsCat translation platform design](TRANSLATION_PLATFORM.md)
