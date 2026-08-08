# Weblate to GitHub workflow

Weblate is the primary place to translate PaladinsCat at
[translate.paladinscat.com](https://translate.paladinscat.com). It must use its GitHub
pull-request integration, never direct pushes to `main`.

## Contributor and reviewer flow

1. Open [translate.paladinscat.com](https://translate.paladinscat.com), then
   choose a language and namespace.
2. Submit a translation or suggestion, preserving placeholders exactly.
3. A language reviewer approves the wording in Weblate.
4. Weblate synchronizes approved changes to its dedicated branch and opens or
   updates one pull request against `main`.
5. A maintainer checks the GitHub diff and required validation, then merges.

Weblate review is linguistic QA. GitHub pull-request review and the required
`npm run validate` check remain release authorization.

## Project configuration

- Import `locales/en` as the source language and target files under
  `locales/<locale>`; keep namespace paths intact.
- Enable repository webhooks so Weblate pulls English source updates promptly.
- Configure a dedicated GitHub bot with only this repository's content and
  pull-request permissions.
- Restrict Weblate registration and assign language-review permissions to
  trusted reviewers.
- Do not store the bot token in this repository, locale files, or the frontend.

## Source updates and conflicts

Application changes update canonical English in a normal pull request. After
merge, Weblate pulls the source change through its webhook or scheduled sync.
Resolve any Weblate Git conflict before creating a translation pull request;
do not overwrite changed English keys from Weblate.
