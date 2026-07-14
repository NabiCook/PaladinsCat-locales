# Contributing with a private Tolgee instance

You may use Tolgee on your own computer without giving PaladinsCat access to
your server. Tolgee is only an editor and translation-memory workspace; the
reviewed contribution is still submitted to the public locale repository.

For the Docker installation, see [SELF_HOSTED_TOLGEE.md](SELF_HOSTED_TOLGEE.md).

## Website translations available today

Until the PaladinsCat catalog API is available, use the public Git repository
as the exchange point.

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

## Planned catalog API workflow

When the localization data service and companion sync helper are released, the
manual clone/import/export steps will become:

```powershell
paladinscat-l10n init --catalog website --locale de --tolgee-url http://127.0.0.1:8080
paladinscat-l10n pull
paladinscat-l10n submit
```

These commands document the intended interface; `paladinscat-l10n` is not yet
published. The helper will use a PaladinsCat contribution token only for
submission. It will never upload a Tolgee administrator token.

## Game-client translations

The planned `game-client` bundle will use keys in this form:

```text
msg.42189
msg.100026
```

The numeric message ID is the stable identity. A game key such as `item_name`
may occur thousands of times and is supplied only as translator context.

The bundle will contain English text, placeholders, contextual key names, and a
source revision. Contributors will import the XLIFF 1.2 or CSV bundle into their
local Tolgee project, translate it, and submit an export through the same data
service. Approved translations will be joined back to DAT records by message ID
and validated before a game localization artifact is produced.

## Contribution rules

- Translate values only; never rename translation keys.
- Preserve placeholders such as `{name}` and `@@target_name@@` exactly.
- Do not translate markup, command names, or values marked non-translatable.
- Submit one catalog and target language per contribution bundle.
- Partial translations are welcome.
- Do not include Tolgee databases, credentials, API tokens, or Docker volumes.

