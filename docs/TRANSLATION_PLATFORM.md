# Translation platform plan

## Recommended: self-hosted Weblate

Run Weblate as a separate service and connect it **only** to this public
`PaladinsCat-locales` repository. Configure each file listed in
`locales/modules.json` as a Weblate component. Translators use the Weblate web
interface; Weblate creates commits or pull requests containing only locale JSON
changes.

Do not connect Weblate, Pontoon, or any translator account to the private
PaladinsCat application repository.

## Safe workflow

1. The private application updates its canonical English modules.
2. `npm run sync-community-locales -- <public-repository-path>` updates
   `locales/en/` and `locales/modules.json` in this repository.
3. A maintainer commits those English changes to this public repository.
4. Weblate pulls the update and exposes changed strings to translators.
5. Weblate pushes a branch or pull request with translated modules.
6. GitHub Actions validates keys and JSON before the maintainer merges it.

## Why Weblate instead of Pontoon

Both are capable version-control-driven translation systems. Weblate has a
straightforward self-hosted option and documented continuous localization with
Git-hosting integration. Pontoon is a sound option for a larger Mozilla-style
community, but its own project documentation says production deployment needs
adaptation outside its documented Heroku path and warns against production
Docker deployment.

For PaladinsCat, start with GitHub pull requests and the included validator.
Introduce self-hosted Weblate when enough translators need a browser-based
editor, translation memory, review queue, or glossary.
