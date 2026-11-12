# 口播稿与分镜

写口播稿、把已有稿件拆成分镜、或准备可录制方案时读取本文件。

## SCRIPT.md 规则

口播稿要服务真实朗读：

- 一行一口气，通常不超过 20 个中文字。
- 可以保留自然口语连接词，但不要用废话填充。
- 不念出的拍摄/剪辑提示写在 `【】` 里。
- 前 3-5 秒必须停住观众：反差、强断言、具体结果或明确数字。避免“大家好今天我们来聊聊”。
- 适合时，钩子后 5-30 秒内安排痛点共鸣段。
- CTA 只保留一个主动作。
- 标明口述状态：`AI初稿`、`口述校准中` 或 `本人已口述定稿`。

使用 `templates/SCRIPT.template.md`。

如果用户要求“直接可录”“更像我本人讲话”“顺便绑定特效库”或需要更完整的痛点共鸣写法，继续读取 `references/aroll-script-guide.md`。

## 痛点共鸣写法

给出方案前，先让目标观众认出自己：

- 用第二人称具体场景：“你是不是也这样……”
- 说出观众不好意思说出口的小细节。
- 用 2-3 个递进确认，让观众连续点头。
- 必要时把痛点折算成时间、钱或重试次数。
- 结尾立刻转折：“直到我发现……”或“问题其实不在你……”

不要嘲讽观众，要站在观众一边。

## STORYBOARD.md 规则

写 B-Roll 分镜前先读 `references/shot-grammar.md`。画面描述要像镜头，不要像网页布局：先写观众注意什么、镜头怎样运动，再写素材或特效。

按“先概念后素材”（concept-first）顺序推进：

`核心信息（Message）-> 叙事弧 -> 口播拆句 -> A/B-Roll 判定 -> 画面策略 -> 素材/特效绑定`。

按句子或语义小节拆稿。每行尽量 10-40 个中文字，约 2.5-10 秒。

必需列：

| 列 | 作用 |
| --- | --- |
| 镜号 | 1、2、3…… |
| 段落 | 钩子、背景、痛点、机制、演示、对比、总结、CTA |
| 台词 | 来自 `SCRIPT.md` 的口播原句 |
| 类型 | A-ROLL 或 B-ROLL |
| 景别+运动 | B-Roll 必填，A-Roll 可选 |
| 画面描述 | 观众看到什么 |
| 素材策略 | 屏录、真实截图、AI 图、AI 视频、实拍、排版/特效 |
| B-Roll 模式 | 已有特效/库内 id，或 `NEW: <设想>` |
| 图像提示词 | 需要 AI 图时填写 |
| 视频提示词 | 需要 AI 视频时填写 |
| SFX | 音效类型/文件、触发点、音量备注 |
| 素材文件 | 阶段 5 后回填 |
| 预估时长 | 口播字数 / 每秒 4-4.5 字 |
| 真实时间戳 | A-Roll 清洗后回填 |
| 状态 | 已规划 / 待素材 / 已生成 / 已验收 / 已剪辑 / 已发布 |
| 本镜目的 | 观众这一镜应该记住或感受到什么 |

使用 `templates/STORYBOARD.template.md`。

## BROLL-STYLE.md

首次进入分镜或素材阶段时，生成或更新项目级 `BROLL-STYLE.md`，使用 `templates/BROLL-STYLE.template.md`。

写作依据：

- 先读 `references/broll-style-standard.md`。
- 结合 `data/experience-log.md` 的个人默认偏好。
- 可以根据本选题覆写色彩、元素和情绪，但不要降低屏录工艺、证据真实性和字幕可读性。
- 深色屏录序列中插入 AI 概念图时，必须校准色温和明暗，不要让画面跳戏。

`BROLL-STYLE.md` 应至少写清：

- 主平台与画幅。
- 屏录采集规格、光标行为、隐私遮挡和背景包装。
- AI 图/AI 视频的视觉基线、禁用风格和多候选评审标准。
- 字幕安全区、字号/行数、与特效避让规则。
- 计划中的 Pattern Interrupt、转场密度和 CTA 画面事件。
- 如果主片超过 2 分钟，同步规划 60-90 秒衍生精剪版的结构。

## A/B-Roll 判断

- “我/我们/感受/观点/转折”通常保留 A-Roll，用来建立信任。
- “看这个/数据/步骤/结果/对比”通常用 B-Roll，提供证据。
- 钩子常常先用 A-Roll 建立人，再快速切 B-Roll 给证据。
- B-Roll 要支撑论点，不要只是装饰。
- 证据、数据、产品操作类镜头必须使用真实屏录或真实截图。

## 自检

- B-Roll 覆盖率 >= 40%。
- 连续 A-Roll 不超过 20 秒，除非明确说明理由。
- 连续 B-Roll 不超过 30 秒，避免太久不回到人。
- 钩子有专门设计的第一镜。
- 每个 B-Roll 行都有素材策略和 B-Roll 模式。
- 每行都有非空的本镜目的。
- CTA 主动作唯一。
- Pattern Interr…1638 tokens truncated…真实时间轴，进出场至少留 0.15s 呼吸 |
| 字幕摘录 | 触发这个特效的真实字幕原文或短摘录 |
| 叙事意图 | 开场钩子、痛点、对比、算账、步骤、演示、总结、CTA 等 |
| mode_id | 库内 id；确无匹配才用 `NEW: <一句话设想>` |
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
5. 对每个节拍确认模式 id 存在于特效库 registry/catalog/snippet，并把 snippet 内容槽位替换成本条视频的真实字幕、关键词、数字、步骤、CTA 或素材。
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
