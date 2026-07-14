# Repository-first translation architecture

GitHub is the translation database and the only approval boundary.

```text
shared Tolgee web UI
        ↓ scheduled Tolgee CLI export on GitHub Actions
GitHub pull request (automation/tolgee-export)
        ↓ validation and merge
PaladinsCat-locales main
        ↓ pinned submodule revision
PaladinsCat frontend image and VPS deployment
```

Tolgee retains a local editing database for translation memory, state, and batch
operations. The checked-in files remain authoritative. PaladinsCat no longer
stores localization drafts, API tokens, submissions, or approval state.

The GitHub workflow holds its Tolgee project key in GitHub Actions secrets, not
on the PaladinsCat VPS. A local Tolgee plus GitHub Desktop remains available for
contributors who do not use the shared project.

Pull-request validation enforces repository structure, per-namespace source
keys, non-empty values, length limits, Unicode validity, and exact placeholder
preservation. Human wording review happens once on GitHub.

The private PaladinsCat application repository records the exact reviewed
locale commit as a Git submodule pointer. The VPS deploy initializes that pinned
revision and copies its `locales/` directory into the frontend image. Updating
translations therefore requires a locale pull request followed by a mechanical
submodule-pointer update, not another translation approval.
