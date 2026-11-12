# 全管线细节

## 目录

1. 工程结构与 composition 约定
2. GSAP 时间轴约定
3. 渲染参数
4. 合成参数与画质
5. 字幕安全区与人物安全区
6. 抽帧 QA 命令

## 1. 工程结构与 composition 约定

```text
<视频目录>/broll-overlay/
├── index.html      # composition 主文件
├── assets/         # 素材图（ASCII 文件名，如 praise_infoq.jpg）
└── overlay.webm    # 渲染产物
```

`index.html` 骨架要点：

- 根节点：`<div id="root" data-composition-id="<id>" data-start="0" data-width="1920" data-height="1080" data-duration="<成片总时长>">`
- 透明 overlay：`html/body` 和根节点都**不设背景色**
- 每个节拍一个 clip：`<div id="b1" class="clip beat" data-start="<秒>" data-duration="<秒>" data-track-index="0">`
- `.beat { position: absolute; inset: 0; }`，节拍内部元素绝对定位
- 中文字体栈：`"PingFang SC", "Hiragino Sans GB", "Noto Sans SC", sans-serif`（lint 会提示缺 @font-face，本地系统字体可接受；Docker 渲染需自带字体）
- 数字使用 `font-variant-numeric: tabular-nums` 防跳动

## 2. GSAP 时间轴约定

```html
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<script>
  window.__timelines = window.__timelines || {};
  const tl = gsap.timeline({ paused: true });
  // tl.from(...) / tl.to(...) 第三个参数是绝对秒数（相对 composition 起点）
  window.__timelines["<composition-id>"] = tl;
</script>
```

节奏规则：

- 入场放在 `clip start + 0.15s` 左右，出场在 `clip end - 0.5s` 左右开始，避免硬切
- 入场曲线常用 `back.out(1.3~2)`、`expo.out`、`elastic.out(1, 0.55)`；出场统一 `power2.in`
- 多卡片用 `stagger: 0.12~0.16`
- 强调动效：`scale 1.04~1.08 + repeat: 3~5, yoyo: true`，用于价格、结论、关注按钮
- 盖章效果：`from { scale: 3.2, opacity: 0, rotation: 24, ease: "power4.in" }` 再接两段小回弹

进阶编排（节拍模块化、stagger 对象、autoAlpha、count-up、SplitText）按 [gsap-best-practices.md](gsap-best-practices.md) 执行；节拍 ≥ 4 个时优先「子 timeline + 绝对秒挂载」结构，节拍内部用相对时序。

## 3. 渲染参数

```bash
npx hyperframes render . --format webm -o overlay.webm
```

- **必须**带 `--format webm` 才输出 VP9 + alpha；只写 `-o overlay.webm` 会得到 H.264 无透明（扩展名不决定编码）
- 渲染完用 `ffprobe -show_entries stream=codec_name` 确认是 `vp9` 再合成
- 1080p 即可（即使源是 4K）
- 渲染前必跑 `lint` + `validate`，再用 `inspect --frame` 抽节拍关键帧目检

## 4. 合成参数与画质

```bash
ffmpeg -i 原视频.mp4 -c:v libvpx-vp9 -i overlay.webm \
  -filter_complex "[1:v]scale=3840:2160[ov];[0:v][ov]overlay=0:0:shortest=1" \
  -c:a copy -c:v libx264 -crf 18 -preset medium 特效版.mp4
```

- **必须**给 overlay 输入显式指定 `-c:v libvpx-vp9`，默认解码器会丢 alpha
- overlay 用 `scale` 放大到源分辨率；1080p 设计稿放大到 4K 后文字边缘依然干净（矢量排版 + 大字号）
- 音频直接 `-c:a copy`

## 5. 字幕安全区与人物安全区

以 1920x1080 设计稿为准：

- **字幕安全区**：底部约 920px 以下不放任何元素（烧录字幕通常在此）
- **人物安全区**：口播人脸通常在画面右侧或中部，先抽 2~3 帧确认人物位置，再决定元素往哪边排
- 卡片堆叠类（好评瀑布、证据网格）宽度控制在 640~1180px，避免顶到字幕区；出问题优先「缩宽度 + 上移 top + 缩 gap」

## 6. 抽帧 QA 命令

```bash
# 单帧抽查（t 取节拍中段）
ffmpeg -ss <t> -i 特效版.mp4 -frames:v 1 -q:v 2 qa_<id>.jpg -y
```

每个节拍至少查 1 帧；重点查：字幕遮挡、人脸遮挡、文字换行/溢出、错别字、半透明残影。
