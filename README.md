# PaladinsCat community translations

This public repository is the source of truth for PaladinsCat translations.
Translation changes are made on a Git branch, validated by GitHub Actions, and
reviewed once as a normal pull request.

## Contribute

The primary workflow is entirely web based: edit translations in Tolgee, then
the scheduled GitHub workflow exports `TRANSLATED` and `REVIEWED` values into a
pull request. Merging that pull request is the only translation approval.

For a local-only Tolgee instance or a small direct edit, clone this repository,
export into the working tree, and create the pull request with GitHub Desktop.

- [Contribution rules](CONTRIBUTING.md)
- [Tolgee and GitHub Desktop workflow](docs/CONTRIBUTING_WITH_TOLGEE.md)
- [Automated Tolgee pull requests](docs/TOLGEE_GITHUB_AUTOMATION.md)
- [Local Tolgee Docker setup](docs/SELF_HOSTED_TOLGEE.md)

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
deployment. No translation drafts, API tokens, or approval queues are stored on
the PaladinsCat server.
