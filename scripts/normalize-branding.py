#!/usr/bin/env python3
"""Keep PaladinsCat's wordmark and standalone labels identical in every locale."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path


TARGET_LOCALES = ("de", "es-419", "fr", "ja", "pl", "pt-BR", "ru", "tr", "zh-CN", "zh-TW")
LOGO_OVERRIDES = {"home.brandLead": "Paladins", "home.brandAccent": "Cat"}


def write_json(path: Path, contents: dict[str, str]) -> None:
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False, dir=path.parent) as stream:
        temporary = Path(stream.name)
        json.dump(contents, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    os.replace(temporary, path)


def main() -> int:
    repository = Path(__file__).resolve().parents[1]
    locales_root = repository / "locales"
    modules = json.loads((locales_root / "modules.json").read_text(encoding="utf-8"))
    changes = 0

    for locale in TARGET_LOCALES:
        for module in modules:
            source_path = locales_root / "en" / f"{module}.json"
            target_path = locales_root / locale / f"{module}.json"
            if not target_path.is_file():
                continue
            source = json.loads(source_path.read_text(encoding="utf-8"))
            target = json.loads(target_path.read_text(encoding="utf-8"))
            changed = False
            for key, value in source.items():
                replacement = LOGO_OVERRIDES.get(key)
                if replacement is None and value in {"PaladinsCat", "PaladinsCat ©"}:
                    replacement = value
                if replacement is not None and target.get(key) != replacement:
                    target[key] = replacement
                    changes += 1
                    changed = True
            if changed:
                write_json(target_path, dict(sorted(target.items())))
    print(f"Normalized {changes} PaladinsCat brand value(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
