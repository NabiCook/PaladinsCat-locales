# PaladinsCat community translations

This public repository is the source of truth for PaladinsCat translations.
Translation changes are made on a Git branch, validated by GitHub Actions, and
reviewed once as a normal pull request.

## Contribute

Edit translations in Tolgee, export `TRANSLATED` and `REVIEWED` values to a Git
branch, and merge one GitHub pull request. For the current local-only Tolgee
instance, a guarded local agent performs the export and GitHub Desktop (or Git)
publishes the branch. A scheduled GitHub-hosted export is available only when
Tolgee is deployed at an Internet-reachable URL and explicitly enabled.

- [Contribution rules](CONTRIBUTING.md)
- [Tolgee and GitHub Desktop workflow](docs/CONTRIBUTING_WITH_TOLGEE.md)
- [Local-agent Tolgee setup](docs/LOCAL_AGENT_TOLGEE.md)
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
