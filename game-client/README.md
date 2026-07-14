# Game-client translation artifacts

Approved game translations are stored as one UTF-8 CSV per target language:

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

These CSVs are translation artifacts, not game binaries. Use the desktop
GameDecoder serialization workflow to build a DAT file from a reviewed CSV.
The game-client source manifest must be available in the contributor's local
toolchain before adding a target CSV; the PaladinsCat VPS no longer publishes a
game catalog or stores game translation submissions.
