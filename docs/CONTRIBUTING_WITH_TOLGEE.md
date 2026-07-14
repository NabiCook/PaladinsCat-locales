# Local Tolgee to GitHub Desktop fallback

The shared Tolgee project normally exports directly to a GitHub pull request
through the scheduled repository workflow. See
[TOLGEE_GITHUB_AUTOMATION.md](TOLGEE_GITHUB_AUTOMATION.md).

Use this fallback when Tolgee runs only on your computer or when you want to
control the exported files locally. GitHub pull requests remain the single
review and approval gate; PaladinsCat does not receive or store drafts.

## 1. Clone and branch

Clone `https://github.com/NabiCook/PaladinsCat-locales.git` with GitHub Desktop,
then create a branch such as `l10n/ko-navigation` from the latest `main`.

Do not discard unrelated uncommitted preview or review files. GitHub Desktop
lets you select only the intended locale files for a commit.

## 2. Start Tolgee

Follow [SELF_HOSTED_TOLGEE.md](SELF_HOSTED_TOLGEE.md), create a website project
with English as its base language, enable namespaces, and add the target
language. Create a project API key with permission to view keys/translations
and edit translations.

The project ID is the number in the Tolgee project URL.

## 3. Configure the current shell

```powershell
$env:TOLGEE_API_URL = "http://127.0.0.1:8080"
$env:TOLGEE_PROJECT_ID = "6"
$env:TOLGEE_TARGET_LOCALE = "ko"
$env:TOLGEE_API_KEY = "tgpak_..."
npm install
```

These values are local credentials and must not be committed. Each contributor
may use a different Tolgee project ID and target language.

## 4. Import the canonical English source

```powershell
npm run tolgee:push
```

The checked-in `tolgee.config.cjs` maps files like
`locales/en/ui/navigation.json` to the `ui/navigation` namespace. English is
overridden from Git because Git is authoritative; target languages are not
pushed by this command.

Import any already-approved target files through Tolgee's Import screen when
initializing a new project so a later export does not omit them.

## 5. Translate in Tolgee

Use Tolgee's translation state, search, translation memory, and batch tools.
Only non-empty values in `TRANSLATED` or `REVIEWED` state are exported by the
repository configuration.

## 6. Export to the working tree

```powershell
npm run tolgee:export
```

This runs Tolgee CLI `pull`, writes the selected language directly under
`locales/<language>/<namespace>.json`, and validates the repository. Review the
diff in GitHub Desktop before committing.

## 7. Create the pull request

In GitHub Desktop:

1. select only the intended locale files;
2. commit them to the translation branch;
3. publish the branch;
4. choose **Create Pull Request**;
5. merge after GitHub Actions passes and the wording looks correct.

The PaladinsCat application repository pins merged locale commits for VPS
deployments. There is no separate PaladinsCat approval step.

## Updating source strings

Pull the latest locale-repository `main`, rerun `npm run tolgee:push`, and review
Tolgee's changed source strings before continuing. If your Git branch is stale,
update it from `main` before opening or merging the pull request.
