#!/usr/bin/env python3
"""Build a curated, native-game terminology glossary for frontend translation.

This is deliberately a keyword source, not a bulk UI translator. It chooses an
English game term only when an exact English catalog entry has native values in
one or more game languages. General frontend prose should still be translated
normally, with this glossary applied to game-specific terminology.
"""

from __future__ import annotations

import csv
import json
import os
import tempfile
from pathlib import Path


TARGET_LOCALES = ("de", "es-419", "fr", "ja", "ko", "pl", "pt-BR", "ru", "tr", "zh-CN", "zh-TW")
TERMS = (
    "Champion", "Champions", "Ability", "Abilities", "Loadout", "Loadouts",
    "Card", "Cards", "Item", "Items", "Map", "Maps", "Ranked", "Casual",
    "Practice", "Siege", "Onslaught", "Team Deathmatch", "Payload", "Credits",
    "Crystals", "Gold", "Experience", "XP", "Level", "Levels", "Skin", "Skins",
    "Emote", "Spray", "Mount", "Avatar", "Title", "Party", "Friends", "Clan",
    "Battle Pass", "Challenge", "Challenges", "Quest", "Quests", "Reward", "Rewards",
    "Victory", "Defeat", "Damage", "Healing", "Elimination", "Eliminations", "Kill",
    "Kills", "Death", "Deaths", "Assist", "Assists", "Cooldown", "Ultimate", "Flank",
    "Front Line", "Support", "Player", "Players", "Profile", "Settings", "Store",
)


def read_catalog(path: Path) -> tuple[list[dict[str, str]], dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != ["message_id", "value"]:
            raise SystemExit(f"{path}: expected message_id,value header")
        rows = list(reader)
    values_by_id = {row["message_id"]: row["value"] for row in rows}
    if len(values_by_id) != len(rows):
        raise SystemExit(f"{path}: duplicate message_id")
    return rows, values_by_id


def atomic_write_json(path: Path, contents: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False, dir=path.parent) as stream:
        temporary = Path(stream.name)
        json.dump(contents, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    os.replace(temporary, path)


def main() -> int:
    repository = Path(__file__).resolve().parents[1]
    game_client = repository / "game-client"
    english_rows, _ = read_catalog(game_client / "en.csv")
    target_catalogs = {locale: read_catalog(game_client / f"{locale}.csv")[1] for locale in TARGET_LOCALES}
    terms: dict[str, object] = {}

    for term in TERMS:
        candidates = [row for row in english_rows if row["value"].casefold() == term.casefold()]
        if not candidates:
            continue
        # Prefer the game entry that has the broadest native-language coverage.
        selected = max(
            candidates,
            key=lambda row: (
                sum(row["message_id"] in catalog for catalog in target_catalogs.values()),
                -int(row["message_id"]),
            ),
        )
        message_id = selected["message_id"]
        translations = {
            locale: catalog[message_id]
            for locale, catalog in target_catalogs.items()
            if message_id in catalog
        }
        if translations:
            terms[term] = {
                "messageId": message_id,
                "translations": translations,
                "missingLocales": [locale for locale in TARGET_LOCALES if locale not in translations],
            }

    atomic_write_json(
        game_client / "term-glossary.json",
        {
            "schemaVersion": 1,
            "strategy": "Use native translations for listed game terms; translate general prose normally.",
            "source": "game-client/en.csv matched by exact English value and stable message_id",
            "terms": terms,
        },
    )
    print(f"Wrote {len(terms)} verified game terms to term-glossary.json.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
