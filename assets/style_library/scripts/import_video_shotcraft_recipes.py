#!/usr/bin/env python3
# ## 核心功能
# 把 video-shotcraft 的公开 Gallery 数据规范化为本地统一配方库，并生成 file:// 可读取的 JS 快照。
# ## 输入
# 上游 library.json、Apache-2.0 LICENSE、固定 Git commit 与目标输出目录。
# ## 输出
# source-library.json、recipes.json、recipes.js、LICENSE 与 SOURCE.md。
# ## 定位
# chaojifeng-video-content-creator 特效库的外部 Remotion 配方导入器；不修改原生 registry/snippets。
# ## 依赖
# 仅使用 Python 标准库；网络模式读取 GitHub Pages 与 raw.githubusercontent.com。
# ## 维护规则
# 上游版本、字段映射或输出契约变化时同步更新本文件及 scripts/EffectsLibrary_scripts_README.md。

"""Import a pinned video-shotcraft snapshot as normalized Remotion recipes."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


UPSTREAM_OWNER = "Vincentwei1021"
UPSTREAM_REPO = "video-shotcraft"
DEFAULT_COMMIT = "0d6f0b57f0d4d6700761644c07f7ef03c3e50234"
LIBRARY_URL = "https://vincentwei1021.github.io/video-shotcraft/api/library.json"
GALLERY_BASE_URL = "https://vincentwei1021.github.io/video-shotcraft/"


def read_bytes(source: str) -> bytes:
    """Read bytes from a local path or HTTPS URL."""
    if source.startswith(("https://", "http://")):
        request = urllib.request.Request(source, headers={"User-Agent": "chaojifeng-video-content-creator-recipe-importer/1.0"})
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.read()
    return Path(source).read_bytes()


def normalize_library(raw: dict, commit: str) -> dict:
    """Convert upstream cards into the unified recipe-card contract."""
    cards = raw.get("cards")
    if not isinstance(cards, list):
        raise ValueError("上游 library.json 缺少 cards 数组")

    recipes: list[dict] = []
    style_ids: set[str] = set()
    for card in cards:
        card_id = card.get("name")
        styles = card.get("styles")
        if not card_id or not isinstance(styles, list) or not styles:
            raise ValueError(f"配方记录不完整: {card_id or '<missing-name>'}")

        normalized_styles: list[dict] = []
        for style in styles:
            style_id = style.get("key")
            if not style_id:
                raise ValueError(f"{card_id}: style 缺少 key")
            if style_id in style_ids:
                raise ValueError(f"重复 style id: {style_id}")
            style_ids.add(style_id)
            media = style.get("media") or {}
            media_url = media.get("url")
            normalized_styles.append(
                {
                    "id": style_id,
                    "name": style.get("label") or style_id,
                    "desc": style.get("description") or card.get("summary") or card.get("intention") or "",
                    "preview": {
                        "type": media.get("type") or ("mp4" if media_url else "none"),
                        "url": urllib.parse.urljoin(GALLERY_BASE_URL, media_url) if media_url else None,
                        "availability": "remote" if media_url else "missing",
                    },
                }
            )

        source_path = card.get("source") or f"references/shots/{card.get('category', 'uncategorized')}/{card_id}.md"
        source_url = urllib.parse.urljoin(GALLERY_BASE_URL, card.get("sourceUrl") or source_path)
        github_source_url = (
            f"https://github.com/{UPSTREAM_OWNER}/{UPSTREAM_REPO}/blob/{commit}/{source_path}"
        )
        demo_url = (
            f"https://github.com/{UPSTREAM_OWNER}/{UPSTREAM_REPO}/tree/{commit}/"
            f"demos/{card.get('category', 'uncategorized')}/{card_id}"
        )
        recipes.append(
            {
                "id": card_id,
                "namespace": "video-shotcraft",
                "name": card_id,
                "engine": "remotion",
                "runtimeStatus": "upstream-source",
                "verification": "upstream-preview",
                "category": card.get("category") or "uncategorized",
                "tags": card.get("tags") or [card.get("category") or "uncategorized"],
                "summary": card.get("summary") or card.get("intention") or "",
                "intention": card.get("intention") or card.get("summary") or "",
                "use": card.get("use") or "",
                "duration": card.get("duration") or "",
                "energy": card.get("energy") or "",
                "addedAt": card.get("addedAt"),
                "updatedAt": card.get("updatedAt"),
                "sourcePath": source_path,
                "recipeUrl": source_url,
                "githubSourceUrl": github_source_url,
                "implementationUrl": demo_url,
                "styles": normalized_styles,
            }
        )

    return {
        "schemaVersion": 1,
        "source": {
            "name": UPSTREAM_REPO,
            "repository": f"https://github.com/{UPSTREAM_OWNER}/{UPSTREAM_REPO}",
            "gallery": GALLERY_BASE_URL + "library.html",
            "commit": commit,
            "upstreamRevision": raw.get("revision"),
            "license": "Apache-2.0",
            "importedAt": datetime.now(timezone.utc).isoformat(),
            "mediaPolicy": "remote-preview-only",
        },
        "stats": {
            "recipeCount": len(recipes),
            "styleCount": sum(len(recipe["styles"]) for recipe in recipes),
            "previewCount": sum(
                1
                for recipe in recipes
                for style in recipe["styles"]
                if style["preview"]["availability"] == "remote"
            ),
        },
        "recipes": recipes,
    }


def write_snapshot(output_dir: Path, raw_bytes: bytes, license_bytes: bytes, normalized: dict) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    raw = json.loads(raw_bytes.decode("utf-8"))
    (output_dir / "source-library.json").write_text(
        json.dumps(raw, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    payload = json.dumps(normalized, ensure_ascii=False, indent=2)
    (output_dir / "recipes.json").write_text(payload + "\n", encoding="utf-8")
    (output_dir / "recipes.js").write_text(
        f"window.__REMOTION_RECIPE_LIBRARY__ = {payload};\n", encoding="utf-8"
    )
    (output_dir / "LICENSE").write_bytes(license_bytes)
    source = normalized["source"]
    (output_dir / "SOURCE.md").write_text(
        "# video-shotcraft 配方来源\n\n"
        f"- 仓库：{source['repository']}\n"
        f"- 固定提交：`{source['commit']}`\n"
        f"- 上游数据版本：`{source.get('upstreamRevision')}`\n"
        f"- 导入时间：{source['importedAt']}\n"
        "- 许可证：Apache-2.0（见同目录 `LICENSE`）\n"
        "- 本地改动：只做字段规范化、绝对链接补全和引擎/验证状态标注。\n"
        "- 媒体策略：不复制上游视频、音乐或音效；Gallery 仅按需读取远程 MP4 预览。\n"
        "- 运行边界：这些记录是 Remotion 配方及上游源码入口，不冒充本地 HTML snippet。\n",
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="导入 video-shotcraft Remotion 配方快照")
    parser.add_argument("--input", default=LIBRARY_URL, help="上游 library.json 的路径或 URL")
    parser.add_argument("--commit", default=DEFAULT_COMMIT, help="用于固定源码链接的 Git commit")
    parser.add_argument(
        "--license-input",
        default=None,
        help="Apache-2.0 LICENSE 路径或 URL；默认读取固定 commit 的 LICENSE",
    )
    parser.add_argument("--output-dir", type=Path, required=True, help="配方快照输出目录")
    args = parser.parse_args(argv)

    license_source = args.license_input or (
        f"https://raw.githubusercontent.com/{UPSTREAM_OWNER}/{UPSTREAM_REPO}/{args.commit}/LICENSE"
    )
    raw_bytes = read_bytes(args.input)
    raw = json.loads(raw_bytes.decode("utf-8"))
    normalized = normalize_library(raw, args.commit)
    license_bytes = read_bytes(license_source)
    write_snapshot(args.output_dir, raw_bytes, license_bytes, normalized)
    stats = normalized["stats"]
    print(
        f"已导入 {stats['recipeCount']} 张 Remotion 配方卡 / "
        f"{stats['styleCount']} 个样式 / {stats['previewCount']} 个远程预览"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"导入失败: {exc}", file=sys.stderr)
        raise SystemExit(1)
