#!/usr/bin/env python3
"""生成产品介绍卡 snippet（product 分类）。

共用版式：左侧图标 + 右侧名称/类型徽章/一句话介绍，玻璃拟态卡 + 主题色描边光晕。
合规：无二维码、无网址、无联系方式（平台限流红线）。

用法：
    python3 scripts/gen_product_cards.py                       # 生成 4 张通用卡片
    python3 scripts/gen_product_cards.py --config products.json  # 按你的产品列表生成
    python3 scripts/gen_product_cards.py --out <目录>          # 指定输出目录

products.json 是数组，每项字段：
    slug    文件名后缀，生成 product-card-<slug>.html
    prefix  元素 id 前缀（全库唯一，2~4 个小写字母）
    name    产品名称
    type    app | web | opensource | desktop（决定徽章配色）
    badge   徽章文案
    desc    一句话介绍
    accent  主题色，如 #3e9eff
    logo    可选，放进项目 assets/ 的图片文件名；缺省用名称首字做图标

新增卡片后，在 registry.json 里补一条记录，再运行 build_effects_gallery.py build 与 refresh。
"""
from __future__ import annotations

import argparse
import json
import pathlib

DEFAULT_OUT = pathlib.Path(__file__).resolve().parent.parent / "snippets"

DEFAULT_PRODUCTS = [
    {"slug": "app", "prefix": "pca", "name": "【产品名称】", "type": "app", "badge": "iOS App",
     "desc": "【一句话介绍：它帮谁解决什么问题】", "accent": "#3e9eff"},
    {"slug": "web", "prefix": "pcb", "name": "【产品名称】", "type": "web", "badge": "网站",
     "desc": "【一句话介绍：它帮谁解决什么问题】", "accent": "#46d390"},
    {"slug": "opensource", "prefix": "pcc", "name": "【项目名称】", "type": "opensource", "badge": "GitHub 开源",
     "desc": "【一句话介绍：它帮谁解决什么问题】", "accent": "#a878ff"},
    {"slug": "desktop", "prefix": "pcd", "name": "【产品名称】", "type": "desktop", "badge": "客户端",
     "desc": "【一句话介绍：它帮谁解决什么问题】", "accent": "#4dd0e1"},
]

BADGE_STYLE = {
    "app": ("rgba(62,158,255,.16)", "rgba(62,158,255,.45)", "#7ab8ff"),
    "web": ("rgba(70,211,144,.14)", "rgba(70,211,144,.45)", "#5fe0a8"),
    "opensource": ("rgba(168,120,255,.16)", "rgba(168,120,255,.45)", "#c9a8ff"),
    "desktop": ("rgba(77,208,225,.14)", "rgba(77,208,225,.45)", "#4dd0e1"),
}

TPL = """<!--
模式：产品介绍卡 · {type_label}（product-card-{slug}）【产品卡片层 · 5~7s 驻留】
适用场景：视频中讲到或演示某个产品时叠加的标准产品介绍卡：图标 + 名称 + 类型徽章 + 一句话。
  把名称和一句话换成你的产品信息即可；有 logo 时放进项目 assets/ 并改用 <img> 图标。
⚠️ 合规铁律：卡内禁止二维码 / 网址 / 联系方式 / 导流话术（平台限流红线），只陈述产品事实。
框架参数：
  - 停靠位置（默认底部居中，可改 left/right 侧停靠避开人脸）、入场时间 t0、驻留时长
  - 图标：默认取名称首字做字标，也可以换成项目 assets/ 内的 logo 图片
技术要点：
  - 卡 y 64 back.out 浮入 → 图标 back.out(2.2) 微弹 + 主题色光晕呼吸 → 文案 stagger 入
  - shine 高光斜扫一次（700ms）提质感；退场 y 36 power2.in
  - 同一工程可叠多张产品卡：id 前缀 {pfx}- 全库唯一，无冲突
-->
<style>
  #{pfx}-card {{ position: absolute; left: 50%; bottom: 170px; display: flex; align-items: center; gap: 26px;
    background: rgba(10,14,22,.9); border: 1px solid {accent}66; border-radius: 24px;
    padding: 26px 42px 26px 28px; white-space: nowrap; overflow: hidden;
    box-shadow: 0 0 56px {accent}26, 0 28px 64px rgba(0,0,0,.5); }}
  #{pfx}-icon {{ width: 104px; height: 104px; border-radius: 24px; flex: 0 0 auto;
    display: flex; align-items: center; justify-content: center;
    color: #fff; font-size: 52px; font-weight: 900;
    background: linear-gradient(145deg, {accent}, {accent}99);
    border: 1px solid rgba(255,255,255,.22); box-shadow: 0 10px 28px rgba(0,0,0,.5); }}
  #{pfx}-name {{ color: #f2f5fc; font-size: 40px; font-weight: 900; letter-spacing: 1px; }}
  #{pfx}-badge {{ display: inline-block; vertical-align: 6px; margin-left: 16px; font-size: 17px; font-weight: 800;
    border-radius: 99px; padding: 4px 16px; letter-spacing: 1px;
    color: {b_text}; background: {b_bg}; border: 1px solid {b_border}; }}
  #{pfx}-desc {{ color: #a3adc2; font-size: 23px; font-weight: 700; margin-top: 10px; }}
  #{pfx}-shine {{ position: absolute; top: -40%; left: 0; width: 110px; height: 180%;
    background: linear-gradient(105deg, transparent, rgba(255,255,255,.16), transparent);
    transform: skewX(-18deg); }}
</style>

<div id="{pfx}-card">
  {icon_html}
  <div>
    <span id="{pfx}-name">{name}<span id="{pfx}-badge">{badge}</span></span>
    <div id="{pfx}-desc">{desc}</div>
  </div>
  <div id="{pfx}-shine" data-layout-ignore></div>
</div>

<script>
  gsap.set("#{pfx}-card", {{ xPercent: -50 }});
  gsap.set("#{pfx}-shine", {{ x: -160 }});
  tl.from("#{pfx}-card", {{ autoAlpha: 0, y: 64, duration: 0.55, ease: "back.out(1.5)" }}, t0);
  tl.from("#{pfx}-icon", {{ scale: 0.5, rotation: -8, duration: 0.5, ease: "back.out(2.2)" }}, t0 + 0.15);
  tl.from(["#{pfx}-name", "#{pfx}-desc"], {{ autoAlpha: 0, x: 26, duration: 0.45, stagger: 0.12 }}, t0 + 0.3);
  tl.from("#{pfx}-badge", {{ autoAlpha: 0, scale: 0.5, duration: 0.4, ease: "back.out(2.4)" }}, t0 + 0.6);
  tl.to("#{pfx}-shine", {{ x: 760, duration: 0.7, ease: "power2.inOut" }}, t0 + 0.85);
  tl.to("#{pfx}-icon", {{ boxShadow: "0 0 34px {accent}99", duration: 0.55, yoyo: true, repeat: 2,
    ease: "sine.inOut" }}, t0 + 1.1);
  tl.to("#{pfx}-card", {{ autoAlpha: 0, y: 36, duration: 0.45, ease: "power2.in" }}, t0 + 5.2);
</script>
"""

TYPE_LABEL = {"app": "应用", "web": "网站", "opensource": "开源项目", "desktop": "客户端"}


def monogram(name: str) -> str:
    """取名称里第一个非括号字符做字标。"""
    for ch in name:
        if ch not in "【】[]()（） ":
            return ch
    return "P"


def render(item: dict) -> str:
    ptype = item.get("type", "app")
    if ptype not in BADGE_STYLE:
        raise SystemExit(f"未知类型 {ptype!r}，可选：{', '.join(BADGE_STYLE)}")
    b_bg, b_border, b_text = BADGE_STYLE[ptype]
    pfx = item["prefix"]
    logo = item.get("logo")
    if logo:
        icon_html = f'<img id="{pfx}-icon" src="assets/{logo}">'
    else:
        icon_html = f'<div id="{pfx}-icon">{monogram(item["name"])}</div>'
    return TPL.format(
        slug=item["slug"], pfx=pfx, name=item["name"], badge=item["badge"], desc=item["desc"],
        accent=item["accent"], b_bg=b_bg, b_border=b_border, b_text=b_text,
        icon_html=icon_html, type_label=TYPE_LABEL[ptype],
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="生成产品介绍卡 snippet")
    parser.add_argument("--config", type=pathlib.Path, help="产品列表 JSON；缺省生成 4 张通用卡片")
    parser.add_argument("--out", type=pathlib.Path, default=DEFAULT_OUT, help="输出目录，默认 style_library/snippets")
    args = parser.parse_args()

    products = DEFAULT_PRODUCTS
    if args.config:
        products = json.loads(args.config.read_text(encoding="utf-8"))
    args.out.mkdir(parents=True, exist_ok=True)
    for item in products:
        path = args.out / f"product-card-{item['slug']}.html"
        path.write_text(render(item), encoding="utf-8")
        print(f"OK {path.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
