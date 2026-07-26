# Game-client translation artifacts

Approved game translations are stored as one UTF-8 CSV per game language:

```text
game-client/de.csv
game-client/fr.csv
```

Each file has exactly two columns:

```csv
message_id,value
42189,Translated text
```

`message_id` is the stable identity from the decoded game catalog. Files are
committed on a translation branch and reviewed as a normal GitHub pull request.
Do not replace IDs with the repeated game `key` field.

## Native game sources

The checked-in packs are generated from native game language data, not from
machine translation or string-key matching. `source-manifest.json` records the
game language code, source package checksum, and exact string count for every
pack. This preserves the terminology players see in the game, including
champion, ability, item, card, and mode names.

Refresh all supported packages from a sibling `PaladinsCat-Tempest` checkout:

```powershell
python scripts/import-game-client-locales.py
npm run validate
```

The importer exports current client languages only: `en`, `de`, `es-419`, `fr`,
`ja`, `ko`, `pl`, `pt-BR`, `ru`, `tr`, `zh-CN`, and `zh-TW`. Korean uses the
maintained decoded catalog because its merged DAT is not re-decodable. The
importer deliberately excludes `ESN` (the stale English fallback) and `DEB`
(debug English).

## Game-term glossary for UI translation

Build the curated native-term glossary after refreshing the client packs:

```powershell
python scripts/build-game-term-glossary.py
```

`term-glossary.json` is the authority for game-specific UI terms such as
champion, ability, loadout, card, and queue/mode names. Apply those terms when
translating frontend UI and surrounding prose. Translate ordinary copy normally;
do not use the game catalog as a blanket machine-translation source.

`translate-frontend-general-copy.py` applies this rule mechanically: it direct-
translates non-game frontend modules only, masks native glossary terms and
placeholders during translation, and restores them afterward. It never touches
Korean or `game/*` descriptions.

## Frontend game terms

To add native terms and descriptions to the frontend, run the second importer
after refreshing the client packs:

```powershell
python scripts/import-frontend-game-locales.py
npm run validate
```

It writes only exact, unique English-to-`message_id` matches into the partial
`locales/<language>/game/*.json` files. This keeps official skill, talent, and
loadout descriptions intact in their native language. Existing translations are
preserved by default. Use `--force` only after reviewing a source update. The
companion `frontend-game-match-manifest.json` reports the coverage and makes
gaps explicit; unmatched strings remain available for human translation instead
of being guessed.

These CSVs are translation artifacts, not game binaries. Use the desktop
GameDecoder serialization workflow to build a DAT file from a reviewed CSV.
The game-client source manifest must be available in the contributor's local
toolchain before adding a target CSV; the PaladinsCat VPS no longer publishes a
game catalog or stores game translation submissions.
