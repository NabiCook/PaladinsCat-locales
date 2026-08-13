# Local Git fallback

Use this only when Weblate is unavailable or a maintainer explicitly requests a
repository edit.

1. Clone `https://github.com/PaladinsCat/PaladinsCat-locales.git` and branch from
   current `main`.
2. Edit only target-language values under `locales/<locale>` or approved
   `game-client/<locale>.csv` files. Do not add keys or alter placeholders.
3. Run `npm install` once, then `npm run validate`.
4. Commit only intended locale files, publish the branch, and open a pull
   request. Merge after required checks and reviewer approval pass.

The fallback has the same repository validation and release rules as Weblate.
