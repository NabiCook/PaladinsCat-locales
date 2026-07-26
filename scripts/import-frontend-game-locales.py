#!/usr/bin/env python3
"""Add verified native-game translations to frontend game locale modules.

The importer first requires a unique native English ``message_id``. It also
normalizes the client's card-only formatting (ability prefixes and ``scale``
placeholders), then uses conservative semantic and title-adjacent matches for
talent/loadout descriptions. The target value is always taken from that same
ID in the target language's client catalog. Ambiguous, missing, and
placeholder-incompatible values are intentionally left untranslated for human
review.
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
LEADING_ABILITY_PATTERN = re.compile(r"^\s*\[[^\]]+\]\s*")
SCALE_PLACEHOLDER_PATTERN = re.compile(r"\{scale=([^{}]+)\}", re.IGNORECASE)
WORD_PATTERN = re.compile(r"[a-z0-9]+")
FUZZY_STOP_WORDS = frozenset({
    "a", "an", "the", "your", "you", "of", "to", "by", "for", "with", "and", "or", "in", "on",
    "at", "from", "is", "are", "be", "as", "it", "this", "that", "after", "while", "when", "up",
    "all", "each", "every", "their", "them", "they", "its", "into", "no", "now",
})


def parse_args() -> argparse.Namespace:
    repository = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game-client-root", type=Path, default=repository / "game-client")
    parser.add_argument("--locales-root", type=Path, default=repository / "locales")
    parser.add_argument("--force", action="store_true", help="replace existing verified native values")
    parser.add_argument("--locales", default=",".join(TARGET_LOCALES), help="comma-separated BCP 47 tags")
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


def normalize_game_value(value: str) -> str:
    """Align client card formatting with the compact web description format."""
    value = LEADING_ABILITY_PATTERN.sub("", value)
    value = SCALE_PLACEHOLDER_PATTERN.sub(r"{\1}", value)
    return re.sub(r"\s+", " ", value).strip()


def content_tokens(value: str) -> set[str]:
    return {
        token for token in WORD_PATTERN.findall(normalize_game_value(value).casefold())
        if token not in FUZZY_STOP_WORDS
    }


def title_token(value: str) -> str:
    return "".join(WORD_PATTERN.findall(value.casefold()))


def build_semantic_index(values_by_id: dict[str, str]) -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    tokens_by_id: dict[str, set[str]] = {}
    ids_by_token: dict[str, set[str]] = defaultdict(set)
    for message_id, value in values_by_id.items():
        tokens = content_tokens(value)
        tokens_by_id[message_id] = tokens
        for token in tokens:
            ids_by_token[token].add(message_id)
    return tokens_by_id, ids_by_token


def build_title_index(values_by_id: dict[str, str]) -> dict[str, list[str]]:
    titles: dict[str, list[str]] = defaultdict(list)
    for message_id, value in values_by_id.items():
        token = title_token(value)
        if token:
            titles[token].append(message_id)
    return titles


def descriptions_are_compatible(source_value: str, candidate_value: str) -> bool:
    if normalize_game_value(source_value).casefold() == normalize_game_value(candidate_value).casefold():
        return True
    source_tokens = content_tokens(source_value)
    candidate_tokens = content_tokens(candidate_value)
    smaller, larger = (
        (candidate_tokens, source_tokens)
        if len(candidate_tokens) <= len(source_tokens)
        else (source_tokens, candidate_tokens)
    )
    return len(smaller) >= 5 and smaller <= larger and len(larger) - len(smaller) <= 10


def title_adjacent_match(
    key: str,
    source_value: str,
    values_by_id: dict[str, str],
    title_index: dict[str, list[str]],
) -> str | None:
    """Resolve duplicate generic card text through its unique client title."""
    card_or_talent = key.split(".")[-2]
    title_ids = title_index.get(title_token(card_or_talent), [])
    candidates: list[str] = []
    for title_id in title_ids:
        try:
            description_id = str(int(title_id) + 1)
        except ValueError:
            continue
        description = values_by_id.get(description_id)
        if description and descriptions_are_compatible(source_value, description):
            candidates.append(description_id)
    if len(candidates) == 1:
        return candidates[0]
    # The canonical title is a stronger identity than a stale web description.
    # Use its adjacent client description only when the title itself is unique;
    # duplicate names still require compatible text above.
    if len(title_ids) == 1:
        try:
            adjacent_id = str(int(title_ids[0]) + 1)
        except ValueError:
            return None
        return adjacent_id if adjacent_id in values_by_id else None
    return None


def unique_semantic_match(
    source_value: str,
    tokens_by_id: dict[str, set[str]],
    ids_by_token: dict[str, set[str]],
) -> str | None:
    """Return one safe short/long-description match, otherwise no match."""
    source_tokens = content_tokens(source_value)
    if len(source_tokens) < 5:
        return None
    seed_tokens = sorted(source_tokens, key=lambda token: len(ids_by_token[token]))[:3]
    candidate_ids = set.intersection(*(ids_by_token[token] for token in seed_tokens))
    matches: list[str] = []
    for message_id in candidate_ids:
        candidate_tokens = tokens_by_id[message_id]
        smaller, larger = (
            (candidate_tokens, source_tokens)
            if len(candidate_tokens) <= len(source_tokens)
            else (source_tokens, candidate_tokens)
        )
        if len(smaller) >= 5 and smaller <= larger and len(larger) - len(smaller) <= 10:
            matches.append(message_id)
    return matches[0] if len(matches) == 1 else None


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
    english_values_to_ids, english_values_by_id = read_catalog(game_client_root / "en.csv")
    normalized_english_values_to_ids: dict[str, list[str]] = defaultdict(list)
    for message_id, value in english_values_by_id.items():
        normalized_english_values_to_ids[normalize_game_value(value)].append(message_id)
    semantic_tokens_by_id, semantic_ids_by_token = build_semantic_index(english_values_by_id)
    english_title_index = build_title_index(english_values_by_id)
    requested = tuple(locale.strip() for locale in options.locales.split(",") if locale.strip())
    invalid = set(requested) - set(TARGET_LOCALES)
    if invalid:
        raise SystemExit(f"Unsupported locale(s): {', '.join(sorted(invalid))}")
    manifest: dict[str, object] = {
        "schemaVersion": 1,
        "matching": "unique exact, normalized card format, or conservative talent/card semantic match",
        "locales": {},
    }

    for locale in requested:
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

            exact_matches = normalized_matches = semantic_matches = title_matches = added = refreshed = skipped_existing = 0
            for key, english_value in source.items():
                message_ids = english_values_to_ids.get(english_value, [])
                match_kind = "exact"
                if len(message_ids) != 1:
                    message_ids = normalized_english_values_to_ids.get(normalize_game_value(english_value), [])
                    match_kind = "normalized"
                if len(message_ids) != 1 and module == "game/champions" and (
                    ".talents." in key or ".loadouts." in key
                ) and key.endswith(".description"):
                    semantic_id = unique_semantic_match(english_value, semantic_tokens_by_id, semantic_ids_by_token)
                    message_ids = [semantic_id] if semantic_id else []
                    match_kind = "semantic"
                if len(message_ids) != 1 and module == "game/champions" and (
                    ".talents." in key or ".loadouts." in key
                ) and key.endswith(".description"):
                    title_id = title_adjacent_match(key, english_value, english_values_by_id, english_title_index)
                    message_ids = [title_id] if title_id else []
                    match_kind = "title-adjacent"
                if len(message_ids) != 1:
                    continue
                native_value = target_values_by_id.get(message_ids[0])
                if native_value is None:
                    continue
                native_value = normalize_game_value(native_value)
                if placeholders(native_value) != placeholders(english_value):
                    continue
                if match_kind == "exact":
                    exact_matches += 1
                elif match_kind == "normalized":
                    normalized_matches += 1
                elif match_kind == "semantic":
                    semantic_matches += 1
                else:
                    title_matches += 1
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
                "exactNativeMatches": exact_matches,
                "normalizedNativeMatches": normalized_matches,
                "semanticNativeMatches": semantic_matches,
                "titleAdjacentNativeMatches": title_matches,
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
