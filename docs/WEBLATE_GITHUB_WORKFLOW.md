# Weblate to GitHub workflow

Weblate is the primary place to translate PaladinsCat at
[translate.paladinscat.com](https://translate.paladinscat.com). Maintainers review
and validate translation changes before publishing them to GitHub `main`.

## Contributor and reviewer flow

1. Open [translate.paladinscat.com](https://translate.paladinscat.com), then
   choose a language and namespace.
2. Submit a translation or suggestion, preserving placeholders exactly.
3. A language reviewer approves the wording in Weblate. The project commit
   policy excludes every string that is not in Weblate's approved state.
4. A maintainer reviews the approved translation diff and runs `npm run validate`.
5. Publish the reviewed changes through the owner-approved `main` workflow.
   External Git contributors submit pull requests from personal forks.
6. The frontend's hourly locale-pin workflow detects the merged locale commit,
   validates it, compiles the complete frontend, and only then opens a
   protected frontend pull request for the mechanical submodule-pin change.

Weblate review is linguistic QA. Maintainer review and the required
`npm run validate` check remain release authorization.

The upstream repository permits only `main`. Translation automation must use a
permitted fork-based path; it must not create an upstream translation branch.

## Project configuration

- Import `locales/en` as the source language and target files under
  `locales/<locale>`; keep namespace paths intact.
- The self-hosted Weblate GitHub App is connected to the PaladinsCat workspace
  and installed only for `PaladinsCat-locales`. Its app webhook updates Weblate
  after merged source changes.
- Reviews are enabled and the project quality policy is **Only include approved
  translations**. Reviewers use a project-scoped role; contributors cannot
  approve their own wording by virtue of translation access.
- Restrict Weblate registration and assign language-review permissions to
  trusted reviewers.
- Do not store the bot token in this repository, locale files, or the frontend.

The platform sync helper's upstream-branch PR flow conflicts with this policy.
Reconcile that flow before using the helper to publish translation changes.

## Source updates and conflicts

Application maintainers update canonical English directly on `main` after
`npm run validate` passes. Weblate then pulls the source change through its
webhook or scheduled sync.
Resolve any Weblate Git conflict before publishing translation changes;
do not overwrite changed English keys from Weblate.

If the project-wide repository conflict auto-locks the Weblate components
(`auto_lock_error`), recover it with the documented procedure in the
operations runbook `localization-release.md` ("Weblate lock recovery"):
back up the diverged VCS state, reset the local repo to `origin/main`,
unlock the components via Weblate's supported path, and clear the stale
`MergeFailure` alert with a successful repository update.
