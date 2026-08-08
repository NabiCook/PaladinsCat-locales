# PaladinsCat community translations

This public repository is the source of truth for PaladinsCat translations.
Translation changes are made on a Git branch, validated by GitHub Actions, and
reviewed once as a normal pull request.

## Contribute

Translate in the [PaladinsCat Weblate project](https://translate.paladinscat.com).
Approved translations are
synchronized to a Weblate-owned GitHub pull request; merge it only after the
repository validation and review pass. GitHub `main` remains authoritative.
Direct local Git editing remains available as a fallback.

- [Contribution rules](CONTRIBUTING.md)
- [Weblate and GitHub workflow](docs/WEBLATE_GITHUB_WORKFLOW.md)
- [Local Git fallback](docs/LOCAL_GIT_FALLBACK.md)

Run the same mechanical checks used by pull requests before committing:

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
