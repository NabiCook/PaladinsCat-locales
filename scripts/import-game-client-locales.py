#!/usr/bin/env python3
"""Export native Paladins game-client localization data for PaladinsCat.

The game packages identify text with numeric ``message_id`` values.  Those IDs,
not the repeated human-readable keys, are the contract used when rebuilding a
language DAT.  This importer decodes the game DATs with the adjacent
PaladinsCat-Tempest GameDecoder and produces the reviewed two-column artifacts
used by this repository.

It intentionally imports the translations shipped by the client.  It does not
machine-translate, infer terms from English, or merge text across languages.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any


LOCALES: tuple[tuple[str, str, str], ...] = (
    ("INT", "en", "Lang_INT.dat"),
    ("DEU", "de", "Lang_DEU.dat"),
    ("ESL", "es-419", "Lang_ESL.dat"),
    ("FRA", "fr", "Lang_FRA.dat"),
    ("JPN", "ja", "Lang_JPN.dat"),
    # The maintained merged Korean DAT is intentionally not re-decodable. Its
    # verified decoded catalog is retained alongside it and has every stable ID.
    ("KOR", "ko", "Lang_KOR.csv"),
    ("POL", "pl", "Lang_POL.dat"),
    ("POR", "pt-BR", "Lang_POR.dat"),
    ("RUS", "ru", "Lang_RUS.dat"),
    ("TUR", "tr", "Lang_TUR.dat"),
    ("CHN", "zh-CN", "Lang_CHN.dat"),
    ("CHT", "zh-TW", "Lang_CHT.dat"),
)
MAX_VALUE_LENGTH = 8_000


def parse_args() -> argparse.Namespace:
    repository = Path(__file__).resolve().parents[1]
    sibling_root = repository.parent / "PaladinsCat-Tempest"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--localization-root",
        type=Path,
        default=sibling_root / "Localization",
        help="directory containing the game language folders",
    )
    parser.add_argument(
        "--decoder-root",
        type=Path,
        default=sibling_root / "Tools" / "GameDecoder",
        help="PaladinsCat-Tempest Tools/GameDecoder directory",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=repository / "game-client",
        help="directory that receives <locale>.csv and source-manifest.json",
    )
    return parser.parse_args()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def atomic_write_csv(path: Path, rows: list[tuple[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", newline="", delete=False, dir=path.parent
    ) as stream:
        temporary = Path(stream.name)
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(("message_id", "value"))
        writer.writerows(rows)
    os.replace(temporary, path)


def read_source_records(source: Path, decoder: Any) -> list[dict[str, Any]]:
    if source.suffix.lower() == ".dat":
        return decoder.decode_file(source)
    if source.suffix.lower() == ".csv":
        with source.open("r", encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            if reader.fieldnames is None or not {"message_id", "value"}.issubset(reader.fieldnames):
                raise SystemExit(f"{source}: source CSV must contain message_id and value columns")
            return list(reader)
    raise SystemExit(f"Unsupported game localization source: {source}")


def main() -> int:
    options = parse_args()
    localization_root = options.localization_root.resolve()
    decoder_root = options.decoder_root.resolve()
    output_root = options.output_root.resolve()
    if not localization_root.is_dir():
        raise SystemExit(f"Localization root does not exist: {localization_root}")
    if not decoder_root.is_dir():
        raise SystemExit(f"GameDecoder root does not exist: {decoder_root}")

    sys.path.insert(0, str(decoder_root))
    try:
        decoder = importlib.import_module("decode")
    except ImportError as error:
        raise SystemExit(f"Unable to load GameDecoder from {decoder_root}: {error}") from error

    prepared_packs: list[tuple[Path, list[tuple[str, str]], dict[str, Any]]] = []
    for game_code, locale, source_name in LOCALES:
        source = localization_root / game_code / source_name
        if not source.is_file():
            raise SystemExit(f"Missing game language package: {source}")

        records = read_source_records(source, decoder)
        rows: list[tuple[str, str]] = []
        seen_ids: set[str] = set()
        skipped_blank_values = 0
        for record in records:
            message_id = str(record.get("message_id", "")).strip()
            value = record.get("value")
            if not message_id.isdecimal() or not isinstance(value, str):
                raise SystemExit(f"{source}: invalid decoded record: {record!r}")
            if message_id in seen_ids:
                raise SystemExit(f"{source}: duplicate message_id {message_id}")
            seen_ids.add(message_id)
            if not value.strip():
                skipped_blank_values += 1
                continue
            if len(value) > MAX_VALUE_LENGTH or "\ufffd" in value:
                raise SystemExit(f"{source}: invalid value for message_id {message_id}")
            rows.append((message_id, value))

        prepared_packs.append(
            (
                output_root / f"{locale}.csv",
                rows,
                {
                    "locale": locale,
                    "gameCode": game_code,
                    "source": f"{game_code}/{source_name}",
                    "sourceFormat": source.suffix.removeprefix(".").lower(),
                    "sha256": sha256(source),
                    "sourceRecords": len(records),
                    "exportedRecords": len(rows),
                    "skippedBlankValues": skipped_blank_values,
                },
            )
        )

    # Decode and validate every source before changing any checked-in artifact.
    manifest_sources: list[dict[str, Any]] = []
    for target, rows, source_metadata in prepared_packs:
        atomic_write_csv(target, rows)
        manifest_sources.append(source_metadata)
        print(f"{source_metadata['gameCode']} -> {target.name}: {len(rows):,} strings")

    manifest = {
        "schemaVersion": 1,
        "description": "Native game-client strings exported by stable message_id.",
        "sources": manifest_sources,
    }
    manifest_path = output_root / "source-manifest.json"
    temporary_path = manifest_path.with_suffix(".json.tmp")
    temporary_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(temporary_path, manifest_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
