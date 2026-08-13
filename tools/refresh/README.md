# Maintainer locale-refresh tools

These repeatable import tools rebuild reviewed locale source material from game
client exports. They are not Weblate, build, CI, or production-operation
scripts. Run them only for a documented source refresh, review generated diffs,
then pass `npm run validate` and the normal pull-request workflow.
