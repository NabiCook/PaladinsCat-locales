# Game-client releases

## Ownership

| Content | Canonical owner |
|---|---|
| Public launcher GUI, installers and release tools | Independent `PaladinsCat-Launcher` repository |
| Native compiler, resolver, font converter and IME implementation | `Z:\NABI\Project\PaladinsCat-WatchCat` |
| Native catalogs and reviewed translation inputs | This repo: `game-client/` and `game-client/native/translations/` |
| Download catalog and package contracts | This repo: `game-client/catalog.json`, `schema/` |
| Local generated drafts | This repo: ignored `game-client/.release-staging/` |
| Published binary payloads and manifests | Immutable GitHub Release assets on `NabiCook/PaladinsCat-locales` |

Do not copy patcher or IME source into this repository. Keep current reviewed
translations here; WatchCat dated review/capture evidence remains in WatchCat.
Distribute the GUI with its embedded font's `Inter-LICENSE.txt`, retained from
WatchCat's asset directory. Internal diagnostic helpers and the bounded build
runner are development tools and are not required in the end-user GUI package.
No game originals, private diagnostics, credentials or machine-specific
diagnostic manifests belong in Git or public release assets.

## Download contract

The patcher reads
`https://raw.githubusercontent.com/NabiCook/PaladinsCat-locales/main/game-client/catalog.json`.
Catalog v1 has `packages` for locale bundles and optional `ime_packages` for IME
releases. An empty array offers no release. A source/catalog commit does not
publish downloadable packages. The GUI also accepts an explicit public GitHub
catalog asset URL in Repository settings, while retaining the repository link.
This permits inspection of a published preview before its catalog update reaches `main`.

Every entry identifies an immutable manifest URL and its SHA-256. Each manifest
pins the supported game executable and every payload hash/size. HTTPS GitHub
is the current publisher trust boundary; publisher signatures are not yet used.
The patcher reuses verified cached assets. A correction is a new immutable
release and catalog entry, not replacement of an existing asset.

Locale bundles retain the WatchCat v1 manifest and exact writable-file allowlist.
They carry the reviewed locale source commit and client build/fingerprint.
Record the exact committed IME source and packaging executable hash in release
provenance. Do not label an IME-only commit as the packaging implementation
commit. An update to the game requires renewed native mapping, hash, package and
visual checks.

## IME package

An IME release uses `schema/ime-package.schema.json`: package/version identity,
`Win64`, `KOR`, native ABI `[4,9,7,1]`, executable fingerprint, DLL hash/size,
WatchCat `source_commit`, and raw GitHub download descriptor.

From WatchCat, after building the source:

```powershell
$localeRepo = 'C:\Users\nabi\PaladinsCat\paladinscat-locales'
paladinscat-release.exe ime PATH_TO_BUILT_DLL $localeRepo 0.1.0
paladinscat-release.exe validate $localeRepo
```

The `ime` command creates a new ignored draft directory containing
`ime-package.json` and `PaladinsCatImeFix.dll`. The `validate` command separately
reads the catalog, native JSON dependencies and approval hashes without changing
them. No catalog entry, game installation or publication is
performed. The builder checks the actual x64 DLL exports and native ABI without
executing it. `draft:true` and an empty source commit deliberately prevent remote
distribution; local GUI import accepts a verified draft for preparation.

Before publication, review/commit the exact WatchCat source, record its commit,
freeze and hash the payload, add the final GitHub asset URL/descriptor, and set
`draft:false`. Revalidate the final manifest, supported build, installer rollback
and relevant live acceptance. The relocated/path-portable build has CPU checks;
the earlier v4-r1 gameplay result is evidence for that frozen build only. Live
disable and a new portable client trial remain separately unverified.

A user-authorized preview may be published with those pending checks explicitly
listed in both catalog and manifest notes. `draft:false` permits downloading; it
does not mean stable, fully translated, or accepted on a live client. Mark the
GitHub release as a prerelease, exclude it from latest stable, and retain the
pending gates in provenance. Stable promotion still requires those checks.

Upload immutable payloads/manifests first, then review the catalog change with
their final manifest hashes. Apply parent publication rules; preparation does
not authorize push or publication. The GUI installs the fixed mod directory
`.tempest/v2/mods/PaladinsCat-IME`, independently of translation files. Tempest
loads it on the next launch; no resident WatchCat background service is needed.

## Source publication

Owner-directed agent work stays in the existing `main` checkout. The human
prohibits creating branches, worktrees, forks or pull requests for this workflow.
Review and validate the source before an authorized publication, respecting
remote protections. External contributor/Weblate PR procedures are separate.
Keep immutable approval
receipts byte-identical and validate their pins before committing. Commit the
native dictionaries, receipts, ownership snapshot, catalog contracts and docs;
exclude ignored staging data and machine-specific diagnostic manifests.

The WatchCat Rust native repository validator checks dictionary dependencies and
approval hashes. Its local publication guard additionally checks the exact
checkout and GitHub destination, a clean worktree, the permitted source paths,
credential patterns in all reachable blobs, and non-deleting, forward-moving
updates from the existing `main` checkout to `refs/heads/main`. Feature-branch
publication is refused. Guard source and local hook wrappers belong to WatchCat. This
source push is independent of uploading binary release assets or completing the
full localization coverage and visual acceptance gates.

## Published preview: 2026-10-10

[game-client-preview-20261010-r1](https://github.com/NabiCook/PaladinsCat-locales/releases/tag/game-client-preview-20261010-r1)
contains Korean v172 and IME 0.1.0 for the exact Win64 8.1 executable fingerprint.
Both catalog entries and manifests explicitly say PREVIEW. Translation review,
unresolved native ownership, targeted visual checks, portable IME gameplay and
live disable remain pending.

| Manifest | SHA-256 |
|---|---|
| `locale-package.json` | `a67cdc912b2420e4885f2eb0fcfb628c5c08b6ba20e0f2eb5bfc3e6a6474ea5c` |
| `ime-package.json` | `b64c71f21d472afd62ccc114f9faa68c23f76e53c52e83bcdf26815085581f7e` |

Locale source: `9192457a4907d3508c5de0ffe6ef6dff54fa6d16`.
WatchCat IME source: `3b361669eedd02190f7a242483e3bfa84cd63775`.
The release has 15 immutable assets, including nine compressed locale payloads,
the DLL, both manifests, the catalog, provenance and font notice. The production
Rust download engine verified both packages from a fresh cache, including
compressed and decoded hashes/sizes, actual DLL exports and ABI `[4,9,7,1]`.
These checks did not install into a game or execute the DLL.

Reproduce in WatchCat with the built `paladinscat-release` Rust CLI:

```text
assemble-preview BUNDLE_JSON IME_PACKAGE_JSON LOCALE_REPO NEW_TAG LOCALE_COMMIT IME_COMMIT
verify-downloads PUBLIC_CATALOG_URL NEW_EMPTY_CACHE_DIRECTORY
use-catalog PUBLIC_CATALOG_URL
```

`assemble-preview` refuses an existing tag directory, prepares gzip payloads,
final manifests, catalog and provenance under ignored `.release-staging`, and
publishes nothing. Upload all assets to a draft GitHub prerelease, verify their
identities and sizes, then publish under the user's release authorization.
Run `verify-downloads` against the public asset catalog in a fresh cache before
offering it. `use-catalog` downloads/verifies both families into the GUI cache
and persists that catalog URL and prepared selections; it changes no game files.
Review the matching `game-client/catalog.json` in existing `main`, then publish
under the user's established release authorization. Do not create a PR or bypass
remote protections.

## Korean terminology preview: 2026-10-14

[game-client-preview-20261014-v174](https://github.com/NabiCook/PaladinsCat-locales/releases/tag/game-client-preview-20261014-v174)
updates the Korean localization package to `kor-ui-v174-skills-bf6ef4ec41f7`.
Skills and abilities use 스킬; View Skills uses 스킬 확인; champion selection
uses 선택. The existing IME 0.1.0 catalog entry and its previous immutable
manifest remain unchanged. The old v172 release remains available as history.

Locale source: `aeb5a91065d90daca8b4f513c01dca0288f35821`.
Final `locale-package.json` SHA256:
`80aa4b5fe2a67dcc5f1691a9906e4a443f6dd61afe368603718b835d0adadef9`.
The release contains ten compressed localization payloads, the locale manifest,
catalog, packaging provenance and font notice. Full translation, unresolved
native-source coverage and targeted visual review remain pending; this is a
terminology preview, not stable or complete localization.

Localization-only preparation used the maintainer's Rust launcher release-tool
working tree. As checked on 2026-10-14, published Launcher `main` is 0.3.5 and
does not yet include `assemble-locale-preview` or `validate-catalog`. The commands
here describe those pending maintainer interfaces, not features available in
the published 0.3.5 CLI:

```text
assemble-locale-preview BUNDLE_JSON LOCALE_REPO NEW_TAG LOCALE_COMMIT SHORT_PREVIEW_NOTES
```

It preserves the existing `ime_packages` array, refuses replacing an existing
staging directory, verifies decoded inputs while compressing and pins every
download hash/size. Publish the immutable prerelease assets first, verify the
public download with `verify-downloads` and an empty cache, then update the
existing main catalog. A source push alone cannot update downloadable assets.

## Korean DLC and system preview: 2026-10-14

[game-client-preview-20261014-v175-r1](https://github.com/NabiCook/PaladinsCat-locales/releases/tag/game-client-preview-20261014-v175-r1)
contains 2,158 system-message corrections and 93 DLC/product body translations.
The owner authorized general wording, with later corrections through issue
reports. The new per-message authoring files preserve exact ID, key, English
source and prior target; the display dictionary links them through `record_files`.
The queue message reads 대전 대기열에 입장했습니다. Existing approved names and
스킬 terminology remain intact.

Locale source: `399ba9472b0dad8166c170947b118dbfe2d3369a`.
Final manifest SHA256:
`678e684513159582e4d6bbc3dc29534e5a214c2ec3939ffe0863a190ebeb10c9`.
DAT SHA256:
`dda1158c2f68f8ce943447d00e5a4d3367ea329ee3852653c3b2271341e915b9`.
Only the DAT payload changed; nine unchanged payloads retain their immutable
v174 URLs and hashes. The v174 update cache reused those nine verified artifacts
and downloaded the new DAT, then verified all ten decoded payloads. IME 0.1.0
retains its prior manifest and payload. The managed translation cache contains
one latest bundle after the update.

With a maintainer build containing the pending CLI modes, run
`validate-catalog CATALOG_JSON` before publication to check the catalog's
actual launcher contract; locale entries require `bundle_id`, while IME entries
use `package_id`. This package remains a preview; unrelated native source
coverage remains pending. Wording/visual feedback for this batch is on demand.

## Korean objective terminology preview: 2026-10-14

[game-client-preview-20261014-v176-r1](https://github.com/NabiCook/PaladinsCat-locales/releases/tag/game-client-preview-20261014-v176-r1)
standardizes five source-bound capture-point objective messages with 거점.
The reviewed rows are MSG_BONUS_OBJ_POINTS (23028), Objective Captured (%)
(1000011383), Distance From Current Objective (1000022297), Has Current
Objective (1000022332), and the objective mitigation description (1000146978).
Other uses of “point” for locations, checkpoints, and abilities are unchanged.

Locale source: `587c38b8042b1eefa8150f55ff04456e8abbad41`.
Bundle: `kor-ui-v176-objective-ebc8c79b0c0b`.
Final `locale-package.json` SHA256:
`f1ffab96a98f7115163eabba05588700cb0bd101dc92d49de01a1949b60aa1fe`.
DAT SHA256:
`ebc8c79b0c0b44f6fb93446b125f80778d111a5506f8b61ffe57630373266041`.
Only the compressed DAT is new; nine unchanged payloads keep their immutable
v174 URLs and hashes. The existing IME entry is unchanged. The GitHub prerelease
contains the DAT, manifest, catalog, provenance, font notice and release notes.
The package remains a preview; full translation coverage and in-game visual
acceptance are pending. No game files were changed.

## Korean v177: 2026-10-15

Preview release: [Korean v177](https://github.com/NabiCook/PaladinsCat-locales/releases/tag/game-client-preview-20261015-v177-r2).
Bundle: `kor-ui-v177-1a73a309d6ab`.

The candidate standardizes Gold as 골드 in 57 reviewed DAT entries while
retaining the v176 objective wording 거점. Only the Korean DAT payload changes;
nine unchanged assets reuse their verified immutable v174 URLs and hashes.

Locale source commit: `ab5e06a116b193b47237c97259d7a75a4dc0a0e5`.
Manifest SHA256: `a6b51a6dee1c023c0c3cb1772c44f86a8fa754307b0ccc2603b4609213359b2a`.
DAT SHA256: `1a73a309d6ab6e2d12e304a755e2ab1c0ca771ed03e899f9e8f1f87226689383`.

Revision r2 corrects only the package identity and short version label. All ten
payload descriptors are byte-for-byte equivalent to r1, including their existing
immutable URLs, sizes and hashes. The game revision remains v177. Existing r1
assets are preserved; the rolling main catalog pins the new metadata revision.
Version titles are plain (`Korean v177`); translation details belong here and in
release notes, rather than version names. The main-only red line is enforced by
GitHub rules, local reference transactions and the publication validator.

The approved native-name subset gate passes; the full name gate remains blocked
by existing unresolved coverage (108 localized unclassified names, 449 partly
English names, 8,697 unclassified source records and 46,936 unreviewed names).
Full localization and in-game visual acceptance remain pending. The preview
assets are published; they have not been installed, and no game files were changed.
