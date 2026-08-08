# Repository-first translation architecture

GitHub `main` is the authoritative translation database and release approval
boundary. Weblate is the contributor workspace and linguistic-review layer.

```text
shared Weblate web UI
        ↓ reviewer-approved changes synchronized by Weblate
GitHub pull request (Weblate-owned branch)
        ↓ repository validation and maintainer merge
PaladinsCat-locales main
        ↓ pinned submodule revision
PaladinsCat frontend image and VPS deployment
```

Weblate retains drafts, translation memory, review state, and contributor
permissions. The checked-in files remain authoritative. PaladinsCat does not
store localization drafts, API tokens, submissions, or approval state.

Weblate is hosted separately from the frontend and uses a narrowly scoped GitHub
bot credential. Credentials remain in Weblate or GitHub Secrets, never in a
locale file or frontend environment. Local Git plus GitHub Desktop remains a
fallback for contributors who cannot use Weblate.

Pull-request validation enforces repository structure, per-namespace source
keys, non-empty values, length limits, Unicode validity, and exact placeholder
preservation. Weblate language reviewers perform wording QA; GitHub maintainers
review the resulting diff and merge only after validation passes.

The private PaladinsCat application repository records the exact reviewed
locale commit as a Git submodule pointer. The VPS deploy initializes that pinned
revision and copies its `locales/` directory into the frontend image. Updating
translations therefore requires a locale pull request followed by a mechanical
submodule-pointer update, not another translation approval.
