# Federated translation platform

PaladinsCat does not need to operate a public Tolgee server. The recommended
design is a format-neutral localization data service: contributors may edit in
the PaladinsCat website, a private Tolgee instance on their own computer, or
another translation tool that supports the same exchange files.

## Status

Direct GitHub pull requests work today. The catalog and submission endpoints
described below are the contract for the planned PaladinsCat data service; they
must not be advertised as live until the backend implements them.

## Trust boundary

```text
PaladinsCat/GitHub source
        |
        | public catalog export
        v
contributor sync helper <-> contributor-owned Tolgee
        |
        | authenticated contribution bundle
        v
validation -> pending submission/PR -> maintainer approval -> production
```

The contributor's computer always initiates the connection. PaladinsCat never
connects to a contributor's Tolgee API, and a contributor never receives a
PaladinsCat infrastructure or GitHub App credential.

## Catalogs

The service exposes two independent catalogs:

- `website`: PaladinsCat interface text. Existing module paths, such as
  `ui/navigation`, map to translation namespaces.
- `game-client`: Paladins client text extracted from localization DAT files.
  Its stable translation key is `msg.<message_id>`. The repeated game `key`
  field is context only and must never be used as the unique translation key.

Both catalogs use English as their base language. Each downloadable bundle has
a manifest containing the schema version, catalog ID, source revision, source
language, key count, and SHA-256 checksum.

## Planned HTTP contract

### Discover catalogs

```http
GET /api/localization/v1/catalogs
```

Returns catalog metadata, current source revisions, supported languages,
formats, and download URLs. This endpoint is public and cacheable.

### Download a working bundle

```http
GET /api/localization/v1/catalogs/{catalog}/export?locale=de&format=xliff
```

Supported formats should be:

- XLIFF 1.2 for Tolgee and other translation systems;
- flat JSON for website modules;
- UTF-8 CSV for spreadsheets and the game localization toolchain.

Responses include an `ETag`, `Content-Disposition`, source revision, and bundle
checksum. Conditional requests with `If-None-Match` avoid downloading unchanged
catalogs.

### Submit a contribution

```http
POST /api/localization/v1/submissions
Authorization: Bearer <PaladinsCat contribution token>
Content-Type: multipart/form-data
```

The request contains `catalog`, `locale`, `format`, `baseRevision`, and the
translation file. It creates a pending submission or GitHub pull request; it
never changes a released locale directly.

```http
GET /api/localization/v1/submissions/{submissionId}
Authorization: Bearer <PaladinsCat contribution token>
```

Returns validation and review status to the submitting user.

### Display progress

```http
GET /api/localization/v1/progress?catalog=website
```

Returns approved, pending, untranslated, and stale counts per language. Public
progress is calculated from the approved GitHub snapshot plus pending
submissions, not from any contributor's private Tolgee instance.

## Validation and approval

Every submission must be treated as untrusted input. The backend must enforce:

- signed-in contributor identity, scoped tokens, rate limits, and upload limits;
- known catalog, locale, source revision, and translation keys;
- exact placeholder preservation and valid Unicode;
- no source-language edits, scripts, binary executables, or path traversal;
- decompression limits and safe archive handling;
- duplicate-ID rejection for game-client data;
- stale-source reporting when the submitted base revision is no longer current.

A valid submission remains pending until a maintainer approves and merges it.
Production continues to read approved files from the default branch of the
public locale repository.

## Synchronization helper

A small `paladinscat-l10n` companion CLI or container should perform the
Tolgee-specific work:

1. download and verify the current bundle;
2. import it into the contributor's local Tolgee project;
3. export the chosen target language from Tolgee;
4. package the export with its original source revision;
5. submit it to PaladinsCat and display validation results.

This helper is preferable to Tolgee webhooks. It works behind NAT, requires no
public port on the contributor's computer, and keeps the exchange protocol
usable by tools other than Tolgee.

## GitHub synchronization

GitHub remains the release ledger:

1. application changes update canonical English website modules;
2. game extraction updates the canonical game-client source manifest;
3. public export endpoints serve those revisions;
4. accepted submissions create branches or pull requests;
5. GitHub Actions validates the resulting files;
6. a maintainer merges the approved changes.

Do not implement unrestricted two-way synchronization. Source keys flow out
from GitHub/PaladinsCat; target-language contributions flow back through the
validated submission endpoint.
