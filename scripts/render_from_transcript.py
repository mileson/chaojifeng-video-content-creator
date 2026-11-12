#!/usr/bin/env python3
"""Render a talking-head edit from transcript segments and review windows.

This script intentionally uses only the Python standard library plus FFmpeg.
It reads the skill's lightweight YAML-like config files with small parsers for
the specific fields this skill owns.
"""

# # 文件说明书 (File Manual)
# ## 核心功能 (Core Function)
# 根据逐字稿、剪辑决策与字幕样式生成清洗后的口播视频、SRT、ASS 和验证材料；也提供统一的 SRT→ASS 入口，默认支持带轻微字距的橙色圆角底、黑字白描边双层字幕；所有 SRT/ASS 导出在最终换行后清理行尾标点，纯标点行阻断导出以待复核。
#
# ## 输入 (Input)
# 源视频、标准化逐字稿或现成 SRT、subtitle_plan、剪辑窗口、停顿日志，以及 data 目录中的清洗规则和字幕样式配置。
#
# ## 输出 (Output)
# 清洗版 MP4、统一样式 ASS、SRT、edit_decisions、隐藏口播审计、抽帧检查图和 publish-notes。
#
# ## 定位 (Position)
# chaojifeng-video-content-creator 的阶段 6 到阶段 8 执行器，负责把语义清洗决策稳定地落实到音视频和字幕渲染。
#
# ## 依赖 (Dependency)
# - data/subtitle_styles.yaml：提供默认及可选字幕视觉预设。
# - data/filler_rules.yaml：提供停顿、口水词、剪后空白和词边界保护规则。
# - FFmpeg/libass：完成音视频拼接、ASS 字幕烧录与代表帧抽取。
#
# ## 维护规则 (Maintenance Rules)
# 1. 每次修改代码逻辑后，必须检查并更新上述的【核心功能】、【输入】、【输出】等信息，确保文档与代码一致。
# 2. 禁止修改或删除本【维护规则】章节的内容。
# 3. 修改完成后，必须扫描当前文件所在的文件夹目录，找到对应的 [当前文件夹名称]_README.md 文档，并同步更新该 README 中关于本文件的描述信息。

from __future__ import annotations

import argparse
import difflib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent


def parse_scalar(value: str) -> Any:
    value = value.strip()
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    if value.startswith("'") and value.endswith("'"):
        return value[1:-1]
    if value in {"true", "false"}:
        return value == "true"
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value


def load_replacements(path: Path) -> list[tuple[str, str]]:
    replacements: list[tuple[str, str]] = []
    current_from: str | None = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line.startswith("- from:"):
            current_from = parse_scalar(line.split(":", 1)[1])
        elif line.startswith("to:") and current_from is not None:
            replacements.append((current_from, parse_scalar(line.split(":", 1)[1])))
            current_from = None
    return replacements


def load_silence_config(path: Path) -> dict[str, float]:
    defaults = {
        "ignore_below_seconds": 0.25,
        "suggest_delete_above_seconds": 1.0,
        "force_review_above_seconds": 5.0,
        "keep_padding_seconds": 0.16,
        "minimum_keep_piece_seconds": 0.75,
    }
    in_silence = False
    in_semantic = False
    for raw in path.read_text(encoding="utf-8").splitlines():
        if raw.strip() == "silence:":
            in_silence = True
            in_semantic = False
            continue
        if raw.strip() == "semantic_cut_patterns:":
            in_silence = False
            in_semantic = True
            continue
        if (in_silence or in_semantic) and raw and not raw.startswith(" "):
            break
        if (in_silence or in_semantic) and ":" in raw:
            key, value = raw.strip().split(":", 1)
            if key in defaults:
                defaults[key] = float(parse_scalar(value))
    return defaults


def load_subtitle_cleanup_config(path: Path) -> dict[str, Any]:
    defaults: dict[str, Any] = {
        "forbid_terminal_ellipsis": True,
        "near_duplicate_window_seconds": 1.2,
        "near_duplicate_similarity": 0.72,
        "overlap_min_chars": 6,
        "false_start_min_chars": 3,
        "false_start_max_delete_chars": 18,
        "max_subtitle_visual_width_ratio": 1.0,
        "min_split_event_seconds": 0.85,
    }
    in_cleanup = False
    for raw in path.read_text(encoding="utf-8").splitlines():
        if raw.strip() == "subtitle_cleanup:":
            in_cleanup = True
            continue
        if in_cleanup and raw and not raw.startswith(" "):
            break
        if in_cleanup and ":" in raw:
            key, value = raw.strip().split(":", 1)
            if key in defaults:
                defaults[key] = parse_scalar(value)
    return defaults


def load_consistency_config(path: Path) -> dict[str, Any]:
    defaults: dict[str, Any] = {
        "enabled": True,
        "block_on_hidden_speech": True,
        "min_hidden_chars": 3,
        "min_hidden_duration_seconds": 0.20,
        "max_source_gap_seconds": 1.2,
    }
    in_consistency = False
    for raw in path.read_text(encoding="utf-8").splitlines():
        if raw.strip() == "subtitle_audio_consistency:":
            in_consistency = True
            continue
        if in_consistency and raw and not raw.startswith(" "):
            break
        if in_consistency and ":" in raw:
            key, value = raw.strip().split(":", 1)
            if key in defaults:
                defaults[key] = parse_scalar(value)
    return defaults


def load_boundary_silence_config(path: Path) -> dict[str, Any]:
    defaults: dict[str, Any] = {
        "enabled": True,
        "gap_threshold_seconds": 0.28,
        "keep_before_word_seconds": 0.08,
        "keep_after_word_seconds": 0.06,
        "min_cut_seconds": 0.16,
        "max_passes": 2,
    }
    in_section = False
    for raw in path.read_text(encoding="utf-8").splitlines():
        if raw.strip() == "post_cut_silence_cleanup:":
            in_section = True
            continue
        if in_section and raw and not raw.startswith(" "):
            break
        if in_section and ":" in raw:
            key, value = raw.strip().split(":", 1)
            if key in defaults:
                defaults[key] = parse_scalar(value)
    return defaults


def load_word_boundary_guard_config(path: Path) -> dict[str, Any]:
    defaults: dict[str, Any] = {
        "enabled": True,
        "protect_initial_segment_start": True,
        "apply_start_guard_to_first_segment_only": True,
        "near_segment_start_seconds": 0.08,
        "pre_word_padding_seconds": 0.18,
        "max_start_extension_seconds": 0.24,
        "near_segment_end_seconds": 0.08,
        "post_word_padding_seconds": 0.18,
        "max_extension_seconds": 0.24,
        "stop_before_next_word_seconds": 0.04,
    }
    in_section = False
    for raw in path.read_text(encoding="utf-8").splitlines():
        if raw.strip() == "word_boundary_guard:":
            in_section = True
            continue
        if in_section and raw and not raw.startswith(" "):
            break
        if in_section and ":" in raw:
            key, value = raw.strip().split(":", 1)
            if key in defaults:
                defaults[key] = parse_scalar(value)
    return defaults


def load_style(path: Path, requested: str | None) -> tuple[str, dict[str, Any]]:
    text = path.read_text(encoding="utf-8").splitlines()
    default_style = "orange_rounded_black_white_outline"
    for raw in text:
        if raw.startswith("default_style:"):
            default_style = str(parse_scalar(raw.split(":", 1)[1]))
            break
    name = requested or default_style
    style: dict[str, Any] = {}
    in_style = False
    for raw in text:
        if raw.startswith(f"  {name}:"):
            in_style = True
            continue
        if in_style:
            if raw.startswith("  ") and not raw.startswith("    ") and raw.strip().endswith(":"):
                break
            if raw.startswith("    ") and ":" in raw:
                key, value = raw.strip().split(":", 1)
                style[key] = parse_scalar(value)
    if not style:
        raise SystemExit(f"Subtitle style not found: {name}")
    return name, style


def parse_time_pair(value: str) -> tuple[float, float, str]:
    parts = value.split(":", 2)
    if len(parts) < 2:
        raise argparse.ArgumentTypeError("window must be START:END[:REASON]")
    start = float(parts[0])
    end = float(parts[1])
    reason = parts[2] if len(parts) == 3 else "手动保留"
    if end <= start:
        raise argparse.ArgumentTypeError("window END must be greater than START")
    return start, end, reason


def parse_silence_log(path: Path | None) -> list[tuple[float, float, float]]:
    if not path or not path.exists():
        return []
    silences: list[tuple[float, float, float]] = []
    current: float | None = None
    for line in path.read_text(errors="ignore").splitlines():
        m = re.search(r"silence_start: ([0-9.]+)", line)
        if m:
            current = float(m.group(1))
        m = re.search(r"silence_end: ([0-9.]+) \| silence_duration: ([0-9.]+)", line)
        if m and current is not None:
            end = float(m.group(1))
            duration = float(m.group(2))
            silences.append((current, end, duration))
            current = None
    return silences


def assign_output_timeline(segments: list[dict[str, Any]], cover_duration: float) -> list[dict[str, Any]]:
    cursor = cover_duration
    for idx, seg in enumerate(segments):
        seg["id"] = idx
        seg["duration"] = round(float(seg["source_end"]) - float(seg["source_start"]), 3)
        seg["output_start"] = round(cursor, 3)
        cursor += seg["duration"]
        seg["output_end"] = round(cursor, 3)
    return segments


def load_segments_from_decisions(path: Path, cover_duration: float) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    segments: list[dict[str, Any]] = []
    for seg in data.get("segments", []):
        source_start = float(seg["source_start"])
        source_end = float(seg["source_end"])
        if source_end <= source_start:
            continue
        segments.append({
            "source_start": round(source_start, 3),
            "source_end": round(source_end, 3),
            "reason": str(seg.get("reason", "复用已确认剪辑边界")),
        })
    if not segments:
        raise SystemExit(f"No usable segments found in {path}")
    return assign_output_timeline(segments, cover_duration), data


def clean_text(text: str, replacements: list[tuple[str, str]]) -> str:
    cleaned = re.sub(r"\s+", " ", text.strip())
    for old, new in replacements:
        cleaned = cleaned.replace(old, new)
    cleaned = re.sub(r"\s+", " ", cleaned.strip())
    cleaned = cleaned.replace(" ,", ",")
    cleaned = re.sub(r"(\.{3,}|…+)\s*$", "", cleaned)
    return cleaned


def word_time(value: Any) -> float:
    numeric = float(value)
    if numeric > 10_000:
        return numeric / 1000.0
    return numeric


def normalize_word(word: dict[str, Any]) -> dict[str, Any] | None:
    text = str(word.get("text") or word.get("word") or "").strip()
    if not text and not word.get("isGap"):
        return None
    start_value = word.get("start", word.get("start_time"))
    end_value = word.get("end", word.get("end_time"))
    if start_value is None or end_value is None:
        return None
    start = word_time(start_value)
    end = word_time(end_value)
    if end <= start:
        return None
    return {"text": text, "start": start, "end": end, "isGap": bool(word.get("isGap", False))}


def collect_transcript_words(transcript: dict[str, Any]) -> list[dict[str, Any]]:
    words: list[dict[str, Any]] = []
    for src in transcript.get("segments", []):
        for word in src.get("words", []):
            item = normalize_word(word)
            if item and not item.get("isGap"):
                words.append(item)
    words.sort(key=lambda item: (float(item["start"]), float(item["end"])))
    return words


def needs_space(left: str, right: str) -> bool:
    if not left or not right:
        return False
    return left[-1].isascii() and right[0].isascii() and left[-1].isalnum() and right[0].isalnum()


def join_words(words: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for word in words:
        token = str(word.get("text", "")).strip()
        if not token:
            continue
        if parts and needs_space(parts[-1], token):
            parts.append(" ")
        parts.append(token)
    text = "".join(parts)
    text = re.sub(r"\s+([,，.。!！?？;；:：、])", r"\1", text)
    text = re.sub(r"([（(《“‘])\s+", r"\1", text)
    text = re.sub(r"\s+([）)》”’])", r"\1", text)
    return text


def fmt_srt(t: float) -> str:
    ms = int(round(t * 1000))
    h, rem = divmod(ms, 3_600_000)
    m, rem = divmod(rem, 60_000)
    s, ms = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def fmt_ass(t: float) -> str:
    cs = int(round(t * 100))
    h, rem = divmod(cs, 360_000)
    m, rem = divmod(rem, 6_000)
    s, cs = divmod(rem, 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def visual_width(text: str) -> float:
    return sum(0.55 if ord(ch) < 128 else 1.0 for ch in text)


NO_SPLIT_PAIRS = {
    "可以", "专业", "问题", "命名", "文档", "文件", "网页", "内容", "标题",
    "离职", "交接", "负责", "归档", "自动", "分类", "打包", "标准", "规范",
    "需求", "客户", "资料", "同学", "亮点", "实现", "确认", "信息", "生成",
    "我们", "他们", "你们", "看到", "看见", "整理", "事情", "过程", "里面",
    "名称", "序号", "引用", "对话", "扫描", "个人", "日期", "重复", "提交",
    "很多", "其实", "一些", "相对", "不再", "仓库", "未来", "职交", "接包",
}


def normalize_for_compare(text: str) -> str:
    lowered = text.lower()
    return re.sub(r"[\s,，.。!！?？;；:：、\"“”'‘’()（）\[\]【】<>《》-]+", "", lowered)


def is_compare_char(ch: str) -> bool:
    return not re.match(r"[\s,，.。!！?？;；:：、\"“”'‘’()（）\[\]【】<>《》\-]+", ch)


def normalized_source_chars(words: list[dict[str, Any]]) -> list[dict[str, Any]]:
    chars: list[dict[str, Any]] = []
    for word_index, word in enumerate(words):
        for ch in str(word.get("text", "")).lower():
            if is_compare_char(ch):
                chars.append({"char": ch, "word_index": word_index})
    return chars


def common_prefix_len(left: str, right: str) -> int:
    size = min(len(left), len(right))
    for idx in range(size):
        if left[idx].lower() != right[idx].lower():
            return idx
    return size


def trim_suffix_prefix_overlap(previous: str, current: str, min_chars: int) -> tuple[str, bool]:
    best = 0
    max_len = min(len(previous), len(current), 40)
    for size in range(min_chars, max_len + 1):
        if previous[-size:].lower() == current[:size].lower():
            best = size
    if not best:
        return previous, False
    trimmed = previous[:-best].rstrip("，,。；;、 ")
    return trimmed, bool(trimmed)


def remove_false_starts(text: str, cleanup_cfg: dict[str, Any]) -> str:
    min_chars = int(cleanup_cfg["false_start_min_chars"])
    max_delete = int(cleanup_cfg["false_start_max_delete_chars"])
    cleaned = text
    changed = True
    passes = 0
    while changed and passes < 8:
        changed = False
        passes += 1
        for start in range(len(cleaned)):
            best: tuple[int, int] | None = None
            for repeat in range(start + min_chars, min(len(cleaned), start + max_delete + 1)):
                prefix = common_prefix_len(cleaned[start:], cleaned[repeat:])
                if prefix >= min_chars:
                    best = (start, repeat)
            if best:
                start, repeat = best
                cleaned = (cleaned[:start] + cleaned[repeat:]).lstrip("，,。；;、 ")
                changed = True
                break
    return cleaned


def is_bad_split(text: str, index: int) -> bool:
    if index <= 0 or index >= len(text):
        return False
    prev = text[index - 1]
    curr = text[index]
    if prev.isascii() and curr.isascii() and prev.isalnum() and curr.isalnum():
        return True
    return f"{prev}{curr}" in NO_SPLIT_PAIRS


def choose_split_index(text: str, max_visual_width: float) -> int:
    target = max_visual_width * 0.88
    width = 0.0
    candidates: list[tuple[float, int]] = []
    break_after = set("，,。！？!?；;、 ")
    soft_before = set("并就还也但那这我你他它们而或给和在把从到对跟将是有要需不再")
    soft_after = set("的了着过吧吗呢啊呀哦行")

    for idx, ch in enumerate(text):
        width += 0.55 if ord(ch) < 128 else 1.0
        split_index = idx + 1
        if split_index < 6 or is_bad_split(text, split_index):
            continue
        if width > max_visual_width:
            break
        score = abs(width - target)
        if ch in break_after:
            score -= 9
        if ch in soft_after:
            score -= 3
        if split_index < len(text) and text[split_index] in soft_before:
            score -= 2
        candidates.append((score, split_index))

    if candidates:
        return min(candidates)[1]

    width = 0.0
    fallback = min(len(text), max(1, int(max_visual_width)))
    for idx, ch in enumerate(text):
        width += 0.55 if ord(ch) < 128 else 1.0
        if width > max_visual_width:
            fallback = idx
            break
    while fallback > 1 and is_bad_split(text, fallback):
        fallback -= 1
    return max(1, fallback)


def split_text_chunks(text: str, max_visual_width: float) -> list[str]:
    if visual_width(text) <= max_visual_width:
        return [text]
    chunks: list[str] = []
    remaining = text.strip()
    while remaining:
        if visual_width(remaining) <= max_visual_width:
            chunks.append(remaining.strip())
            break
        split_at = choose_split_index(remaining, max_visual_width)
        chunk = remaining[:split_at].strip()
        if chunk:
            chunks.append(chunk)
        remaining = remaining[split_at:].strip()
    if len(chunks) > 1 and visual_width(chunks[-1]) < 4:
        chunks[-2] = f"{chunks[-2]}{chunks[-1]}"
        chunks.pop()
    return chunks


def split_event(event: dict[str, Any], max_visual_width: float, min_seconds: float) -> list[dict[str, Any]]:
    chunks = split_text_chunks(event["text"], max_visual_width)
    if len(chunks) == 1:
        return [event]
    duration = max(0.01, event["end"] - event["start"])
    weights = [max(1.0, visual_width(chunk)) for chunk in chunks]
    total_weight = sum(weights)
    output: list[dict[str, Any]] = []
    cursor = event["start"]
    for idx, (chunk, weight) in enumerate(zip(chunks, weights)):
        if idx == len(chunks) - 1:
            end = event["end"]
        else:
            share = duration * (weight / total_weight)
            remaining_chunks = len(chunks) - idx - 1
            latest_end = event["end"] - remaining_chunks * min_seconds
            end = min(max(cursor + min_seconds, cursor + share), latest_end)
            if end <= cursor:
                end = cursor + max(0.01, duration / len(chunks))
        output.append({"start": round(cursor, 3), "end": round(end, 3), "text": chunk})
        cursor = end
    return output


def load_subtitle_plan(path: Path | None) -> dict[str, Any]:
    if not path or not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def plan_replacements(plan: dict[str, Any]) -> list[tuple[str, str]]:
    replacements: list[tuple[str, str]] = []
    for item in plan.get("global_replacements", []):
        old = str(item.get("from", ""))
        new = str(item.get("to", ""))
        if old:
            replacements.append((old, new))
    return replacements


def merge_cut_ranges(ranges: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ordered = sorted(ranges, key=lambda item: (float(item["start"]), float(item["end"])))
    merged: list[dict[str, Any]] = []
    for item in ordered:
        current = {
            "start": round(max(0.0, float(item["start"])), 3),
            "end": round(max(0.0, float(item["end"])), 3),
            "text": str(item.get("text", "")),
            "reason": str(item.get("reason", "词级口水词剪切")),
        }
        if current["end"] <= current["start"]:
            continue
        if merged and current["start"] <= float(merged[-1]["end"]) + 0.015:
            merged[-1]["end"] = round(max(float(merged[-1]["end"]), float(current["end"])), 3)
            texts = [value for value in [merged[-1].get("text", ""), current.get("text", "")] if value]
            if texts:
                merged[-1]["text"] = "+".join(texts)
            reasons = [value for value in [merged[-1].get("reason", ""), current.get("reason", "")] if value]
            if reasons:
                merged[-1]["reason"] = " + ".join(dict.fromkeys(reasons))
            continue
        merged.append(current)
    return merged


def plan_word_cut_ranges(plan: dict[str, Any]) -> list[dict[str, Any]]:
    ranges: list[dict[str, Any]] = []
    for item in plan.get("word_cut_ranges", []):
        try:
            start = float(item["start"])
            end = float(item["end"])
        except (KeyError, TypeError, ValueError):
            continue
        if end <= start:
            continue
        padding_before = float(item.get("padding_before", 0.0))
        padding_after = float(item.get("padding_after", 0.0))
        ranges.append({
            "start": max(0.0, start - padding_before),
            "end": max(0.0, end + padding_after),
            "text": str(item.get("text", "")),
            "reason": str(item.get("reason", "词级口水词剪切")),
        })
    return merge_cut_ranges(ranges)


def event_matches_override(event: dict[str, Any], override: dict[str, Any]) -> bool:
    tolerance = float(override.get("tolerance", 0.35))
    if "source_start" in override and "source_start" in event:
        if abs(float(event["source_start"]) - float(override["source_start"])) <= tolerance:
            return True
    if "source_end" in override and "source_end" in event:
        if abs(float(event["source_end"]) - float(override["source_end"])) <= tolerance:
            return True
    if "start" in override and abs(float(event["start"]) - float(override["start"])) <= tolerance:
        return True
    if "end" in override and abs(float(event["end"]) - float(override["end"])) <= tolerance:
        return True
    range_start = override.get("range_start")
    range_end = override.get("range_end")
    if range_start is not None and range_end is not None:
        overlap = min(float(event["end"]), float(range_end)) - max(float(event["start"]), float(range_start))
        return overlap > max(0.2, 0.45 * (float(event["end"]) - float(event["start"])))
    return False


def split_event_from_plan_parts(
    event: dict[str, Any],
    parts: list[Any],
    min_seconds: float,
) -> list[dict[str, Any]]:
    texts: list[str] = []
    weights: list[float] = []
    for part in parts:
        if isinstance(part, dict):
            text = str(part.get("text", "")).strip()
            weight = float(part.get("weight", max(1.0, visual_width(text))))
        else:
            text = str(part).strip()
            weight = max(1.0, visual_width(text))
        if text:
            texts.append(text)
            weights.append(weight)
    if not texts:
        return []
    if len(texts) == 1:
        return [{"start": event["start"], "end": event["end"], "text": texts[0], "_planned": True}]

    duration = max(0.01, float(event["end"]) - float(event["start"]))
    total_weight = sum(weights)
    cursor = float(event["start"])
    output: list[dict[str, Any]] = []
    for idx, (text, weight) in enumerate(zip(texts, weights)):
        if idx == len(texts) - 1:
            end = float(event["end"])
        else:
            share = duration * (weight / total_weight)
            remaining = len(texts) - idx - 1
            latest_end = float(event["end"]) - remaining * min_seconds
            end = min(max(cursor + min_seconds, cursor + share), latest_end)
            if end <= cursor:
                end = cursor + max(0.01, duration / len(texts))
        output.append({"start": round(cursor, 3), "end": round(end, 3), "text": text, "_planned": True})
        cursor = end
    return output


def apply_subtitle_plan(
    events: list[dict[str, Any]],
    plan: dict[str, Any],
    min_seconds: float,
) -> list[dict[str, Any]]:
    overrides = list(plan.get("event_overrides", []))
    used: set[int] = set()
    output: list[dict[str, Any]] = []
    for event in events:
        matched_index: int | None = None
        for idx, override in enumerate(overrides):
            if idx in used:
                continue
            if event_matches_override(event, override):
                matched_index = idx
                break
        if matched_index is None:
            output.append(event)
            continue
        used.add(matched_index)
        planned = split_event_from_plan_parts(event, overrides[matched_index].get("parts", []), min_seconds)
        output.extend(planned or [event])
    return output


def clean_subtitle_events(events: list[dict[str, Any]], cleanup_cfg: dict[str, Any]) -> list[dict[str, Any]]:
    overlap_min = int(cleanup_cfg["overlap_min_chars"])
    window = float(cleanup_cfg["near_duplicate_window_seconds"])
    similarity_cutoff = float(cleanup_cfg["near_duplicate_similarity"])
    compact: list[dict[str, Any]] = []

    for event in events:
        event = dict(event)
        event["text"] = remove_false_starts(event["text"], cleanup_cfg)
        event["text"] = re.sub(r"(\.{3,}|…+)\s*$", "", event["text"]).strip("，,。；;、 ")
        if not event["text"]:
            continue

        if compact:
            previous = compact[-1]
            gap = event["start"] - previous["end"]
            prev_norm = normalize_for_compare(previous["text"])
            curr_norm = normalize_for_compare(event["text"])

            if gap <= window and previous["text"] == event["text"]:
                previous["end"] = event["end"]
                continue

            if gap <= window:
                trimmed, usable = trim_suffix_prefix_overlap(previous["text"], event["text"], overlap_min)
                if usable and trimmed != previous["text"]:
                    previous["text"] = trimmed
                    prev_norm = normalize_for_compare(previous["text"])

            if gap <= window and prev_norm and curr_norm:
                similarity = difflib.SequenceMatcher(None, prev_norm, curr_norm).ratio()
                if curr_norm.startswith(prev_norm) or (similarity >= similarity_cutoff and len(curr_norm) >= len(prev_norm)):
                    compact[-1] = event
                    continue
                if prev_norm.startswith(curr_norm) or similarity >= similarity_cutoff:
                    previous["end"] = max(previous["end"], event["end"])
                    continue

        compact.append(event)

    return compact


def subtitle_text_lines(text: str, max_chars: int) -> list[str]:
    manual_lines = [line.strip() for line in text.replace("\\n", "\n").splitlines() if line.strip()]
    if not manual_lines:
        manual_lines = [text.strip()]
    chunks: list[str] = []
    for line in manual_lines:
        chunks.extend(split_text_chunks(line, float(max_chars)))
    return chunks


def wrap_text(text: str, max_chars: int, max_lines: int) -> str:
    chunks = subtitle_text_lines(text, max_chars)
    if len(chunks) > max_lines:
        chunks = chunks[: max_lines - 1] + ["".join(chunks[max_lines - 1:])]
    return r"\N".join(clean_subtitle_line_end(line) for line in chunks)


def rounded_rect_ass_path(width: int, height: int, radius: int) -> str:
    """Return a one-pixel ASS vector path for a rounded rectangle."""
    radius = max(1, min(radius, width // 2, height // 2))
    control = int(round(radius * 0.55228475))
    return " ".join([
        f"m {radius} 0",
        f"l {width - radius} 0",
        f"b {width - radius + control} 0 {width} {radius - control} {width} {radius}",
        f"l {width} {height - radius}",
        f"b {width} {height - radius + control} {width - radius + control} {height} {width - radius} {height}",
        f"l {radius} {height}",
        f"b {radius - control} {height} 0 {height - radius + control} 0 {height - radius}",
        f"l 0 {radius}",
        f"b 0 {radius - control} {radius - control} 0 {radius} 0",
    ])


def rounded_caption_layout(wrapped_text: str, style: dict[str, Any]) -> dict[str, int]:
    text_lines = [line for line in wrapped_text.split(r"\N") if line]
    font_size = float(style["font_size"])
    padding_h = int(style.get("padding_h", 34))
    padding_v = int(style.get("padding_v", 14))
    line_height = int(style.get("line_height", round(font_size * 1.28)))
    min_width = int(style.get("min_width", 320))
    max_width = int(style.get("max_width", 1480))
    letter_spacing = float(style.get("letter_spacing_px", 0.0))
    widest_line = max(text_lines, key=visual_width, default="")
    widest = visual_width(widest_line)
    spacing_width = max(0, len(widest_line) - 1) * letter_spacing
    width = max(min_width, min(max_width, int(round(widest * font_size + spacing_width + 2 * padding_h))))
    height = max(line_height + 2 * padding_v, len(text_lines) * line_height + 2 * padding_v)
    margin_v = int(style.get("margin_v", 38))
    x = (1920 - width) // 2
    y = 1080 - margin_v - height
    ratio = float(style.get("corner_radius_ratio", 0.25))
    radius = int(round(height * ratio))
    return {"width": width, "height": height, "x": x, "y": y, "radius": radius}


TRAILING_SUBTITLE_PUNCTUATION = re.compile(r"[，,。.!！?？;；:：、…]+\s*$")


def clean_subtitle_line_end(text: str) -> str:
    """Remove display-line terminal punctuation without changing interior text."""
    cleaned = TRAILING_SUBTITLE_PUNCTUATION.sub("", text.rstrip())
    if text.strip() and not cleaned:
        raise ValueError("Subtitle line contains only punctuation; review the cue before export")
    return cleaned


def srt_text(text: str) -> str:
    return "\n".join(clean_subtitle_line_end(line) for line in subtitle_text_lines(text, 999))


def build_keep_segments(
    windows: list[tuple[float, float, str]],
    silences: list[tuple[float, float, float]],
    silence_cfg: dict[str, float],
    cover_duration: float,
) -> list[dict[str, Any]]:
    threshold = silence_cfg["suggest_delete_above_seconds"]
    pad = silence_cfg["keep_padding_seconds"]
    min_piece = silence_cfg["minimum_keep_piece_seconds"]
    segments: list[dict[str, Any]] = []
    for start, end, reason in windows:
        cursor = start
        for ss, se, duration in silences:
            if se <= start or ss >= end or duration < threshold:
                continue
            cut_start = max(start, ss + pad)
            cut_end = min(end, se - pad)
            if cut_end <= cursor or cut_end - cut_start <= 0.25:
                continue
            if cut_start - cursor >= min_piece:
                segments.append({"source_start": cursor, "source_end": cut_start, "reason": reason})
            cursor = max(cursor, cut_end)
        if end - cursor >= min_piece:
            segments.append({"source_start": cursor, "source_end": end, "reason": reason})

    merged: list[dict[str, Any]] = []
    for seg in segments:
        if merged and seg["reason"] == merged[-1]["reason"] and seg["source_start"] - merged[-1]["source_end"] < 0.18:
            merged[-1]["source_end"] = seg["source_end"]
        else:
            merged.append(seg)

    return assign_output_timeline(merged, cover_duration)


def apply_source_cuts(
    segments: list[dict[str, Any]],
    cut_ranges: list[dict[str, Any]],
    cover_duration: float,
) -> list[dict[str, Any]]:
    if not cut_ranges:
        return assign_output_timeline(segments, cover_duration)

    min_piece = 0.04
    output: list[dict[str, Any]] = []
    for seg in segments:
        cursor = float(seg["source_start"])
        seg_end = float(seg["source_end"])
        for cut in cut_ranges:
            cut_start = max(float(cut["start"]), float(seg["source_start"]))
            cut_end = min(float(cut["end"]), seg_end)
            if cut_end <= cursor or cut_start >= seg_end:
                continue
            if cut_start - cursor >= min_piece:
                kept = {key: value for key, value in seg.items() if key not in {"id", "duration", "output_start", "output_end"}}
                kept["source_start"] = round(cursor, 3)
                kept["source_end"] = round(cut_start, 3)
                kept["reason"] = seg.get("reason", "手动保留")
                output.append(kept)
            cursor = max(cursor, cut_end)
        if seg_end - cursor >= min_piece:
            kept = {key: value for key, value in seg.items() if key not in {"id", "duration", "output_start", "output_end"}}
            kept["source_start"] = round(cursor, 3)
            kept["source_end"] = round(seg_end, 3)
            kept["reason"] = seg.get("reason", "手动保留")
            output.append(kept)
    return assign_output_timeline(output, cover_duration)


def words_overlapping_range(
    words: list[dict[str, Any]],
    start: float,
    end: float,
) -> list[dict[str, Any]]:
    return [
        word for word in words
        if float(word["end"]) > start + 0.005 and float(word["start"]) < end - 0.005
    ]


def apply_word_boundary_guard(
    segments: list[dict[str, Any]],
    words: list[dict[str, Any]],
    cfg: dict[str, Any],
    source_duration: float | None,
    cover_duration: float,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if not cfg.get("enabled", True) or not words:
        return segments, []

    protect_initial_start = bool(cfg.get("protect_initial_segment_start", True))
    first_segment_only = bool(cfg.get("apply_start_guard_to_first_segment_only", True))
    near_start = float(cfg["near_segment_start_seconds"])
    pre_pad = float(cfg["pre_word_padding_seconds"])
    max_start_extension = float(cfg["max_start_extension_seconds"])
    near_end = float(cfg["near_segment_end_seconds"])
    post_pad = float(cfg["post_word_padding_seconds"])
    max_extension = float(cfg["max_extension_seconds"])
    stop_before_next = float(cfg["stop_before_next_word_seconds"])
    updated: list[dict[str, Any]] = []
    adjustments: list[dict[str, Any]] = []

    for idx, seg in enumerate(segments):
        item = {key: value for key, value in seg.items() if key not in {"id", "duration", "output_start", "output_end"}}
        seg_start = float(seg["source_start"])
        seg_end = float(seg["source_end"])

        if protect_initial_start and (not first_segment_only or idx == 0):
            start_words = words_overlapping_range(words, seg_start - near_start, seg_end)
            next_words = [word for word in start_words if float(word["start"]) >= seg_start - near_start]
            if next_words:
                first_word = min(next_words, key=lambda word: float(word["start"]))
                first_start = float(first_word["start"])
                if 0 <= first_start - seg_start <= near_start:
                    new_start = max(0.0, first_start - min(pre_pad, max_start_extension))
                    if idx > 0:
                        new_start = max(new_start, float(segments[idx - 1]["source_end"]) + 0.02)
                    if new_start < seg_start - 0.005:
                        item["source_start"] = round(new_start, 3)
                        adjustments.append({
                            "from_start": round(seg_start, 3),
                            "to_start": round(new_start, 3),
                            "source_end": round(seg_end, 3),
                            "first_word": str(first_word.get("text", "")),
                            "reason": "保护开头字的音头",
                        })
                        seg_start = new_start

        segment_words = words_overlapping_range(words, seg_start, seg_end + near_end)
        prior_words = [word for word in segment_words if float(word["end"]) <= seg_end + near_end]
        if prior_words:
            last_word = max(prior_words, key=lambda word: float(word["end"]))
            last_end = float(last_word["end"])
            if 0 <= seg_end - last_end <= near_end:
                cap = min(seg_end + max_extension, last_end + post_pad)
                if source_duration:
                    cap = min(cap, source_duration)
                next_words = [word for word in words if float(word["start"]) > last_end + 0.005]
                if next_words:
                    cap = min(cap, max(seg_end, float(next_words[0]["start"]) - stop_before_next))
                if idx + 1 < len(segments):
                    cap = min(cap, max(seg_end, float(segments[idx + 1]["source_start"]) - 0.02))
                if cap > seg_end + 0.005:
                    item["source_end"] = round(cap, 3)
                    adjustments.append({
                        "source_start": round(seg_start, 3),
                        "from_end": round(seg_end, 3),
                        "to_end": round(cap, 3),
                        "last_word": str(last_word.get("text", "")),
                        "reason": "保护结尾短词尾音",
                    })
        updated.append(item)

    return assign_output_timeline(updated, cover_duration), adjustments


def plan_boundary_silence_cuts(
    words: list[dict[str, Any]],
    segments: list[dict[str, Any]],
    cfg: dict[str, Any],
) -> list[dict[str, Any]]:
    if not cfg.get("enabled", True) or not words:
        return []

    threshold = float(cfg["gap_threshold_seconds"])
    keep_before = float(cfg["keep_before_word_seconds"])
    keep_after = float(cfg["keep_after_word_seconds"])
    min_cut = float(cfg["min_cut_seconds"])
    cuts: list[dict[str, Any]] = []

    for seg in segments:
        seg_start = float(seg["source_start"])
        seg_end = float(seg["source_end"])
        segment_words = words_overlapping_range(words, seg_start, seg_end)
        if not segment_words:
            continue

        first_word = min(segment_words, key=lambda word: float(word["start"]))
        first_start = float(first_word["start"])
        leading_end = max(seg_start, first_start - keep_before)
        if first_start - seg_start >= threshold and leading_end - seg_start >= min_cut:
            cuts.append({
                "start": round(seg_start, 3),
                "end": round(leading_end, 3),
                "text": "",
                "reason": "自动清理片段开头无词空白",
            })

        last_word = max(segment_words, key=lambda word: float(word["end"]))
        last_end = float(last_word["end"])
        trailing_start = min(seg_end, last_end + keep_after)
        if seg_end - last_end >= threshold and seg_end - trailing_start >= min_cut:
            cuts.append({
                "start": round(trailing_start, 3),
                "end": round(seg_end, 3),
                "text": "",
                "reason": "自动清理片段结尾无词空白",
            })

    return merge_cut_ranges(cuts)


def word_output_span(word: dict[str, Any], segments: list[dict[str, Any]]) -> dict[str, Any] | None:
    overlaps: list[tuple[float, float, float, float]] = []
    for seg in segments:
        overlap_start = max(float(word["start"]), float(seg["source_start"]))
        overlap_end = min(float(word["end"]), float(seg["source_end"]))
        if overlap_end - overlap_start <= 0.005:
            continue
        out_start = float(seg["output_start"]) + (overlap_start - float(seg["source_start"]))
        out_end = float(seg["output_start"]) + (overlap_end - float(seg["source_start"]))
        overlaps.append((overlap_start, overlap_end, out_start, out_end))
    if not overlaps:
        return None
    return {
        "text": word["text"],
        "start": round(overlaps[0][0], 3),
        "end": round(overlaps[-1][1], 3),
        "out_start": round(overlaps[0][2], 3),
        "out_end": round(overlaps[-1][3], 3),
    }


def group_selected_words(words: list[dict[str, Any]], max_source_gap: float = 1.2) -> list[list[dict[str, Any]]]:
    groups: list[list[dict[str, Any]]] = []
    current: list[dict[str, Any]] = []
    for word in words:
        if current and float(word["start"]) - float(current[-1]["end"]) > max_source_gap:
            groups.append(current)
            current = []
        current.append(word)
    if current:
        groups.append(current)
    return groups


def collect_kept_word_groups(
    transcript: dict[str, Any],
    segments: list[dict[str, Any]],
    max_source_gap: float,
) -> list[list[dict[str, Any]]]:
    groups: list[list[dict[str, Any]]] = []
    for src in transcript.get("segments", []):
        words = [
            item
            for word in src.get("words", [])
            if (item := normalize_word(word)) and not item.get("isGap")
        ]
        selected_words = [
            span
            for word in words
            if (span := word_output_span(word, segments)) is not None
        ]
        groups.extend(group_selected_words(selected_words, max_source_gap=max_source_gap))
    return groups


def overlapping_subtitle_text(events: list[dict[str, Any]], out_start: float, out_end: float) -> str:
    parts: list[str] = []
    for event in events:
        overlap = min(float(event["end"]), out_end) - max(float(event["start"]), out_start)
        if overlap > 0.01:
            parts.append(str(event.get("text", "")))
    return "".join(parts)


def hidden_issue_from_words(words: list[dict[str, Any]], reason: str) -> dict[str, Any]:
    return {
        "source_start": round(float(words[0]["start"]), 3),
        "source_end": round(float(words[-1]["end"]), 3),
        "output_start": round(float(words[0]["out_start"]), 3),
        "output_end": round(float(words[-1]["out_end"]), 3),
        "text": join_words(words),
        "reason": reason,
    }


def audit_subtitle_audio_consistency(
    transcript: dict[str, Any],
    segments: list[dict[str, Any]],
    events: list[dict[str, Any]],
    cfg: dict[str, Any],
) -> dict[str, Any]:
    if not cfg.get("enabled", True):
        return {"enabled": False, "issues": [], "checked_groups": 0}

    min_chars = int(cfg["min_hidden_chars"])
    min_duration = float(cfg["min_hidden_duration_seconds"])
    max_gap = float(cfg["max_source_gap_seconds"])
    groups = collect_kept_word_groups(transcript, segments, max_gap)
    issues: list[dict[str, Any]] = []

    for group in groups:
        if not group:
            continue
        source_chars = normalized_source_chars(group)
        source_norm = "".join(item["char"] for item in source_chars)
        if not source_norm:
            continue

        subtitle_text = overlapping_subtitle_text(events, float(group[0]["out_start"]), float(group[-1]["out_end"]))
        subtitle_norm = normalize_for_compare(subtitle_text)
        if not subtitle_norm:
            if len(source_norm) >= min_chars and float(group[-1]["end"]) - float(group[0]["start"]) >= min_duration:
                issues.append(hidden_issue_from_words(group, "kept audio has no subtitle coverage"))
            continue

        matcher = difflib.SequenceMatcher(None, source_norm, subtitle_norm)
        for tag, i1, i2, _j1, _j2 in matcher.get_opcodes():
            if tag != "delete":
                continue
            hidden_chars = source_chars[i1:i2]
            if len(hidden_chars) < min_chars:
                continue
            first_word_index = int(hidden_chars[0]["word_index"])
            last_word_index = int(hidden_chars[-1]["word_index"])
            hidden_words = group[first_word_index:last_word_index + 1]
            if not hidden_words:
                continue
            duration = float(hidden_words[-1]["end"]) - float(hidden_words[0]["start"])
            if duration < min_duration:
                continue
            hidden_text = join_words(hidden_words)
            hidden_norm = normalize_for_compare(hidden_text)
            if len(hidden_norm) < min_chars:
                continue
            issues.append(hidden_issue_from_words(hidden_words, "kept audio text is missing from final subtitles"))

    return {
        "enabled": True,
        "checked_groups": len(groups),
        "issue_count": len(issues),
        "issues": issues,
    }


def write_hidden_speech_review(json_path: Path, md_path: Path, audit: dict[str, Any]) -> None:
    json_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# Hidden Speech Review",
        "",
        f"- Enabled: {audit.get('enabled', False)}",
        f"- Checked groups: {audit.get('checked_groups', 0)}",
        f"- Issues: {len(audit.get('issues', []))}",
        "",
    ]
    issues = audit.get("issues", [])
    if issues:
        lines.extend([
            "| # | Source | Output | Hidden text | Reason |",
            "|---|---:|---:|---|---|",
        ])
        for idx, issue in enumerate(issues, start=1):
            text = str(issue.get("text", "")).replace("|", "\\|")
            reason = str(issue.get("reason", "")).replace("|", "\\|")
            lines.append(
                f"| {idx} | {issue.get('source_start')}-{issue.get('source_end')} | "
                f"{issue.get('output_start')}-{issue.get('output_end')} | {text} | {reason} |"
            )
        lines.extend([
            "",
            "Action: add confirmed hidden speech to subtitle_plan.word_cut_ranges, or mark the render with --allow-hidden-speech only after manual review.",
        ])
    else:
        lines.append("No kept speech was hidden from the final subtitles.")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_subtitles(
    transcript: dict[str, Any],
    segments: list[dict[str, Any]],
    replacements: list[tuple[str, str]],
    style: dict[str, Any],
    cleanup_cfg: dict[str, Any],
    subtitle_plan: dict[str, Any],
) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for src in transcript.get("segments", []):
        start = float(src["start"])
        end = float(src["end"])
        words = [
            item
            for word in src.get("words", [])
            if (item := normalize_word(word)) and not item.get("isGap")
        ]
        if words:
            selected_words = [
                span
                for word in words
                if (span := word_output_span(word, segments)) is not None
            ]
            for group in group_selected_words(selected_words):
                if not group:
                    continue
                full_source_event = group[0]["start"] <= start + 0.08 and group[-1]["end"] >= end - 0.08
                if full_source_event:
                    text = clean_text(str(src.get("text", "")), replacements)
                else:
                    text = clean_text(join_words(group), replacements)
                if not text or float(group[-1]["out_end"]) - float(group[0]["out_start"]) < 0.35:
                    continue
                events.append({
                    "start": round(float(group[0]["out_start"]), 3),
                    "end": round(float(group[-1]["out_end"]), 3),
                    "source_start": round(float(group[0]["start"]), 3),
                    "source_end": round(float(group[-1]["end"]), 3),
                    "text": text,
                })
            continue

        for seg in segments:
            istart = max(start, seg["source_start"])
            iend = min(end, seg["source_end"])
            if iend - istart < 0.45:
                continue
            text = clean_text(str(src.get("text", "")), replacements)
            event_start = istart
            event_end = iend
            if not text or event_end - event_start < 0.35:
                continue
            events.append({
                "start": round(seg["output_start"] + (event_start - seg["source_start"]), 3),
                "end": round(seg["output_start"] + (event_end - seg["source_start"]), 3),
                "source_start": round(event_start, 3),
                "source_end": round(event_end, 3),
                "text": text,
            })

    max_chars = int(style.get("max_line_chars", 18))
    max_lines = int(style.get("max_lines", 2))
    ratio = float(cleanup_cfg["max_subtitle_visual_width_ratio"])
    max_visual_width = max(8.0, max_chars * max_lines * ratio)
    min_seconds = float(cleanup_cfg["min_split_event_seconds"])

    cleaned_events = clean_subtitle_events(events, cleanup_cfg)
    planned_events = apply_subtitle_plan(cleaned_events, subtitle_plan, min_seconds)
    split_events: list[dict[str, Any]] = []
    for event in planned_events:
        if event.get("_planned"):
            split_events.append({key: value for key, value in event.items() if key != "_planned"})
        else:
            split_events.extend(split_event(event, max_visual_width, min_seconds))
    return clean_subtitle_events(split_events, cleanup_cfg)


def write_ass(path: Path, events: list[dict[str, Any]], style_name: str, style: dict[str, Any]) -> None:
    rounded_background = style.get("background_mode") == "rounded_vector"
    letter_spacing = float(style.get("letter_spacing_px", 0.0))
    lines = [
        "[Script Info]",
        "ScriptType: v4.00+",
        "PlayResX: 1920",
        "PlayResY: 1080",
        "ScaledBorderAndShadow: yes",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        (
            "Style: Default,"
            f"{style['font']},{style['font_size']},{style['primary_colour']},&H000000FF,"
            f"{style['outline_colour']},{style['back_colour']},{style['bold']},0,0,0,100,100,{letter_spacing:g},0,1,"
            f"{style['outline']},{style['shadow']},{style['alignment']},{style['margin_l']},"
            f"{style['margin_r']},{style['margin_v']},1"
        ),
        *([
            (
                "Style: CaptionBackground,"
                f"{style['font']},{style['font_size']},{style.get('background_colour', style['back_colour'])},"
                f"&H000000FF,{style.get('background_colour', style['back_colour'])},"
                f"{style.get('background_colour', style['back_colour'])},0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1"
            )
        ] if rounded_background else []),
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]
    max_chars = int(style.get("max_line_chars", 18))
    max_lines = int(style.get("max_lines", 2))
    for event in events:
        wrapped = wrap_text(event["text"], max_chars, max_lines)
        if rounded_background:
            layout = rounded_caption_layout(wrapped, style)
            drawing = rounded_rect_ass_path(
                layout["width"],
                layout["height"],
                layout["radius"],
            )
            lines.append(
                f"Dialogue: 0,{fmt_ass(event['start'])},{fmt_ass(event['end'])},"
                "CaptionBackground,,0,0,0,,"
                f"{{\\an7\\pos({layout['x']},{layout['y']})\\p1\\bord0\\shad0}}{drawing}{{\\p0}}"
            )
            center_y = layout["y"] + layout["height"] // 2
            lines.append(
                f"Dialogue: 1,{fmt_ass(event['start'])},{fmt_ass(event['end'])},"
                f"Default,,0,0,0,,{{\\an5\\pos(960,{center_y})}}{wrapped}"
            )
            continue
        lines.append(
            f"Dialogue: 0,{fmt_ass(event['start'])},{fmt_ass(event['end'])},"
            f"Default,,0,0,0,,{wrapped}"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_srt(path: Path, events: list[dict[str, Any]]) -> None:
    lines: list[str] = []
    for idx, event in enumerate(events, start=1):
        lines.extend([str(idx), f"{fmt_srt(event['start'])} --> {fmt_srt(event['end'])}", srt_text(event["text"]), ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def read_srt(path: Path) -> list[dict[str, Any]]:
    """Parse the SRT subset produced and consumed by this skill."""
    timestamp = re.compile(
        r"(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*-->\s*"
        r"(\d{2}):(\d{2}):(\d{2}),(\d{3})"
    )
    events: list[dict[str, Any]] = []
    for block in re.split(r"\r?\n\s*\r?\n", path.read_text(encoding="utf-8").strip()):
        block_lines = [line.strip() for line in block.splitlines()]
        if len(block_lines) < 3:
            continue
        match = timestamp.fullmatch(block_lines[1])
        if not match:
            continue
        values = [int(value) for value in match.groups()]
        start = values[0] * 3600 + values[1] * 60 + values[2] + values[3] / 1000.0
        end = values[4] * 3600 + values[5] * 60 + values[6] + values[7] / 1000.0
        text = "\n".join(line for line in block_lines[2:] if line).strip()
        if text and end > start:
            events.append({"start": start, "end": end, "text": text})
    if not events:
        raise SystemExit(f"No valid subtitle events found in SRT: {path}")
    return events


def write_filter_script(path: Path, segment_count: int, cover_duration: float, cover_mode: str) -> None:
    scale = "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:black,setsar=1,fps=30"
    lines = []
    if cover_mode == "intro":
        lines.extend([
            f"[1:v]{scale},trim=duration={cover_duration},setpts=PTS-STARTPTS[vcover];",
            f"anullsrc=channel_layout=mono:sample_rate=48000,atrim=duration={cover_duration},asetpts=PTS-STARTPTS[acover];",
        ])
    elif cover_mode == "first_frame":
        lines.append(f"[1:v]{scale},setpts=PTS-STARTPTS[vcover];")
    for idx in range(segment_count):
        lines.append(f"[0:v]trim=start=SEG{idx}_START:end=SEG{idx}_END,setpts=PTS-STARTPTS,{scale}[v{idx}];")
        lines.append(f"[0:a]atrim=start=SEG{idx}_START:end=SEG{idx}_END,asetpts=PTS-STARTPTS,aresample=48000[a{idx}];")

    if cover_mode == "intro":
        concat_inputs = "[vcover][acover]" + "".join(f"[v{i}][a{i}]" for i in range(segment_count))
        lines.append(f"{concat_inputs}concat=n={segment_count + 1}:v=1:a=1[vcat][acat];")
        lines.append("[vcat]ass=edited.ass[vout];")
    elif cover_mode == "first_frame":
        concat_inputs = "".join(f"[v{i}][a{i}]" for i in range(segment_count))
        lines.append(f"{concat_inputs}concat=n={segment_count}:v=1:a=1[vcat][acat];")
        lines.append("[vcat][vcover]overlay=enable='eq(n,0)':eof_action=pass[vcovered];")
        lines.append("[vcovered]ass=edited.ass[vout];")
    else:
        concat_inputs = "".join(f"[v{i}][a{i}]" for i in range(segment_count))
        lines.append(f"{concat_inputs}concat=n={segment_count}:v=1:a=1[vcat][acat];")
        lines.append("[vcat]ass=edited.ass[vout];")
    lines.append("[acat]anull[aout]")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def materialize_filter_template(template_path: Path, output_path: Path, segments: list[dict[str, Any]]) -> None:
    text = template_path.read_text(encoding="utf-8")
    for seg in segments:
        idx = seg["id"]
        text = text.replace(f"SEG{idx}_START", f"{seg['source_start']:.3f}")
        text = text.replace(f"SEG{idx}_END", f"{seg['source_end']:.3f}")
    output_path.write_text(text, encoding="utf-8")


def run(cmd: list[str], cwd: Path) -> None:
    print(" ".join(cmd))
    subprocess.run(cmd, cwd=str(cwd), check=True)


def run_spoken_audio_qc(
    video: Path,
    decisions: Path,
    transcript: Path,
    output_dir: Path,
    review: Path | None,
) -> dict[str, Any]:
    """Run the fail-closed pre-render spoken-audio audit serially."""
    command = [
        sys.executable,
        str(SKILL_DIR / "scripts" / "spoken_audio_qc.py"),
        "analyze",
        "--input", str(video.resolve()),
        "--timeline", str(decisions.resolve()),
        "--transcript", str(transcript.resolve()),
        "--stage", "pre-render",
        "--output-dir", str(output_dir.resolve()),
    ]
    if review:
        command.extend(["--review", str(review.resolve())])
    print(" ".join(command))
    subprocess.run(command, check=True)
    audit_path = output_dir / "audio-qc.json"
    if not audit_path.exists():
        raise SystemExit(f"音轨质检没有生成结构化报告：{audit_path}")
    return json.loads(audit_path.read_text(encoding="utf-8"))


def attach_cover_metadata(content_video: Path, cover: Path, output: Path, cwd: Path) -> None:
    """Embed cover art as an MP4 attached picture stream without changing frames."""
    run([
        "ffmpeg", "-y", "-hide_banner", "-v", "error", "-stats",
        "-i", str(content_video.name),
        "-i", str(cover.name),
        "-map", "0", "-map", "1",
        "-c", "copy", "-c:v:1", "png",
        "-disposition:v:1", "attached_pic",
        "-metadata:s:v:1", "title=cover",
        "-metadata:s:v:1", "comment=Cover (front)",
        "-movflags", "+faststart",
        str(output.name),
    ], cwd=cwd)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", type=Path)
    parser.add_argument("--cover", type=Path)
    parser.add_argument("--transcript", type=Path)
    parser.add_argument("--silence-log", type=Path)
    parser.add_argument("--work-dir", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--srt-input", type=Path, help="Convert an existing SRT through the canonical subtitle renderer.")
    parser.add_argument("--ass-output", type=Path, help="ASS destination used with --srt-input.")
    parser.add_argument("--window", action="append", type=parse_time_pair)
    parser.add_argument("--segments-from-decisions", type=Path, help="Reuse exact source segments from a prior edit_decisions.json when only repackaging or rerendering.")
    parser.add_argument("--style")
    parser.add_argument("--subtitle-plan", type=Path, help="Agent-authored per-video semantic subtitle split and cleanup plan.")
    parser.add_argument("--mode", default="standard")
    parser.add_argument("--cover-mode", choices=["metadata", "first_frame", "intro"], default="metadata")
    parser.add_argument("--cover-duration", type=float, default=0.0)
    parser.add_argument(
        "--video-encoder",
        default="h264_videotoolbox" if sys.platform == "darwin" else "libx264",
        help="ffmpeg 视频编码器。macOS 默认 h264_videotoolbox，其他系统默认 libx264。",
    )
    parser.add_argument("--video-bitrate", default="8000k")
    parser.add_argument("--audio-bitrate", default="160k")
    parser.add_argument("--allow-hidden-speech", action="store_true", help="Write hidden speech audit but do not block rendering.")
    parser.add_argument("--audio-qc-review", type=Path, help="人工复听后的 spoken-audio-qc review JSON。")
    parser.add_argument("--audio-qc-check-dir", type=Path, help="音轨波形报告输出目录，默认 <work-dir>/checks/spoken-audio-qc。")
    parser.add_argument("--allow-unverified-audio-qc", action="store_true", help="显式接受未完成音轨质检的风险；交付时必须披露。")
    parser.add_argument("--skip-render", action="store_true")
    args = parser.parse_args()

    style_name, style = load_style(SKILL_DIR / "data" / "subtitle_styles.yaml", args.style)
    if args.srt_input:
        if not args.ass_output:
            parser.error("--ass-output is required with --srt-input")
        args.ass_output.parent.mkdir(parents=True, exist_ok=True)
        events = read_srt(args.srt_input)
        write_ass(args.ass_output, events, style_name, style)
        print(json.dumps({
            "status": "ok",
            "mode": "srt_to_ass",
            "style": style_name,
            "subtitle_events": len(events),
            "output": str(args.ass_output),
        }, ensure_ascii=False))
        return

    missing = [
        flag for flag, value in (
            ("--video", args.video),
            ("--transcript", args.transcript),
            ("--work-dir", args.work_dir),
            ("--output", args.output),
        ) if value is None
    ]
    if missing:
        parser.error(f"normal render mode requires: {', '.join(missing)}")

    if args.cover_mode in {"first_frame", "intro"} and not args.cover:
        parser.error("--cover is required when --cover-mode is first_frame or intro")

    args.work_dir.mkdir(parents=True, exist_ok=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)

    transcript = json.loads(args.transcript.read_text(encoding="utf-8"))
    subtitle_plan = load_subtitle_plan(args.subtitle_plan)
    replacements = (
        load_replacements(SKILL_DIR / "data" / "corrections.yaml")
        + load_replacements(SKILL_DIR / "data" / "filler_rules.yaml")
        + plan_replacements(subtitle_plan)
    )
    silence_cfg = load_silence_config(SKILL_DIR / "data" / "filler_rules.yaml")
    cleanup_cfg = load_subtitle_cleanup_config(SKILL_DIR / "data" / "filler_rules.yaml")
    consistency_cfg = load_consistency_config(SKILL_DIR / "data" / "filler_rules.yaml")
    boundary_silence_cfg = load_boundary_silence_config(SKILL_DIR / "data" / "filler_rules.yaml")
    boundary_guard_cfg = load_word_boundary_guard_config(SKILL_DIR / "data" / "filler_rules.yaml")
    silences = parse_silence_log(args.silence_log)
    transcript_words = collect_transcript_words(transcript)
    timeline_cover_duration = args.cover_duration if args.cover_mode == "intro" else 0.0
    auto_boundary_silence_cuts: list[dict[str, Any]] = []
    boundary_guard_adjustments: list[dict[str, Any]] = []
    previous_decisions: dict[str, Any] | None = None
    if args.segments_from_decisions:
        segments, previous_decisions = load_segments_from_decisions(args.segments_from_decisions, timeline_cover_duration)
        word_cut_ranges = previous_decisions.get("word_cut_ranges", [])
        auto_boundary_silence_cuts = previous_decisions.get("auto_boundary_silence_cuts", [])
        boundary_guard_adjustments = previous_decisions.get("word_boundary_guard_adjustments", [])
    else:
        if not args.window:
            parser.error("--window is required unless --segments-from-decisions is provided")
        base_segments = build_keep_segments(args.window, silences, silence_cfg, timeline_cover_duration)
        base_segments, boundary_guard_adjustments = apply_word_boundary_guard(
            base_segments,
            transcript_words,
            boundary_guard_cfg,
            float(transcript["duration"]) if transcript.get("duration") is not None else None,
            timeline_cover_duration,
        )
        word_cut_ranges = plan_word_cut_ranges(subtitle_plan)
        segments = apply_source_cuts(base_segments, word_cut_ranges, timeline_cover_duration)
        for _ in range(int(boundary_silence_cfg.get("max_passes", 2))):
            previous_ranges = merge_cut_ranges(word_cut_ranges)
            new_cuts = plan_boundary_silence_cuts(transcript_words, segments, boundary_silence_cfg)
            combined = merge_cut_ranges(previous_ranges + new_cuts)
            if json.dumps(combined, sort_keys=True, ensure_ascii=False) == json.dumps(previous_ranges, sort_keys=True, ensure_ascii=False):
                break
            auto_boundary_silence_cuts = [
                item for item in combined
                if str(item.get("reason", "")).startswith("自动清理片段")
                or "自动清理片段" in str(item.get("reason", ""))
            ]
            word_cut_ranges = combined
            segments = apply_source_cuts(base_segments, word_cut_ranges, timeline_cover_duration)
    events = build_subtitles(transcript, segments, replacements, style, cleanup_cfg, subtitle_plan)

    ass_path = args.work_dir / "edited.ass"
    srt_path = args.work_dir / "edited.srt"
    decisions_path = args.work_dir / "edit_decisions.json"
    review_path = args.work_dir / "review_draft.md"
    hidden_review_json_path = args.work_dir / "hidden_speech_review.json"
    hidden_review_md_path = args.work_dir / "hidden_speech_review.md"
    filter_template = args.work_dir / "render_filter_template.txt"
    filter_path = args.work_dir / "render_filter.txt"

    write_ass(ass_path, events, style_name, style)
    write_srt(srt_path, events)
    write_filter_script(filter_template, len(segments), timeline_cover_duration, args.cover_mode)
    materialize_filter_template(filter_template, filter_path, segments)
    hidden_speech_audit = audit_subtitle_audio_consistency(transcript, segments, events, consistency_cfg)
    write_hidden_speech_review(hidden_review_json_path, hidden_review_md_path, hidden_speech_audit)

    total_duration = timeline_cover_duration + sum(seg["duration"] for seg in segments)
    decisions = {
        "video": str(args.video),
        "cover": str(args.cover) if args.cover else None,
        "transcript": str(args.transcript),
        "mode": args.mode,
        "cover_mode": args.cover_mode,
        "style": style_name,
        "subtitle_plan": str(args.subtitle_plan) if args.subtitle_plan else None,
        "segments_from_decisions": str(args.segments_from_decisions) if args.segments_from_decisions else None,
        "word_cut_ranges": word_cut_ranges,
        "auto_boundary_silence_cuts": auto_boundary_silence_cuts,
        "word_boundary_guard_adjustments": boundary_guard_adjustments,
        "cover_duration": timeline_cover_duration,
        "original_duration": transcript.get("duration"),
        "edited_duration": round(total_duration, 3),
        "segments": segments,
        "subtitle_events": len(events),
        "hidden_speech_review": str(hidden_review_json_path),
        "hidden_speech_issues": len(hidden_speech_audit.get("issues", [])),
    }
    decisions_path.write_text(json.dumps(decisions, ensure_ascii=False, indent=2), encoding="utf-8")

    keep_rows = "\n".join(
        f"| {seg['id'] + 1} | {seg['source_start']:.2f}-{seg['source_end']:.2f} | "
        f"{seg['output_start']:.2f}-{seg['output_end']:.2f} | {seg['reason']} |"
        for seg in segments
    )
    review_template = (SKILL_DIR / "templates" / "review_draft.md").read_text(encoding="utf-8")
    review = (
        review_template
        .replace("{{video}}", str(args.video))
        .replace("{{mode}}", args.mode)
        .replace("{{original_duration}}", str(transcript.get("duration", "")))
        .replace("{{proposed_duration}}", f"{total_duration:.2f}")
        .replace("{{cover_duration}}", str(timeline_cover_duration))
        .replace("{{subtitle_style}}", style_name)
        .replace("{{keep_rows}}", keep_rows)
        .replace("{{delete_rows}}", "| auto | 按窗口/停顿规则压缩 | 见 edit_decisions.json | medium |")
    )
    review_path.write_text(review, encoding="utf-8")

    if (
        consistency_cfg.get("block_on_hidden_speech", True)
        and hidden_speech_audit.get("issues")
        and not args.allow_hidden_speech
    ):
        raise SystemExit(
            "最终字幕隐藏了仍保留在音视频里的真实口播。"
            f"请检查 {hidden_review_md_path} 并补充 word_cut_ranges；或在人工确认后使用 --allow-hidden-speech 继续。"
        )

    if args.skip_render:
        return

    audio_qc_required = args.mode in {"standard", "aggressive"}
    if audio_qc_required or args.audio_qc_review:
        audio_qc_dir = args.audio_qc_check_dir or (args.work_dir / "checks" / "spoken-audio-qc")
        audio_qc = run_spoken_audio_qc(
            args.video,
            decisions_path,
            args.transcript,
            audio_qc_dir,
            args.audio_qc_review,
        )
        audio_qc_status = str(audio_qc.get("gate", {}).get("status", "invalid"))
        if audio_qc_status != "pass" and not args.allow_unverified_audio_qc:
            raise SystemExit(
                "口播音轨质检未通过，已停止渲染。"
                f"状态={audio_qc_status}；请打开 {audio_qc_dir / 'waveform-report.html'}，"
                f"填写 {audio_qc_dir / 'review-template.json'} 后用 --audio-qc-review 重试。"
            )

    render_output = args.work_dir / f"{args.output.stem}.content.mp4" if args.cover_mode == "metadata" and args.cover else args.output
    ffmpeg_cmd = [
        "ffmpeg", "-y", "-hide_banner", "-v", "error", "-stats",
        "-i", str(args.video.resolve()),
    ]
    if args.cover_mode in {"intro", "first_frame"}:
        ffmpeg_cmd.extend([
            "-loop", "1", "-t", str(max(1 / 30, timeline_cover_duration if args.cover_mode == "intro" else 1.0)), "-i", str(args.cover.resolve()),
        ])
    ffmpeg_cmd.extend([
        "-filter_complex_script", str(filter_path.name),
        "-map", "[vout]", "-map", "[aout]",
        "-c:v", args.video_encoder, "-b:v", args.video_bitrate,
        "-maxrate", "10000k", "-bufsize", "16000k", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", args.audio_bitrate, "-movflags", "+faststart",
        str(render_output.name),
    ])
    run(ffmpeg_cmd, cwd=args.work_dir)

    if args.cover_mode == "metadata" and args.cover:
        attach_cover_metadata(render_output, args.cover, args.output, args.work_dir)
        run([
            "ffmpeg", "-y", "-hide_banner", "-v", "error",
            "-i", str(args.output.name), "-map", "0:v:1", "-frames:v", "1",
            "check_cover_attachment.png",
        ], cwd=args.work_dir)

    run(["ffmpeg", "-y", "-hide_banner", "-v", "error", "-i", str(args.output.name), "-map", "0:v:0", "-frames:v", "1", "check_first_frame.png"], cwd=args.work_dir)
    run(["ffmpeg", "-y", "-hide_banner", "-v", "error", "-ss", "4", "-i", str(args.output.name), "-map", "0:v:0", "-frames:v", "1", "check_subtitle_frame.png"], cwd=args.work_dir)


if __name__ == "__main__":
    main()
