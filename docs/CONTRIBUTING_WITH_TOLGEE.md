# Contributing with a private Tolgee instance

You may use Tolgee on your own computer without giving PaladinsCat access to
your server. Tolgee is only an editor and translation-memory workspace; the
reviewed contribution is still submitted to the public locale repository.

For the Docker installation, see [SELF_HOSTED_TOLGEE.md](SELF_HOSTED_TOLGEE.md).

## Automated catalog workflow

After the federated localization backend release is deployed, create a scoped
CLI token from the PaladinsCat localization page. In your cloned
`PaladinsCat-locales` repository, initialize the helper with the numeric ID of
your local Tolgee project:

```powershell
npm run l10n -- init --catalog website --locale de --project-id 1 --tolgee-url http://127.0.0.1:8080
```

Set both credentials for the current PowerShell session. The Tolgee key is a
project API key from your private Tolgee project; the PaladinsCat token is the
scoped value shown once by the website.

```powershell
$env:TOLGEE_API_KEY = "your-local-tolgee-project-key"
$env:PALADINSCAT_CONTRIBUTION_TOKEN = "pcl10n_..."
```

Download the current catalog, verify its checksum, and import it into Tolgee:

```powershell
npm run l10n -- pull
```

Translate in Tolgee. When the intended strings are marked `TRANSLATED` or
`REVIEWED`, submit them to the administrator queue:

```powershell
npm run l10n -- submit
npm run l10n -- status
```

The helper never stores either secret. It records only project coordinates,
the source revision, checksum, and last submission ID in
`.paladinscat-l10n.json`, which is ignored by Git.

## Manual GitHub fallback

If the catalog endpoint is not yet deployed, use the public Git repository as
the exchange point.

1. Fork and clone `NabiCook/PaladinsCat-locales`.
2. Start your local Tolgee instance and create a project with English as its
   base language and your translation language as a target.
3. Import the English JSON files listed in `locales/modules.json`. Import one
   module at a time and assign its module path as the namespace. For example,
   import `locales/en/ui/navigation.json` into namespace `ui/navigation`.
4. Keep key nesting disabled. Keys such as `nav.home` must remain unchanged.
5. Translate in Tolgee. Translation memory, search, filters, and batch
   operations may be used normally.
6. Export your target language as flat JSON with this file layout:

   ```text
   {languageTag}/{namespace}.{extension}
   ```

7. Extract the export into the repository's `locales/` directory. A German
   navigation export should become `locales/de/ui/navigation.json`.
8. Validate the files:

   ```powershell
   node scripts/validate-locales.mjs
   ```

9. Commit only the target-language JSON files and open a pull request.

Maintainers review every pull request before merging. An exported file is not
used by the website until it reaches the repository's default branch.

## Game-client translations

The `game-client` bundle uses keys in this form:

```text
msg.42189
msg.100026
```

The numeric message ID is the stable identity. A game key such as `item_name`
may occur thousands of times and is supplied only as translator context.

The endpoint becomes available when the PaladinsCat deployment supplies
`LOCALIZATION_GAME_CATALOG_FILE`. It contains English text, placeholders,
contextual key names, and a source revision. Administrator approval creates a
pull request for `game-client/{locale}.csv`. After merge, the desktop
GameDecoder tool can serialize that reviewed `message_id,value` artifact back
to DAT; the PaladinsCat server never handles game binaries or XOR material.

## Contribution rules

- Translate values only; never rename translation keys.
- Preserve placeholders such as `{name}` and `@@target_name@@` exactly.
- Do not translate markup, command names, or values marked non-translatable.
- Submit one catalog and target language per contribution bundle.
- Partial translations are welcome.
- Do not include Tolgee databases, credentials, API tokens, or Docker volumes.
