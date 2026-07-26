#!/usr/bin/env python3
"""Add verified native-game translations to frontend game locale modules.

Only a frontend English value that maps to exactly one native English
``message_id`` is eligible. The target value is then taken from the same ID in
the target language's client catalog. Ambiguous, missing, and placeholder
incompatible values are intentionally left untranslated for human review.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import tempfile
from collections import defaultdict
from pathlib import Path


TARGET_LOCALES = ("de", "es-419", "fr", "ja", "ko", "pl", "pt-BR", "ru", "tr", "zh-CN", "zh-TW")
GAME_MODULES = ("game/champions", "game/talents", "game/items", "game/maps")
PLACEHOLDER_PATTERN = re.compile(r"@@[A-Za-z0-9_]+@@|\{[A-Za-z0-9_]+\}|%(?:\d+\$)?[sdif]")


def parse_args() -> argparse.Namespace:
    repository = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game-client-root", type=Path, default=repository / "game-client")
    parser.add_argument("--locales-root", type=Path, default=repository / "locales")
    parser.add_argument("--force", action="store_true", help="replace existing verified native values")
    return parser.parse_args()


def read_catalog(path: Path) -> tuple[dict[str, list[str]], dict[str, str]]:
    values_to_ids: dict[str, list[str]] = defaultdict(list)
    values_by_id: dict[str, str] = {}
    with path.open("r", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != ["message_id", "value"]:
            raise SystemExit(f"{path}: expected message_id,value header")
        for row in reader:
            message_id = row["message_id"]
            value = row["value"]
            if not message_id.isdecimal() or not value.strip() or message_id in values_by_id:
                raise SystemExit(f"{path}: invalid or duplicate source row")
            values_to_ids[value].append(message_id)
            values_by_id[message_id] = value
    return values_to_ids, values_by_id


def placeholders(value: str) -> list[str]:
    return sorted(match.group(0) for match in PLACEHOLDER_PATTERN.finditer(value))


def atomic_write_json(path: Path, contents: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False, dir=path.parent) as stream:
        temporary = Path(stream.name)
        json.dump(contents, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    os.replace(temporary, path)


def main() -> int:
    options = parse_args()
    game_client_root = options.game_client_root.resolve()
    locales_root = options.locales_root.resolve()
    english_values_to_ids, _ = read_catalog(game_client_root / "en.csv")
    manifest: dict[str, object] = {
        "schemaVersion": 1,
        "matching": "exact English value + unique message_id",
        "locales": {},
    }

    for locale in TARGET_LOCALES:
        _, target_values_by_id = read_catalog(game_client_root / f"{locale}.csv")
        locale_stats: dict[str, dict[str, int]] = {}
        for module in GAME_MODULES:
            source_path = locales_root / "en" / f"{module}.json"
            source = json.loads(source_path.read_text(encoding="utf-8"))
            if not isinstance(source, dict) or not all(isinstance(key, str) and isinstance(value, str) for key, value in source.items()):
                raise SystemExit(f"{source_path}: expected a string-to-string object")

            target_path = locales_root / locale / f"{module}.json"
            target = json.loads(target_path.read_text(encoding="utf-8")) if target_path.is_file() else {}
            if not isinstance(target, dict) or not all(isinstance(key, str) and isinstance(value, str) for key, value in target.items()):
                raise SystemExit(f"{target_path}: expected a string-to-string object")

            unique_matches = added = refreshed = skipped_existing = 0
            for key, english_value in source.items():
                message_ids = english_values_to_ids.get(english_value, [])
                if len(message_ids) != 1:
                    continue
                native_value = target_values_by_id.get(message_ids[0])
                if native_value is None or placeholders(native_value) != placeholders(english_value):
                    continue
                unique_matches += 1
                if key in target and not options.force:
                    skipped_existing += 1
                    continue
                if target.get(key) == native_value:
                    continue
                if key in target:
                    refreshed += 1
                else:
                    added += 1
                target[key] = native_value

            if added or refreshed:
                atomic_write_json(target_path, dict(sorted(target.items())))
            locale_stats[module] = {
                "uniqueNativeMatches": unique_matches,
                "added": added,
                "refreshed": refreshed,
                "preservedExisting": skipped_existing,
            }
            print(f"{locale} {module}: {added} added, {refreshed} refreshed, {skipped_existing} preserved")
        manifest["locales"][locale] = locale_stats

    atomic_write_json(game_client_root / "frontend-game-match-manifest.json", manifest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
