# 工作流契约

这个 skill 同时支持完整链路制作和单阶段进入。先判断入口，再读取最少的参考文件。

## 入口路由

| 入口 | 典型用户请求 | 必要输入 | 主要产物 |
| --- | --- | --- | --- |
| 选题 | “帮我从这个选题做一条视频” | 选题或粗略想法 | `topic-brief.md`、`research.md`、`BRIEF.md` |
| 材料 | “我有这些资料，帮我出稿” | 选题 + 笔记/文档/链接/文件 | `BRIEF.md`、`SCRIPT.md`、`STORYBOARD.md`、`BROLL-STYLE.md` |
| 口播稿 | “我有口播稿，帮我拆分镜” | 口播稿文本 | `STORYBOARD.md`、`BROLL-STYLE.md`、`ASSET-LIST.md` |
| 已录 A-Roll | “我录好了，帮我剪干净” | 视频或音频文件 | 转写、`subtitle_plan.json`、`edit_decisions.json`、干净 A-Roll |
| 本人数字人 | “用我的数字人讲这段稿” | 已授权形象、口播稿；声音克隆需另行授权 | `avatar-aroll/source.mp4`、`provenance.json`、视觉检查；下载受阻则保留 `preview_ready/blocked` |
| 粗剪 | “帮我加字幕/封面/导出版” | 粗剪 MP4 或项目产物 | 可发布 MP4/SRT/ASS/检查帧 |
| 特效 | “给这条视频加 B-Roll 特效” | 视频 + 转写/SRT/分镜/素材 | `EFFECT-BEATS.md`、`broll-overlay/`、粗剪、视觉检查 |

## 标准项目目录

沿用入口的工程契约：项目根目录保留原片、已有录制工程、`【成片】<主题名>.mp4` 和 `【逐字稿】<主题名>.srt`，最终封面放根目录 `封面图/`、工作台为根目录 `<主题名>-视频预发布工作台.html`；其余制作过程进入 `视频剪辑明细/`。下列阶段相对路径都从明细目录解析；先记录项目根目录与明细目录，再配置阶段输出位置。

```text
<项目目录>/
├── <原片与已有录制工程>
├── 【成片】<主题名>.mp4
├── 【逐字稿】<主题名>.srt
├── 封面图/                      # 已确认的最终比例图
├── <主题名>-视频预发布工作台.html
├── 【发布文案】<主题名>.md        # 当前公共标题、正文及逐平台标题和标签
└── 视频剪辑明细/
    ├── topic-brief.md / research.md / BRIEF.md
    ├── SCRIPT.md / STORYBOARD.md / BROLL-STYLE.md
    ├── ASSET-LIST.md / EFFECT-BEATS.md
    ├── assets/ASSET-AUDIT.md
    ├── avatar-aroll/             # 可选：数字人源片、来源与 checks/
    ├── aroll/
    │   ├── cleaned-aroll.mp4
    │   ├── transcript.normalized.json
    │   ├── subtitle_plan.json / edit_decisions.json
    │   ├── edited.srt / edited.ass
    │   ├── work/                 # 音频、局部转写、拼接预检等
    │   └── checks/               # 隐藏口播、剪口审计、二次 ASR
    ├── broll-overlay/            # index.html、overlay.webm、assets/、checks/
    ├── rough-cut/                # rough-with-fx.mp4 与 checks/
    ├── work/封面制作/            # 候选与制作记录；确认后清理未采用图片
    ├── tag-research/
    ├── auto-package-state.json
    ├── checks/                   # 项目级验证与目录迁移记录
    └── publish/
        ├── v001/ v002/ ...       # MP4、SRT/ASS、说明、当前发布数据与回执
        │   └── checks/           # 附件验证、首帧、字幕帧与 QA 拼图
        └── work/                 # 发布阶段中间材料
```

每个阶段文件夹顶层只放阶段交付物和契约文件；执行中间材料进该阶段 `work/`，验收证据进该阶段 `checks/`。根目录成片是已验证版本的交付副本，与版本包成片必须具有相同指纹。

目录纪律：

- 封面及工作台位置、定稿后清理范围和路径同步按入口工程契约执行；清理只针对已确认不用且无当前引用的封面中间图，优先废纸篓。

- 阶段文件夹顶层文件数有预期上限（见下方阶段产物预期表）；打开阶段文件夹第一眼就是交付物，不是几十个中间文件。
- Agent 手工创建的临时文件（wav 切片、局部转写 json/txt、filter 脚本、单帧抽查图）**创建时就直接放进 `work/` 或 `checks/`**，不要先散在阶段根目录再整理。
- 内置脚本（如 `render_from_transcript.py --work-dir "<项目目录>/视频剪辑明细/aroll"`）的固定输出位置不强行改动；其产物里属于契约的（转写、plan、决策、SRT）留在阶段根目录，属于审计的（`hidden_speech_review.*`）在阶段收尾时移入 `checks/`。
- 出新版本（补剪、重渲）时不要平铺 `*-v2` 文件：交付物进 `publish/v00N/`，被替代的中间版本移入对应阶段的 `work/`。
- 抽帧 QA 一律先合成 contact-sheet 拼图审看，单帧文件留在 `checks/` 内，不进阶段根目录。

## 阶段产物预期（进门先声明，出门再核对）

每个执行阶段开始时，先在对话里声明本阶段预期产物；阶段结束时逐项核对。这是防止「做着做着材料越堆越多但阶段没有收口」的机制：

| 阶段 | 预期交付物（阶段根目录可见） | 验收证据（checks/） |
| --- | --- | --- |
| 6 清洗 | 干净 A-Roll、归一化转写、subtitle_plan、edit_decisions、SRT/ASS | hidden_speech_review、剪口 RMS 审计、拼接预检结果、成片二次 ASR 复核 |
| 5.5 数字人 | 源视频和 `provenance.json`；网页预览仅记 `preview_ready` | 源文件 ffprobe、口型/发音/人物一致性抽查 |
| 7a 特效 | `index.html`、`overlay.webm`（VP9 alpha） | 逐节拍 snapshot / contact-sheet、lint+validate+inspect 结果 |
| 7b 粗剪 | `rough-with-fx.mp4` | 特效代表帧抽查 |
| 8 发布 | 明细内 `publish/v00N/` 发布包；根目录成片、逐字稿、最终 `封面图/`、主题工作台与发布文案 Markdown | 封面附件验证、首帧、QA 拼图、成片与逐字稿副本指纹、SRT时间轴及交接路径检查 |

任何一个阶段的交付物没出来之前，不进入下一阶段；返工（如补剪）从它所属阶段重新走，下游阶段（特效时间轴、发布包）随之重出。

阶段 4 之后，`STORYBOARD.md` 是单一事实源。它要承载预估时长、真实时间戳、素材文件名、B-Roll 模式 id 和状态。`BROLL-STYLE.md` 是项目视觉基线，约束屏录、AI 图、字幕安全区和特效避让。阶段 6 清洗产物是后续剪辑和特效的时间轴基准。`EFFECT-BEATS.md` 是录后执行表，只能从 `STORYBOARD.md`、清洗后的真实字幕/SRT、ASR 时间戳和素材审计结果派生。

## 阶段门禁

1. 进入口播稿前，必须知道核心信息（Message）、受众、叙事弧、开场策略、平台、预估时长，以及可用的第一人称事实边界；缺少渠道偏好项时可以由 AI 决策并标注，但不得自行推断人物口吻或经历。
2. 进入素材生产前，必须完成分镜评审，并生成或更新 `BROLL-STYLE.md`。
3. 进入特效制作前，每个 B-Roll 镜头必须有素材策略和 B-Roll 模式；没有现成模式时标 `NEW: <设想>` 并说明理由。
4. 录后特效制作必须先完成 A-Roll 清洗或明确跳过清洗；如果原视频已经剪过，先完成成片时间轴映射。
5. 删除任何真实说出口的内容，必须写进 `subtitle_plan.json` 的 `word_cut_ranges` 并同步剪掉音视频。
6. 实现 Hyperframes 后，先逐节拍 snapshot 抽 2-3 个关键时刻，全部通过后再全片渲染和合成。
7. 进入最终发布导出前，必须检查字幕和音频的一致性，并生成 `hidden_speech_review.md` / `.json`。
8. standard 及以上剪辑强度，交付前必须完成碎词二次审计（成片二次 ASR + 双信号扫描 + 拼接预检，见 `references/cleanup-and-subtitles.md`「碎词二次审计」）。
9. 如果跳过某个门禁，必须在交付里写入“我没有验证的部分”。
10. 数字人 A-Roll 只有达到 `verified` 才进入阶段 6；剪映草稿只有实机打开并检查轨道后才标为 `draft_open_verified`。详见 `references/digital-human-aroll.md`。

## 续作规则

- 优先从 `视频剪辑明细/` 查找已有阶段产物；旧项目尚未整理时先复用原位置，用户要求整理后按入口迁移规则收拢，同步当前路径并保留历史记录。

- 项目里已经有 `BRIEF.md` 时，优先沿用，不要重复追问已锁定信息。
- 项目里已经有 `SCRIPT.md` 时，除非用户要求重写，否则保留原口播措辞。
- 项目里已经有 `STORYBOARD.md` 时，在原表回填或更新，不要另建一份竞争分镜。
- 项目里已经有 `BROLL-STYLE.md` 时，后续素材、特效和字幕都按它执行；如果风格要改，先改这份基线。
- 项目里已经有 `aroll/subtitle_plan.json` 或 `aroll/edit_decisions.json` 时，优先复用已有剪辑边界；只在用户要求或发现问题时追加修正。
- 项目里已经有 `EFFECT-BEATS.md` 时，优先按真实字幕、素材审计和用户反馈更新原表，不要重新生成一份互相冲突的特效稿。
- 用户已经接受过剪辑方案时，包装、码率、封面这类重渲染要复用 `edit_decisions.json` 的边界。
- 一次性决策留在项目目录；只有用户明确说这是可复用偏好时，才写入全局 skill 记忆或配置。
