#!/usr/bin/env python3
"""Export ASR hot words from the skill correction dictionary."""

from __future__ import annotations

import argparse
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent


def parse_scalar(value: str) -> str:
    value = value.strip()
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    if value.startswith("'") and value.endswith("'"):
        return value[1:-1]
    return value


def load_hotwords(path: Path, include_sources: bool) -> list[str]:
    words: list[str] = []
    current_from: str | None = None
    in_preferred_terms = False

    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue

        if line.startswith("preferred_terms:"):
            in_preferred_terms = True
            current_from = None
            continue
        if in_preferred_terms and raw and not raw.startswith(" "):
            in_preferred_terms = False

        if line.startswith("- from:"):
            current_from = parse_scalar(line.split(":", 1)[1])
            continue
        if line.startswith("to:") and current_from is not None:
            if include_sources:
                words.append(current_from)
            words.append(parse_scalar(line.split(":", 1)[1]))
            current_from = None
            continue
        if in_preferred_terms and line.startswith("- "):
            words.append(parse_scalar(line[2:]))

    seen: set[str] = set()
    output: list[str] = []
    for word in words:
        normalized = word.strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        output.append(normalized)
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corrections", type=Path, default=SKILL_DIR / "data" / "corrections.yaml")
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--include-sources", action="store_true")
    args = parser.parse_args()

    hotwords = load_hotwords(args.corrections, args.include_sources)
    text = "\n".join(hotwords) + ("\n" if hotwords else "")
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
