# PaladinsCat community translations

This public repository is the source of truth for PaladinsCat translations.
Contributor translation changes are reviewed through Weblate and GitHub.
Maintainer-owned canonical English source updates are validated locally and
committed directly to `main`.

## Contribute

Translate in the [PaladinsCat Weblate project](https://translate.paladinscat.com).
Maintainers review and validate approved translations before publishing them to
GitHub `main`. Git contributors use personal forks and pull requests.

- [Contribution rules](CONTRIBUTING.md)
- [Weblate and GitHub workflow](docs/WEBLATE_GITHUB_WORKFLOW.md)
- [Local Git fallback](docs/LOCAL_GIT_FALLBACK.md)

Run the locale validator before every commit:

```powershell
npm install
npm run validate
```

## Repository layout

- `locales/modules.json` lists website translation namespaces.
- `locales/en/<namespace>.json` contains canonical English source strings.
- `locales/<locale>/<namespace>.json` contains partial target translations.
- `game-client/<locale>.csv` contains stable `message_id,value` artifacts.

PaladinsCat pins a reviewed commit of this repository into each VPS frontend
deployment. Weblate holds translation drafts and reviewer state; no translation
credentials or approval queues belong in this repository or the frontend.
