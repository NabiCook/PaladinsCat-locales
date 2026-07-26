#!/usr/bin/env python3
"""Repair unsafe game-locale descriptions without machine-translating them.

If a localized game string no longer has the same card-scale placeholders as
the English frontend source, it cannot be rendered reliably. Use the exact
English source as the safe fallback: this preserves the game description and
all runtime values until a verified native client translation is available.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import tempfile
from pathlib import Path


GAME_MODULES = ("game/champions", "game/talents", "game/items", "game/maps")
CARD_PLACEHOLDER_PATTERN = re.compile(r"\{[^{}]+\}")
# Proper nouns such as "Jump to Float" are valid in native Korean game copy.
# Two or more of these English function words alongside Hangul, however, is a
# reliable signal of a partially machine-translated sentence rather than a
# preserved game name.
ENGLISH_FUNCTION_WORD_PATTERN = re.compile(
    r"\b(?:a|an|the|your|you|to|of|with|after|while|when|for|from|and|or|by|"
    r"is|are|gain|increase|reduce|apply|deals|damage|speed|health|cooldown|"
    r"range|radius|enemies|enemy|using|allies|they|their|inside|that|this|"
    r"these|in|on|at|as|into|over|under|up|out)\b",
    re.IGNORECASE,
)


def parse_args() -> argparse.Namespace:
    repository = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--locales-root", type=Path, default=repository / "locales")
    parser.add_argument("--locale", default="ko")
    parser.add_argument(
        "--english-fallback-for-corrupted-korean",
        action="store_true",
        help="replace clearly mixed Korean/English game descriptions with their exact English source",
    )
    return parser.parse_args()


def placeholders(value: str) -> list[str]:
    return sorted(match.group(0) for match in CARD_PLACEHOLDER_PATTERN.finditer(value))


def is_corrupted_korean_description(value: str) -> bool:
    has_hangul = any("가" <= character <= "힣" for character in value)
    return has_hangul and len(ENGLISH_FUNCTION_WORD_PATTERN.findall(value)) >= 2


def atomic_write_json(path: Path, contents: dict[str, str]) -> None:
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False, dir=path.parent) as stream:
        temporary = Path(stream.name)
        json.dump(contents, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    os.replace(temporary, path)


def main() -> int:
    options = parse_args()
    locales_root = options.locales_root.resolve()
    repaired = 0
    corrupted_korean_fallbacks = 0
    for module in GAME_MODULES:
        source_path = locales_root / "en" / f"{module}.json"
        target_path = locales_root / options.locale / f"{module}.json"
        source = json.loads(source_path.read_text(encoding="utf-8"))
        target = json.loads(target_path.read_text(encoding="utf-8"))
        missing = set(source) - set(target)
        extra = set(target) - set(source)
        if missing or extra:
            raise SystemExit(f"{target_path}: key parity failed ({len(missing)} missing, {len(extra)} extra)")

        module_repairs = 0
        module_corrupted_fallbacks = 0
        for key, source_value in source.items():
            if placeholders(source_value) != placeholders(target[key]):
                target[key] = source_value
                module_repairs += 1
            elif (
                options.english_fallback_for_corrupted_korean
                and key.endswith(".description")
                and is_corrupted_korean_description(target[key])
            ):
                target[key] = source_value
                module_corrupted_fallbacks += 1
        if module_repairs or module_corrupted_fallbacks:
            atomic_write_json(target_path, dict(sorted(target.items())))
        repaired += module_repairs
        corrupted_korean_fallbacks += module_corrupted_fallbacks
        print(f"{options.locale} {module}: {module_repairs} placeholder-safe English fallbacks")
        if options.english_fallback_for_corrupted_korean:
            print(f"{options.locale} {module}: {module_corrupted_fallbacks} corrupted-Korean English fallbacks")
    print(f"Repaired {repaired} unsafe game-locale values and {corrupted_korean_fallbacks} corrupted Korean descriptions.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
