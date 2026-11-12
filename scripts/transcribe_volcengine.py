#!/usr/bin/env python3
"""Submit audio to Volcengine/Doubao ASR and normalize the result.

The API key is read from environment variables (see .env.example). It is never
stored in skill files or printed.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import subprocess
import sys
import time
import uuid
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent


def resolve_api_key() -> str:
    for name in ("VOLCENGINE_API_KEY", "VOLCENGINE_ARK_API_KEY", "ARK_API_KEY"):
        value = os.environ.get(name)
        if value:
            return value
    raise SystemExit(
        "Missing API key. Export VOLCENGINE_API_KEY in your shell "
        "(see .env.example), then run this script again."
    )


def request_json(
    method: str,
    url: str,
    api_key: str,
    body: dict[str, Any] | None = None,
    *,
    auth_style: str = "x-api-key",
    timeout: float = 30.0,
    extra_headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    payload = None if body is None else json.dumps(body, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(url, data=payload, method=method)
    request.add_header("Accept", "*/*")
    request.add_header("Connection", "keep-alive")
    if auth_style == "x-api-key":
        request.add_header("x-api-key", api_key)
    elif auth_style == "volcengine-bigmodel":
        request.add_header("X-Api-Key", api_key)
        request.add_header("X-Api-Resource-Id", "volc.bigasr.auc_turbo")
        request.add_header("X-Api-Request-Id", str(uuid.uuid4()))
        request.add_header("X-Api-Sequence", "-1")
    else:
        raise ValueError(f"unknown auth style: {auth_style}")
    for key, value in (extra_headers or {}).items():
        request.add_header(key, value)
    if payload is not None:
        request.add_header("content-type", "application/json")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"Volcengine HTTP {exc.code}: {detail}") from exc


def load_hotwords(path: Path | None) -> list[str]:
    if not path or not path.exists():
        return []
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def submit_url(args: argparse.Namespace, api_key: str) -> str:
    query = urllib.parse.urlencode({
        "language": args.language,
        "use_itn": str(args.use_itn),
        "use_capitalize": str(args.use_capitalize),
        "max_lines": args.max_lines,
        "words_per_line": args.words_per_line,
    })
    body: dict[str, Any] = {"url": args.audio_url}
    hotwords = load_hotwords(args.hotwords)
    if hotwords:
        body["hot_words"] = hotwords
    response = request_json("POST", f"{args.submit_url}?{query}", api_key, body)
    task_id = response.get("id")
    if not task_id:
        raise SystemExit(f"Submit failed: {json.dumps(response, ensure_ascii=False)}")
    return str(task_id)


def audio_format(path: Path) -> str:
    suffix = path.suffix.lower().lstrip(".")
    if suffix in {"wav", "mp3", "ogg"}:
        return suffix
    if suffix == "opus":
        return "ogg"
    return "wav"


def recognize_bigmodel_flash(args: argparse.Namespace, api_key: str) -> dict[str, Any]:
    if not args.audio_file and not args.audio_url:
        raise SystemExit("bigmodel-flash requires --audio-file or --audio-url")
    audio: dict[str, Any]
    if args.audio_file:
        data = base64.b64encode(args.audio_file.read_bytes()).decode("ascii")
        audio = {"data": data, "format": audio_format(args.audio_file)}
    else:
        audio = {"url": args.audio_url, "format": audio_format(Path(urllib.parse.urlparse(args.audio_url).path))}
    audio["language"] = args.language
    body = {
        "user": {"uid": args.uid},
        "audio": audio,
        "request": {
            "model_name": "bigmodel",
            "enable_itn": args.enable_itn,
            "show_utterances": True,
        },
    }
    response = request_json(
        "POST",
        args.flash_url,
        api_key,
        body,
        auth_style="volcengine-bigmodel",
        timeout=args.request_timeout,
    )
    status_code = response.get("code")
    if status_code not in (None, 0, "0", 20000000, "20000000"):
        raise SystemExit(f"Bigmodel flash failed: {json.dumps(response, ensure_ascii=False)}")
    return response


def poll_result(args: argparse.Namespace, api_key: str, task_id: str) -> dict[str, Any]:
    query_url = f"{args.query_url}?{urllib.parse.urlencode({'id': task_id})}"
    attempts = max(1, int(args.timeout / args.poll_interval))
    for _ in range(attempts):
        time.sleep(args.poll_interval)
        response = request_json("GET", query_url, api_key)
        code = response.get("code")
        if code == 0:
            return response
        if code == 1000:
            print(".", end="", flush=True)
            continue
        raise SystemExit(f"Transcription failed: {json.dumps(response, ensure_ascii=False)}")
    raise SystemExit("Transcription timed out before completion.")


def normalize(raw_path: Path, output_path: Path, provider: str) -> None:
    subprocess.run(
        [
            sys.executable,
            str(SCRIPT_DIR / "normalize_asr_result.py"),
            "--input",
            str(raw_path),
            "--output",
            str(output_path),
            "--provider",
            provider,
        ],
        check=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", choices=["vc-url", "bigmodel-flash"], default="bigmodel-flash")
    parser.add_argument("--audio-url", help="Publicly reachable audio URL.")
    parser.add_argument("--audio-file", type=Path, help="Local audio file. Supported by bigmodel-flash via base64.")
    parser.add_argument("--raw-output", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--hotwords", type=Path)
    parser.add_argument("--submit-url", default="https://openspeech.bytedance.com/api/v1/vc/submit")
    parser.add_argument("--query-url", default="https://openspeech.bytedance.com/api/v1/vc/query")
    parser.add_argument("--language", default="zh-CN")
    parser.add_argument("--use-itn", default=True)
    parser.add_argument("--use-capitalize", default=True)
    parser.add_argument("--max-lines", default=1, type=int)
    parser.add_argument("--words-per-line", default=15, type=int)
    parser.add_argument("--flash-url", default="https://openspeech.bytedance.com/api/v3/auc/bigmodel/recognize/flash")
    parser.add_argument("--uid", default="chaojifeng-video-content-creator")
    parser.add_argument("--enable-itn", default=True)
    parser.add_argument("--request-timeout", default=900.0, type=float)
    parser.add_argument("--poll-interval", default=5.0, type=float)
    parser.add_argument("--timeout", default=600.0, type=float)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    args.raw_output.parent.mkdir(parents=True, exist_ok=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.dry_run:
        print(f"ready: provider={args.provider} output paths are configured")
        return

    api_key = resolve_api_key()
    if args.provider == "bigmodel-flash":
        print("recognizing with volcengine bigmodel flash")
        result = recognize_bigmodel_flash(args, api_key)
        provider = "volcengine_bigmodel_flash"
    else:
        if not args.audio_url:
            raise SystemExit("vc-url requires --audio-url")
        task_id = submit_url(args, api_key)
        print(f"submitted task: {task_id}")
        result = poll_result(args, api_key, task_id)
        print()
        provider = "volcengine_vc"
    args.raw_output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    normalize(args.raw_output, args.output, provider)


if __name__ == "__main__":
    main()

