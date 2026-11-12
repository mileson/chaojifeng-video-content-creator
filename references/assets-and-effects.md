# 素材与特效

做素材规划、B-Roll 模式绑定、Hyperframes 叠加轨（overlay）、粗剪视觉终检时读取本文件。本 skill 已内置完整特效库，直接使用 `assets/style_library/`。

## 内置特效库结构

优先使用这些本 skill 内置文件：

| 路径 | 用途 |
| --- | --- |
| `assets/style_library/narrative-index.md` | 按叙事意图反查模式；写稿和分镜绑定 B-Roll 模式前必读 |
| `assets/style_library/catalog.md` | 模式说明、三层结构、转场、产品卡、片尾和使用规则 |
| `assets/style_library/recipe-system.md` | 统一配方模型、引擎路由、状态和来源边界 |
| `assets/style_library/registry.json` | 本地原生模式注册表（事实源）；核对 id、分类、描述、snippet 路径 |
| `assets/style_library/registry.js` | 脚本生成的浏览器版注册表，供 `gallery.html` 在 `file://` 下读取，不手改 |
| `assets/style_library/recipes/video-shotcraft/recipes.js` | 固定版本的 Remotion 配方卡、样式、预览和源码入口 |
| `assets/style_library/snippets/` | 可复用 HTML/GSAP 片段 |
| `assets/style_library/previews/` | 每个模式的真实预览页 |
| `assets/style_library/gallery.html` | 给用户浏览和挑选原生、Hyperframes、Remotion 配方的统一页面 |
| `assets/style_library/official/` | 官方组件蒸馏参考 |
| `assets/style_library/scripts/build_effects_gallery.py` | 修改或新增模式后重建预览、刷新缓存并校验 |
| `examples/clean-then-effects/` | 样例工程：阶段 0 到 4 的产物与阶段 6 的清洗数据 |

开始新视频项目前，如涉及特效选择，先读 `data/experience-log.md` 和 `data/memory.md` 复用历史经验；涉及品牌呈现时读 `data/brand-profile.yaml`。

## BROLL-STYLE.md

每个视频项目都要有自己的 `BROLL-STYLE.md`。若项目还没有，先用 `templates/BROLL-STYLE.template.md` 生成，再按 `references/broll-style-standard.md` 填写。

- 屏录工艺、证据真实性、字幕可读性是硬标准，不因项目风格降级。
- 色彩、光效、纹理、图形元素可以跟随选题调整。
- AI 图/AI 视频的提示词必须跟 `BROLL-STYLE.md` 一致；如果相邻镜头是深色屏录，不要插入浅色极简概念图。
- 粗剪和特效终检时，所有素材和 overlay 都要对照 `BROLL-STYLE.md` 检查。

## ASSET-LIST.md

根据 `STORYBOARD.md` 创建或更新 `ASSET-LIST.md`。使用 `templates/ASSET-LIST.template.md`。

每个素材行都要映射回分镜镜号：

- 屏录：页面/应用状态、操作路径、时长、光标行为、真实性要求。
- 真实截图：准确页面/状态和裁切范围。
- AI 图：提示词、画幅、视觉风格、负面约束。
- AI 视频：提示词、运动方式、时长；用户指定工具或模型时写清。
- 排版/特效：B-Roll 模式 id 和画面文字。
- 实拍空镜：主体、景别、环境、动作。

## B-Roll 模式绑定

写口播稿和分镜时，尽量给 B-Roll 行绑定已有模式 id。使用本 skill 内置特效库：

- 选择模式前，先读取 `assets/style_library/narrative-index.md`，按叙事意图查候选模式。
- 候选模式不确定时，再查 `assets/style_library/catalog.md` 的结构、动画要点和适用场景。
- 选定模式后先读 `assets/style_library/recipe-system.md` 确认引擎：原生配方在 `registry.js` 核对 id 和 snippet；Remotion 配方在 `recipes/video-shotcraft/recipes.js` 核对配方、样式和源码入口。
- 用户想参与选择时，建议打开 `assets/style_library/gallery.html`；用户复制配方指令后，必须按指令里的引擎进入对应实现，不得把 Remotion 远程视频误当成本地 snippet。
- 某行已经有模式时，除非不符合本镜目的，否则不要重选。
- 没有匹配模式时，标记 `NEW: <一句话设想>`，后续先查官方 Hyperframes/catalog 选项，再决定是否新设计。
- A-Roll 行也可以绑定模式，用于关键词字幕、引用卡（quote card）或强调叠加轨。

不要把模式写成泛泛的“酷炫动效”。模式必须说明它如何服务叙事意图。

## 配方与引擎路由

统一配方卡是上层叙事合同，包含意图、分类、样式、参数、来源、预览、引擎和验证状态。实现层分三路：

| 引擎 | 适用 | 执行入口 | 完成门禁 |
| --- | --- | --- | --- |
| `native` | 字幕强调、卡片、HUD、容器、轻量转场 | `registry.js` → `snippets/` → Hyperframes overlay | 本地 preview + snapshot + 成片抽帧 |
| `hyperframes` | HTML/GSAP 逐帧离线渲染和透明叠加轨 | 同一原生 snippet，按 `pipeline.md` 组成 composition | lint/validate + snapshot + render |
| `remotion` | 复杂镜头、2.5D/3D、粒子、数据场景、帧精确编排 | Remotion 配方 → TSX 组件 → `<Composition>` | 本地 Remotion 渲染 + 抽帧；远程 preview 不算本地验证 |

同一配方可以有多个样式；`mode_id` 记录具体 style id，并额外记录 `engine`。只有经过原创转译和本地验证，Remotion 样式才可以新增一个 `native` 实现；不要覆盖原配方或抹掉来源。

## 三层特效规划

生成 `EFFECT-BEATS.md` 前，先把特效分成五类，不要把全片都铺成同一种卡片：

- **骨架层**：常驻标题、步骤进度、章节 HUD、进度条。教程类和产品演示默认考虑；常驻 30 秒到全片。
- **节拍层**：3-8 秒的重点强调，服务钩子、痛点、对比、算账、总结和 CTA。
- **容器层**：窗口、手机画中画、仪表盘、演示容器。内容要有滚动、数字增长或状态变化，不要做死图。
- **转场节拍**：章节切换处使用，默认不要超过每 20 秒一次；必须有叙事理由。
- **片尾/产品卡**：教程、产品、作品展示类可用作者作品墙或产品卡；遵守平台合规，不放二维码、网址或硬导流话术。

节拍密度默认每 10-20 秒一个。钩子、算账/对比、总结、CTA 优先绑定；不要为了“热闹”把每句话都做成特效。

## EFFECT-BEATS.md

录完以后做特效时，先用 `templates/EFFECT-BEATS.template.md` 生成或更新 `EFFECT-BEATS.md`。这份表是 overlay 的执行稿，不是新的分镜稿。

生成顺序：

1. 确定成片时间轴：优先使用用户提供的 SRT；否则使用项目 ASR/转写；如果视频已经剪过，先把原始转写时间映射到成片时间轴。
2. 对齐 `STORYBOARD.md`：用台词文本、关键词和语义，把真实字幕段落映射回镜号；实际口播和脚本不一致时，以真实字幕为准，并在备注里说明差异。
3. 导入模式：已有 `B-Roll 模式` 时直接作为 `mode_id`；除非它明显不符合真实口播内容，否则不要重选。
4. 未预绑定模式的字幕段，按真实字幕的叙事意图读 `narrative-index.md` 选 mode，再用 `catalog.md` 和 `registry.js` 核对。
5. 把每个节拍拆成可填充槽位：标题、关键词、数字、步骤、引用句、对比两侧、CTA、素材文件、品牌/产品名。
6. 对每个 mode 读取对应 snippet，把演示文案替换成本条视频的真实内容；不要原样复用 snippet 里的示例文字。
7. 标出层级：骨架层、节拍层、容器层、转场节拍或片尾/产品卡；检查密度和互相遮挡。

每个节拍必须记录：

| 字段 | 说明 |
| --- | --- |
| beat_id | `b1`, `b2`... |
| 镜号 | 对应 `STORYBOARD.md` 的镜号，可多个 |
| start / duration | 成片真实时间轴，进出场至少留 0.15s 呼吸 |
| 字幕摘录 | 触发这个特效的真实字幕原文或短摘录 |
| 叙事意图 | 开场钩子、痛点、对比、算账、步骤、演示、总结、CTA 等 |
| mode_id | 库内 id；确无匹配才用 `NEW: <一句话设想>` |
| engine | `native` / `hyperframes` / `remotion`；决定实现和验证路线 |
| layer | 骨架层 / 节拍层 / 容器层 / 转场节拍 / 片尾或产品卡 |
| snippet_path | 来自 `registry.js` 的 snippet 路径 |
| content_slots | 这个 snippet 需要填进去的标题、数字、步骤、关键词、CTA、素材 |
| content_source | 内容来自字幕、分镜、素材文件、产品事实或用户补充 |
| 安全区 | 字幕、人脸、产品 UI、光标动作的避让说明 |
| 状态 | 待评审、待素材、待实现、已实现、已抽帧检查 |

填充规则：

- 关键词类 mode：从字幕摘 1-3 个短词，不要改写成新的承诺。
- 引用卡/金句类 mode：只截取真实说出口的句子；需要压缩时保留原意。
- 数字/算账/对比类 mode：数字必须来自字幕、素材或可核对资料；没有来源就标 `待确认`。
- 步骤/清单类 mode：步骤顺序必须跟口播顺序一致。
- 产品卡/功能卡 mode：产品名、功能名、价格、限制条件必须来自用户材料或真实截图。
- 片尾/CTA mode：只保留一个主动作；无二维码、网址或平台不允许的导流话术。

`EFFECT-BEATS.md` 是动手写 overlay 前的评审产物。用户要求全自动继续时，也要先生成它，再基于它实现 `broll-overlay/`。

## 素材审计

粗剪前创建 `assets/ASSET-AUDIT.md`：

```markdown
# Asset Audit

| 素材 | 镜号 | 结论 | 理由 | 问题 |
| --- | --- | --- | --- | --- |
| screen-price-001.mp4 | 5,6 | USE | 展示真实价格对比 | 00:03 光标太快 |
```

使用 `USE`、`SKIP` 或 `REPLACE`。不要用 AI 生成画面冒充真实证据。

## Hyperframes 叠加轨

制作特效时：

1. 用 `ffprobe` 解析源视频的时长、分辨率和帧率。
2. 确认阶段 6 清洗状态：优先使用已清洗 A-Roll、`aroll/edit_decisions.json` 和清洗后的 SRT/ASR；如果用户明确跳过清洗，在交付里写入未清洗风险。
3. 如果视频已经剪过，把原始转写时间映射到成片时间轴。
4. 从 `STORYBOARD.md`、真实字幕和素材审计结果生成或更新 `EFFECT-BEATS.md`。
5. 对每个节拍确认配方 id、style id 和 engine 存在；原生路线核对 registry/catalog/snippet，Remotion 路线核对 recipe/source/TSX，并把内容槽位替换成本条视频的真实字幕、关键词、数字、步骤、CTA 或素材。
6. 创建 `broll-overlay/`，复制素材并改成 ASCII 文件名。
7. 动手写动画前按需读 `references/pipeline.md`、`references/gsap-best-practices.md`、`references/hyperframes-lessons.md`。
8. 按 `EFFECT-BEATS.md` 实现 HTML/GSAP overlay；动画优先使用 transform 和 opacity。
9. Hyperframes 可用时运行 lint/validate。
10. 每改一个节拍，先用 snapshot 抽该节拍 2-3 个关键时刻目检；全部节拍通过后再全片 render。
11. 用 FFmpeg 把透明 WebM 叠到源视频上。
12. 抽检查帧或 contact sheet，做视觉安全检查。

## 视觉终检

检查代表帧：

- 不遮挡字幕、人脸、产品关键 UI 或光标动作。
- 文字没有错别字，并且能放进容器。
- 特效文字来自真实字幕、分镜或素材，不残留 snippet 示例文案。
- 动画进出干净。
- B-Roll 与口播台词和本镜目的匹配。
- 色彩/风格不和项目 `BROLL-STYLE.md` 冲突。
- 转场不要过密；强转场要有叙事理由。

## 特效库成长

如果新特效模式已验证且准备复用，按特效库四件套入库：

1. snippet：写入 `assets/style_library/snippets/`。
2. catalog：追加到 `assets/style_library/catalog.md`。
3. narrative-index：把 id 加进 `assets/style_library/narrative-index.md` 对应叙事意图组。
4. registry + 预览重建：在 `assets/style_library/registry.json` 登记 `id / name / category / desc / anim / params / path / accent / since`，再依次运行 `python3 assets/style_library/scripts/build_effects_gallery.py build`、`refresh`、`validate`（`registry.js` 与 `cache.json` 由脚本生成，不手改）。

入库细则：

- snippet 是结构和动画范式，示例文案每次使用都要替换成本条视频内容。
- snippet 禁止 `repeat: -1`；持续动画用可配置播放时长和有限循环，保证逐帧捕捉确定。
- 新模式预览空白、依赖工程 DOM 或需要特殊居中时，在 `build_effects_gallery.py` 的 `OVERRIDES` 里补演示 DOM/CSS/驱动代码，不要为了预览改坏 snippet 本体。
- 新模式入库后必须打开预览或 gallery 自查；预览报错、空白或不可读时，不算入库完成。

用户要求“扩充素材库”或“新增一批特效”时：

1. 先用 `npx hyperframes catalog` 查官方 blocks/components。
2. 安装到临时 lab 工程后逐个读源码，不要只看名字猜用途。
3. 对照 `registry.json` 做避重清单，按骨架层、节拍层、容器层、转场、工具归类。
4. 把候选组件串进一个 demo composition，每个组件 4-6 秒。
5. 跑 lint、validate、snapshot、render、合成和 contact sheet，再四件套入库。

需要复用的项目经验写入 `data/memory.md`，只记结论、模式和踩坑，不记流水账。
