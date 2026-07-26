#!/usr/bin/env python3
"""Direct-translate non-game frontend copy while preserving native game terms.

Game modules are intentionally excluded: their descriptions come only from the
official client catalog through import-frontend-game-locales.py. Korean is also
excluded so its existing reviewed locale remains untouched.
"""

from __future__ import annotations

import argparse
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path


TARGET_LOCALES = ("de", "es-419", "fr", "ja", "pl", "pt-BR", "ru", "tr", "zh-CN", "zh-TW")
LOCALE_TO_GOOGLE = {"es-419": "es", "pt-BR": "pt", "zh-CN": "zh-CN", "zh-TW": "zh-TW"}
PLACEHOLDER_PATTERN = re.compile(r"@@[A-Za-z0-9_]+@@|\{[A-Za-z0-9_]+\}|%(?:\d+\$)?[sdif]")
TOKEN_PATTERN = re.compile(r"xq(?:ph|term|abbr|brand|nl)\d*x", re.IGNORECASE)
MAX_BATCH_CHARACTERS = 3_500
# These are the site's game-stat abbreviations, not prose to be translated.
# Protect them before sending a sentence to a machine translator: otherwise PR
# becomes public relations and DPM/HPM can be interpreted as unrelated fields.
PROTECTED_METRIC_TOKENS = (
    "AFK", "APM", "BR", "CD", "CPM", "DMG", "DPM", "eCPM", "EGPM", "ELO",
    "HPM", "K/D/A", "KDA", "KBM", "MPM", "P10", "P25", "P75", "P90", "PR",
    "SHPM", "SPM", "TP", "WPM", "WR", "XP",
)
METRIC_PATTERN = re.compile(
    r"(?<![A-Za-z0-9])(" + "|".join(re.escape(token) for token in PROTECTED_METRIC_TOKENS) + r")(?![A-Za-z0-9])",
)
BRAND_PATTERN = re.compile(r"PaladinsCat", re.IGNORECASE)
BRAND_KEY_OVERRIDES = {
    "home.brandLead": "Paladins",
    "home.brandAccent": "Cat",
}


def parse_args() -> argparse.Namespace:
    repository = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--locales-root", type=Path, default=repository / "locales")
    parser.add_argument("--glossary", type=Path, default=repository / "game-client" / "term-glossary.json")
    parser.add_argument("--locales", default=",".join(TARGET_LOCALES), help="comma-separated BCP 47 tags")
    parser.add_argument(
        "--metrics-only",
        action="store_true",
        help="translate only values containing protected game-stat abbreviations",
    )
    return parser.parse_args()


def translate_batch(texts: list[str], target_language: str) -> list[str]:
    joined = "\n".join(texts)
    query = urllib.parse.urlencode({"client": "gtx", "sl": "en", "tl": target_language, "dt": "t", "q": joined})
    request = urllib.request.Request(
        f"https://translate.googleapis.com/translate_a/single?{query}",
        headers={"User-Agent": "PaladinsCat localization importer"},
    )
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                payload = json.loads(response.read().decode("utf-8"))
            translated = "".join(part[0] for part in payload[0])
            rows = translated.split("\n")
            if len(rows) != len(texts):
                raise ValueError(f"translation batch returned {len(rows)} rows for {len(texts)} source rows")
            return rows
        except Exception as error:  # network errors are retried, then reported without writing a partial module
            last_error = error
            time.sleep(attempt + 1)
    raise RuntimeError(f"Direct translation failed for {target_language}: {last_error}")


def atomic_write_json(path: Path, contents: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(contents, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def protector(glossary: dict[str, object], locale: str):
    translations = {
        term: entry["translations"][locale]
        for term, entry in glossary["terms"].items()
        if locale in entry["translations"]
    }
    ordered_terms = sorted(translations, key=len, reverse=True)
    term_pattern = re.compile(
        r"(?<![A-Za-z0-9])(" + "|".join(re.escape(term) for term in ordered_terms) + r")(?![A-Za-z0-9])",
        re.IGNORECASE,
    )

    def protect(value: str) -> tuple[str, dict[str, str]]:
        tokens: dict[str, str] = {}
        counter = 0

        def placeholder(match: re.Match[str]) -> str:
            nonlocal counter
            token = f"xqph{counter}x"
            counter += 1
            tokens[token] = match.group(0)
            return token

        protected = PLACEHOLDER_PATTERN.sub(placeholder, value)

        def metric(match: re.Match[str]) -> str:
            nonlocal counter
            token = f"xqabbr{counter}x"
            counter += 1
            tokens[token] = match.group(0)
            return token

        protected = METRIC_PATTERN.sub(metric, protected)

        def brand(match: re.Match[str]) -> str:
            nonlocal counter
            token = f"xqbrand{counter}x"
            counter += 1
            tokens[token] = "PaladinsCat"
            return token

        protected = BRAND_PATTERN.sub(brand, protected)

        # Normalize dictionary lookup while retaining case-insensitive matching.
        normalized = {term.casefold(): translated for term, translated in translations.items()}
        def normalized_game_term(match: re.Match[str]) -> str:
            nonlocal counter
            token = f"xqterm{counter}x"
            counter += 1
            tokens[token] = normalized[match.group(0).casefold()]
            return token

        protected = term_pattern.sub(normalized_game_term, protected)
        if "\n" in protected:
            token = f"xqnl{counter}x"
            tokens[token] = "\n"
            protected = protected.replace("\n", token)
        return protected, tokens

    return protect


def restore(value: str, tokens: dict[str, str], locale: str, native_terms: tuple[str, ...]) -> str:
    for token, original in tokens.items():
        value = re.sub(re.escape(token), lambda _: original, value, flags=re.IGNORECASE)
    if TOKEN_PATTERN.search(value):
        raise ValueError(f"translation left a protected token behind: {value!r}")
    # Google occasionally joins an all-caps official Spanish term to the word
    # before it (for example, "metaBARAJA"). Restore the word boundary that was
    # present in the English source without changing normal Spanish punctuation.
    if locale == "es-419" and native_terms:
        terms = "|".join(re.escape(term) for term in sorted(native_terms, key=len, reverse=True))
        value = re.sub(rf"(?<=[a-záéíóúñ])(?=(?:{terms}))", " ", value)
    return value


def checked_restore(
    source_value: str,
    translated_value: str,
    tokens: dict[str, str],
    locale: str,
    native_terms: tuple[str, ...],
) -> str:
    restored = restore(translated_value, tokens, locale, native_terms)
    if sorted(PLACEHOLDER_PATTERN.findall(restored)) != sorted(PLACEHOLDER_PATTERN.findall(source_value)):
        # A structurally safe English fallback is preferable to a translated
        # value that loses a runtime placeholder.
        return source_value
    return restored


def main() -> int:
    options = parse_args()
    locales_root = options.locales_root.resolve()
    glossary = json.loads(options.glossary.read_text(encoding="utf-8"))
    requested = tuple(locale.strip() for locale in options.locales.split(",") if locale.strip())
    invalid = set(requested) - set(TARGET_LOCALES)
    if invalid:
        raise SystemExit(f"Unsupported or protected locale(s): {', '.join(sorted(invalid))}")

    modules = json.loads((locales_root / "modules.json").read_text(encoding="utf-8"))
    general_modules = [module for module in modules if not module.startswith("game/")]
    for locale in requested:
        protect = protector(glossary, locale)
        native_terms = tuple(
            entry["translations"][locale]
            for entry in glossary["terms"].values()
            if locale in entry["translations"]
        )
        google_locale = LOCALE_TO_GOOGLE.get(locale, locale)
        for module in general_modules:
            source_path = locales_root / "en" / f"{module}.json"
            source = json.loads(source_path.read_text(encoding="utf-8"))
            source_items = (
                ((key, value) for key, value in source.items() if METRIC_PATTERN.search(value))
                if options.metrics_only
                else source.items()
            )
            source_items = (
                (key, BRAND_KEY_OVERRIDES.get(key, value))
                for key, value in source_items
            )
            prepared: list[tuple[str, str, dict[str, str]]] = [
                (key, *protect(value)) for key, value in source_items
            ]
            translated_by_key: dict[str, str] = {}
            batch: list[tuple[str, str, dict[str, str]]] = []
            batch_length = 0
            for entry in prepared:
                if batch and batch_length + len(entry[1]) + 1 > MAX_BATCH_CHARACTERS:
                    translated = translate_batch([item[1] for item in batch], google_locale)
                    translated_by_key.update({
                        item[0]: checked_restore(source[item[0]], value, item[2], locale, native_terms)
                        for item, value in zip(batch, translated)
                    })
                    batch, batch_length = [], 0
                batch.append(entry)
                batch_length += len(entry[1]) + 1
            if batch:
                translated = translate_batch([item[1] for item in batch], google_locale)
                translated_by_key.update({
                    item[0]: checked_restore(source[item[0]], value, item[2], locale, native_terms)
                    for item, value in zip(batch, translated)
                })

            target_path = locales_root / locale / f"{module}.json"
            existing = json.loads(target_path.read_text(encoding="utf-8")) if target_path.is_file() else {}
            existing.update(translated_by_key)
            atomic_write_json(target_path, dict(sorted(existing.items())))
            print(f"{locale} {module}: {len(translated_by_key)} direct translations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
