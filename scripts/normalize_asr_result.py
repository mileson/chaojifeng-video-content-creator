#!/usr/bin/env python3
"""Normalize ASR provider JSON into the transcript schema used by this skill."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


def as_seconds(value: Any, unit: str) -> float:
    number = float(value)
    if unit == "milliseconds" or (unit == "auto" and number > 10_000):
        return number / 1000.0
    return number


def first_list(data: Any, keys: tuple[str, ...]) -> list[Any]:
    if isinstance(data, dict):
        for key in keys:
            value = data.get(key)
            if isinstance(value, list):
                return value
        for value in data.values():
            found = first_list(value, keys)
            if found:
                return found
    elif isinstance(data, list):
        for item in data:
            found = first_list(item, keys)
            if found:
                return found
    return []


def clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text.strip())
    return re.sub(r"(\.{3,}|…+)\s*$", "", text).strip()


def normalize_word(raw: dict[str, Any], unit: str) -> dict[str, Any] | None:
    text = str(raw.get("text") or raw.get("word") or "").strip()
    start = raw.get("start", raw.get("start_time"))
    end = raw.get("end", raw.get("end_time"))
    if start is None or end is None:
        return None
    start_s = as_seconds(start, unit)
    end_s = as_seconds(end, unit)
    if end_s <= start_s:
        return None
    return {"text": text, "start": round(start_s, 3), "end": round(end_s, 3)}


def normalize_utterance(raw: dict[str, Any], unit: str) -> dict[str, Any] | None:
    start = raw.get("start", raw.get("start_time"))
    end = raw.get("end", raw.get("end_time"))
    words = [word for item in raw.get("words", []) if isinstance(item, dict) and (word := normalize_word(item, unit))]

    alternatives = raw.get("alternatives")
    if not words and isinstance(alternatives, list) and alternatives:
        first = alternatives[0]
        if isinstance(first, dict):
            words = [
                word
                for item in first.get("words", [])
                if isinstance(item, dict) and (word := normalize_word(item, unit))
            ]

    if start is None and words:
        start = words[0]["start"]
    if end is None and words:
        end = words[-1]["end"]
    if start is None or end is None:
        return None

    start_s = as_seconds(start, unit)
    end_s = as_seconds(end, unit)
    if end_s <= start_s:
        return None

    text = clean_text(str(raw.get("text") or raw.get("utterance") or ""))
    if not text and alternatives and isinstance(alternatives, list):
        first = alternatives[0]
        if isinstance(first, dict):
            text = clean_text(str(first.get("text") or ""))
    if not text:
        text = clean_text("".join(str(word["text"]) for word in words))
    if not text:
        return None

    return {
        "start": round(start_s, 3),
        "end": round(end_s, 3),
        "text": text,
        "words": words,
    }


def normalize(data: dict[str, Any], provider: str) -> dict[str, Any]:
    raw_utterances = first_list(data, ("utterances", "results", "segments"))
    unit = "milliseconds" if provider in {"volcengine_vc", "volcengine", "volcengine_bigmodel_flash"} else "auto"
    segments = [
        segment
        for item in raw_utterances
        if isinstance(item, dict) and (segment := normalize_utterance(item, unit))
    ]
    segments.sort(key=lambda item: (item["start"], item["end"]))
    duration = max((segment["end"] for segment in segments), default=0.0)
    return {
        "provider": provider,
        "duration": round(duration, 3),
        "segments": segments,
        "stats": {
            "segment_count": len(segments),
            "word_count": sum(len(segment.get("words", [])) for segment in segments),
            "has_word_timestamps": any(segment.get("words") for segment in segments),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--provider", default="auto")
    args = parser.parse_args()

    data = json.loads(args.input.read_text(encoding="utf-8"))
    transcript = normalize(data, args.provider)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(transcript, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        "normalized",
        transcript["stats"]["segment_count"],
        "segments /",
        transcript["stats"]["word_count"],
        "words",
    )


if __name__ == "__main__":
    main()
{
  "mode": "standard",
  "source": {
    "video": "<source-video.mp4>",
    "transcript": "aroll/transcript.normalized.json",
    "notes": "本文件只记录这条视频的剪辑、字幕拆分和口癖删除计划；可复用规则写入 data/filler_rules.yaml 或 data/corrections.yaml。"
  },
  "global_replacements": [
    {
      "from": "<ASR 识别错词>",
      "to": "<正确写法>",
      "reason": "仅限本条视频的错字、专名或同音词修正"
    }
  ],
  "word_cut_ranges": [
    {
      "start": 12.34,
      "end": 12.72,
      "text": "嗯",
      "reason": "无效语气词/口水话",
      "padding_before": 0.0,
      "padding_after": 0.0,
      "confidence": "high"
    },
    {
      "start": 23.10,
      "end": 24.85,
      "text": "今天的话",
      "reason": "纯口癖，删后不改变语义",
      "padding_before": 0.0,
      "padding_after": 0.0,
      "confidence": "medium"
    }
  ],
  "event_overrides": [
    {
      "range_start": 30.0,
      "range_end": 34.2,
      "reason": "原字幕把两个完整意群粘在一起",
      "parts": [
        {
          "text": "第一句完整意思",
          "weight": 1.0
        },
        {
          "text": "第二句完整意思",
          "weight": 1.0
        }
      ]
    }
  ],
  "review_required": [
    {
      "range": "45.20-48.10",
      "text": "<候选删除内容>",
      "reason": "可能影响语义，需人工确认",
      "confidence": "low"
    }
  ]
}
