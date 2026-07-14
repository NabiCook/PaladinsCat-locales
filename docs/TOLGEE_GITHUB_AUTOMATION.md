# Automated Tolgee web UI to GitHub pull request

Tolgee does not currently provide a documented built-in GitHub pull-request
connector. This repository implements that behavior without the PaladinsCat
API or VPS: a scheduled GitHub Action pulls translated values through the
official Tolgee CLI, validates them, and creates or updates one pull request.

## Requirements

The Tolgee API URL must be reachable from a GitHub-hosted runner. Use Tolgee
Cloud or a separately secured, Internet-reachable Tolgee installation. A
Tolgee instance bound only to `127.0.0.1` cannot use this automation; use the
GitHub Desktop workflow instead.

## Repository configuration

In `PaladinsCat-locales` open **Settings → Secrets and variables → Actions**.
Add these repository variables:

- `TOLGEE_API_URL`: the Tolgee base URL, for example `https://app.tolgee.io`;
- `TOLGEE_PROJECT_ID`: the numeric project ID from its Tolgee URL;
- `TOLGEE_TARGET_LOCALES`: comma- or space-separated locale tags to export,
  for example `ko,fr,pt-BR`.

Add these repository secrets:

- `TOLGEE_API_KEY`: a project key allowed to view keys and translations;
- `LOCALES_PR_TOKEN`: a fine-grained GitHub personal access token restricted
  to this repository with **Contents: Read and write** and
  **Pull requests: Read and write**.

The dedicated token is intentional. Pull requests created with the repository
`GITHUB_TOKEN` do not trigger the separate pull-request validation workflow.
Store neither token in Tolgee, a locale file, the PaladinsCat repository, nor
the VPS.

## Operation

The `Export Tolgee translations to a pull request` workflow runs every 15
minutes. It exports only the configured target locales and only translations
in `TRANSLATED` or `REVIEWED` state. If files changed, it force-refreshes the
automation-owned `automation/tolgee-export` branch and opens or updates its
pull request.

To run immediately, open **Actions → Export Tolgee translations to a pull
request → Run workflow**. Do not commit manually to the automation branch.

After the validation check passes, review the wording and merge. That merge is
the sole translation approval; no PaladinsCat submission or admin approval is
performed.

## English source updates

The automation pulls target languages only. When application English keys
change, a maintainer runs `npm run tolgee:push` from a current repository clone
to update the Tolgee base language. The key stays in a local environment
variable and is never committed.
