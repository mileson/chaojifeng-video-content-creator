#!/usr/bin/env python3
"""口播剪口音轨质检（渲染前门禁）。

用法：
    python3 scripts/spoken_audio_qc.py analyze \\
        --input <原视频> \\
        --timeline <edit_decisions.json> \\
        --transcript <transcript.json> \\
        --stage pre-render \\
        --output-dir <输出目录> \\
        [--review <人工复听后的 review.json>]

做什么：
  1. 用 ffmpeg 把原视频的音轨解码为 16kHz 单声道 PCM。
  2. 对 edit_decisions.json 里的每个剪口（相邻保留片段的接缝）计算 10ms 步长的 RMS 包络。
  3. 标出两类需要人工复听的剪口：
       - 接缝落在发声中：保留片段的尾部或头部仍有语音能量，可能切掉了半个字；
       - 接缝处留下过长的静音：剪口两侧残留的静音加起来超过停顿预算。
  4. 输出 audio-qc.json、waveform-report.html（每个剪口一张包络图）和 review-template.json。
  5. 门禁：没有被标出的剪口直接通过；否则必须传入复听后的 review JSON，
     被标出的每一项都标为 ok，才算 pass；任何一项标为 fix 即 fail。

阈值读取自 data/filler_rules.yaml 的 waveform_verification、pause_budget 与 pre_render_cut_audit，读不到时使用默认值。
依赖：Python 3 标准库与 ffmpeg。
"""

from __future__ import annotations

import argparse
import html
import json
import math
import subprocess
import sys
from array import array
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SKILL_DIR = Path(__file__).resolve().parent.parent
SAMPLE_RATE = 16000
EDGE_WINDOW_SECONDS = 0.03
LOOKBACK_SECONDS = 3.0
REPORT_HALF_WIDTH_SECONDS = 0.8

DEFAULTS = {
    "rms_hop_seconds": 0.01,
    "speech_onset_rms": 0.02,
    "speech_gap_trim_above_seconds": 0.50,
    "window_seconds": 0.30,
    "peak_rms_review_threshold": 0.10,
}


def parse_number(text: str) -> float | None:
    token = text.split("#", 1)[0].strip().strip("\"'")
    try:
        return float(token)
    except ValueError:
        return None


def load_thresholds(path: Path) -> dict[str, float]:
    """从轻量 YAML 里读取 waveform_verification、pause_budget 与 pre_render_cut_audit 下的数值。"""
    values = dict(DEFAULTS)
    if not path.exists():
        return values
    section: str | None = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if not raw.startswith(" "):
            section = stripped[:-1] if stripped.endswith(":") else None
            continue
        if section in {"waveform_verification", "pause_budget", "pre_render_cut_audit"} and ":" in stripped:
            key, value = stripped.split(":", 1)
            key = key.strip()
            if key in values:
                number = parse_number(value)
                if number is not None:
                    values[key] = number
    return values


def decode_pcm(video: Path) -> array:
    command = [
        "ffmpeg", "-v", "error", "-i", str(video),
        "-vn", "-ac", "1", "-ar", str(SAMPLE_RATE), "-f", "s16le", "-",
    ]
    try:
        proc = subprocess.run(command, capture_output=True, check=False)
    except FileNotFoundError:
        raise SystemExit("找不到 ffmpeg。请先安装 ffmpeg，并确认它在 PATH 中。")
    if proc.returncode != 0:
        raise SystemExit(f"ffmpeg 解码音轨失败：{proc.stderr.decode('utf-8', 'replace')[:400]}")
    samples = array("h")
    samples.frombytes(proc.stdout[: len(proc.stdout) // 2 * 2])
    if sys.byteorder == "big":
        samples.byteswap()
    return samples


def rms(samples: array, start: float, end: float) -> float:
    first = max(0, int(start * SAMPLE_RATE))
    last = min(len(samples), int(end * SAMPLE_RATE))
    if last <= first:
        return 0.0
    total = 0
    for value in samples[first:last]:
        total += value * value
    return math.sqrt(total / (last - first)) / 32768.0


def envelope(samples: array, start: float, end: float, hop: float) -> list[tuple[float, float]]:
    points: list[tuple[float, float]] = []
    cursor = max(0.0, start)
    while cursor < end:
        points.append((round(cursor, 3), rms(samples, cursor, cursor + hop)))
        cursor += hop
    return points


def tail_pause(samples: array, end: float, onset: float, hop: float) -> float:
    """从 end 往回找最近一个有语音能量的窗口，返回保留片段尾部的静音长度。"""
    cursor = end
    limit = max(0.0, end - LOOKBACK_SECONDS)
    while cursor - hop >= limit:
        if rms(samples, cursor - hop, cursor) >= onset:
            return round(end - cursor, 3)
        cursor -= hop
    return round(end - limit, 3)


def head_pause(samples: array, start: float, onset: float, hop: float, total: float) -> float:
    """从 start 往后找第一个有语音能量的窗口，返回保留片段头部的静音长度。"""
    cursor = start
    limit = min(total, start + LOOKBACK_SECONDS)
    while cursor + hop <= limit:
        if rms(samples, cursor, cursor + hop) >= onset:
            return round(cursor - start, 3)
        cursor += hop
    return round(limit - start, 3)


def measure_cut(index: int, previous: dict[str, Any], following: dict[str, Any], samples: array,
                cfg: dict[str, float]) -> dict[str, Any]:
    hop = cfg["rms_hop_seconds"]
    onset = cfg["speech_onset_rms"]
    trim_above = cfg["speech_gap_trim_above_seconds"]
    total = len(samples) / SAMPLE_RATE
    prev_end = float(previous["source_end"])
    next_start = float(following["source_start"])

    tail_rms = rms(samples, prev_end - EDGE_WINDOW_SECONDS, prev_end)
    head_rms = rms(samples, next_start, next_start + EDGE_WINDOW_SECONDS)
    window = cfg["window_seconds"]
    tail_peak = max((v for _, v in envelope(samples, prev_end - window, prev_end, hop)), default=0.0)
    head_peak = max((v for _, v in envelope(samples, next_start, next_start + window, hop)), default=0.0)
    tail_gap = tail_pause(samples, prev_end, onset, hop)
    head_gap = head_pause(samples, next_start, onset, hop, total)
    join_pause = round(tail_gap + head_gap, 3)

    flags: list[str] = []
    if tail_rms >= onset:
        flags.append("tail_cuts_speech")
    if head_rms >= onset:
        flags.append("head_cuts_speech")
    if join_pause > trim_above:
        flags.append("long_join_pause")

    return {
        "id": f"cut-{index:03d}",
        "output_time": round(float(previous.get("output_end", 0.0)), 3),
        "source_prev_end": round(prev_end, 3),
        "source_next_start": round(next_start, 3),
        "tail_rms": round(tail_rms, 4),
        "head_rms": round(head_rms, 4),
        "tail_peak_rms": round(tail_peak, 4),
        "head_peak_rms": round(head_peak, 4),
        "high_energy_at_edge": max(tail_rms, head_rms) > cfg["peak_rms_review_threshold"],
        "tail_pause_seconds": tail_gap,
        "head_pause_seconds": head_gap,
        "join_pause_seconds": join_pause,
        "flags": flags,
    }


FLAG_TEXT = {
    "tail_cuts_speech": "保留片段尾部仍有语音能量，可能切掉了字尾",
    "head_cuts_speech": "保留片段头部一开始就有语音能量，可能切掉了字头",
    "long_join_pause": "接缝两侧残留的静音超过停顿预算，可以再收紧",
}


def svg_for_cut(samples: array, cut: dict[str, Any], cfg: dict[str, float]) -> str:
    hop = cfg["rms_hop_seconds"]
    onset = cfg["speech_onset_rms"]
    tail = envelope(samples, cut["source_prev_end"] - REPORT_HALF_WIDTH_SECONDS, cut["source_prev_end"], hop)
    head = envelope(samples, cut["source_next_start"], cut["source_next_start"] + REPORT_HALF_WIDTH_SECONDS, hop)
    series = [value for _, value in tail] + [value for _, value in head]
    if not series:
        return ""
    width, height = 640, 120
    peak = max(max(series), onset * 2, 0.05)
    step = width / len(series)

    def point(i: int, value: float) -> str:
        return f"{i * step:.1f},{height - min(1.0, value / peak) * (height - 6) - 3:.1f}"

    line = " ".join(point(i, value) for i, value in enumerate(series))
    join_x = len(tail) * step
    onset_y = height - min(1.0, onset / peak) * (height - 6) - 3
    return (
        f'<svg viewBox="0 0 {width} {height}" width="{width}" height="{height}" role="img">'
        f'<rect width="{width}" height="{height}" fill="#0f1623"/>'
        f'<line x1="0" y1="{onset_y:.1f}" x2="{width}" y2="{onset_y:.1f}" stroke="#4dd0e1" stroke-dasharray="4 4" stroke-width="1"/>'
        f'<polyline points="{line}" fill="none" stroke="#ffb224" stroke-width="1.6"/>'
        f'<line x1="{join_x:.1f}" y1="0" x2="{join_x:.1f}" y2="{height}" stroke="#ff6b6b" stroke-width="2"/>'
        f"</svg>"
    )


def write_report(path: Path, audit: dict[str, Any], samples: array, cfg: dict[str, float]) -> None:
    sections: list[str] = []
    for cut in audit["cuts"]:
        flagged = bool(cut["flags"])
        reasons = "；".join(FLAG_TEXT[flag] for flag in cut["flags"]) or "未发现风险"
        sections.append(
            f'<section class="{"flag" if flagged else "ok"}">'
            f'<h2>{html.escape(cut["id"])} · 成片 {cut["output_time"]:.2f}s</h2>'
            f'<p>{html.escape(reasons)}</p>'
            f'<p class="meta">原片 {cut["source_prev_end"]:.2f}s → {cut["source_next_start"]:.2f}s；'
            f'尾部静音 {cut["tail_pause_seconds"]:.2f}s，头部静音 {cut["head_pause_seconds"]:.2f}s，'
            f'接缝静音合计 {cut["join_pause_seconds"]:.2f}s；'
            f'前后 {cfg["window_seconds"]:.1f}s 峰值 RMS {cut["tail_peak_rms"]:.3f} / {cut["head_peak_rms"]:.3f}'
            f'{"（接缝紧邻高能量）" if cut["high_energy_at_edge"] else ""}</p>'
            f'{svg_for_cut(samples, cut, cfg)}'
            f"</section>"
        )
    body = "\n".join(sections) or "<p>没有剪口。</p>"
    gate = audit["gate"]
    page = f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><title>剪口音轨质检</title>
<style>
body {{ font: 15px/1.6 -apple-system, "PingFang SC", sans-serif; background:#0b111e; color:#dfe6f3; margin:0; padding:32px; }}
h1 {{ margin:0 0 8px; }} h2 {{ margin:0 0 4px; font-size:18px; }}
section {{ background:#141c2c; border:1px solid #243049; border-radius:12px; padding:16px 20px; margin:16px 0; }}
section.flag {{ border-color:#ffb224; }}
.meta {{ color:#8f9bb3; margin:4px 0 12px; }}
.legend {{ color:#8f9bb3; }}
</style></head><body>
<h1>剪口音轨质检</h1>
<p>门禁状态：<b>{html.escape(gate["status"])}</b>。{html.escape(gate["summary"])}</p>
<p class="legend">橙色折线是 RMS 包络，红线是剪口位置，青色虚线是起音阈值 {cfg["speech_onset_rms"]}。左侧为保留片段的尾部，右侧为下一个保留片段的头部，各 {REPORT_HALF_WIDTH_SECONDS} 秒。</p>
{body}
</body></html>
"""
    path.write_text(page, encoding="utf-8")


def evaluate_gate(cuts: list[dict[str, Any]], review: dict[str, Any] | None) -> dict[str, Any]:
    flagged = [cut for cut in cuts if cut["flags"]]
    if not cuts:
        return {"status": "pass", "summary": "时间轴没有剪口。", "pending": [], "rejected": []}
    if not flagged:
        return {"status": "pass", "summary": f"{len(cuts)} 个剪口都没有被标出风险。", "pending": [], "rejected": []}

    verdicts: dict[str, str] = {}
    if review:
        for item in review.get("items", []):
            verdicts[str(item.get("id"))] = str(item.get("verdict", "")).strip().lower()
    rejected = [cut["id"] for cut in flagged if verdicts.get(cut["id"]) in {"fix", "fail", "reject", "rejected"}]
    pending = [cut["id"] for cut in flagged if verdicts.get(cut["id"]) not in {"ok", "accepted"} and cut["id"] not in rejected]
    if rejected:
        return {"status": "fail", "summary": f"{len(rejected)} 个剪口被复听为需要调整。", "pending": pending, "rejected": rejected}
    if pending:
        return {"status": "needs_review", "summary": f"{len(pending)} 个被标出的剪口等待人工复听。", "pending": pending, "rejected": []}
    return {"status": "pass", "summary": f"{len(flagged)} 个被标出的剪口都已人工复听确认。", "pending": [], "rejected": []}


def analyze(args: argparse.Namespace) -> int:
    timeline = json.loads(args.timeline.read_text(encoding="utf-8"))
    segments = timeline.get("segments", [])
    cfg = load_thresholds(SKILL_DIR / "data" / "filler_rules.yaml")
    samples = decode_pcm(args.input)

    cuts = [
        measure_cut(i + 1, segments[i], segments[i + 1], samples, cfg)
        for i in range(len(segments) - 1)
    ]
    review = json.loads(args.review.read_text(encoding="utf-8")) if args.review else None
    gate = evaluate_gate(cuts, review)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    audit = {
        "stage": args.stage,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "input": str(args.input),
        "timeline": str(args.timeline),
        "transcript": str(args.transcript) if args.transcript else None,
        "thresholds": cfg,
        "cut_count": len(cuts),
        "flagged_count": sum(1 for cut in cuts if cut["flags"]),
        "cuts": cuts,
        "gate": gate,
    }
    (args.output_dir / "audio-qc.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(args.output_dir / "waveform-report.html", audit, samples, cfg)

    template = {
        "stage": args.stage,
        "instructions": "逐项复听剪口前后各 1 秒。可以接受填 ok；需要调整 word_cut_ranges 填 fix，并在 note 写原因。",
        "items": [
            {"id": cut["id"], "output_time": cut["output_time"], "flags": cut["flags"], "verdict": "", "note": ""}
            for cut in cuts if cut["flags"]
        ],
    }
    (args.output_dir / "review-template.json").write_text(json.dumps(template, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps({
        "status": gate["status"],
        "cuts": len(cuts),
        "flagged": audit["flagged_count"],
        "report": str(args.output_dir / "waveform-report.html"),
    }, ensure_ascii=False))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="口播剪口音轨质检（渲染前门禁）。")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("analyze", help="分析剪口并输出报告与门禁状态")
    p.add_argument("--input", type=Path, required=True, help="原视频或原音频")
    p.add_argument("--timeline", type=Path, required=True, help="edit_decisions.json")
    p.add_argument("--transcript", type=Path, help="转写 JSON，仅记录在报告里")
    p.add_argument("--stage", default="pre-render", help="检查阶段标签，默认 pre-render")
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--review", type=Path, help="人工复听后的 review JSON")
    p.set_defaults(func=analyze)
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
