# 清洗与字幕

处理原始 A-Roll、ASR、转写归一化、口水词/重复/停顿清洗、字幕校正、字幕与音频一致性门禁时读取本文件。阶段 6 必须先于阶段 7 特效节拍，除非用户明确跳过清洗。

## 输入

可以接受：

- 源视频或音频。
- 已有口播稿。
- 已有转写/SRT/ASS。
- 已有 `edit_decisions.json` 或保留片段列表。
- 仅在发布包装时使用封面图。

如果提供了口播稿，用 ASR 获取时间戳；只有确认稿件与实际音频匹配后，才对齐并校正文案。

## 内置配置和脚本

优先使用本 skill 内置的配置和脚本：

| 路径 | 用途 |
| --- | --- |
| `data/filler_rules.yaml` | 口水词、`X 的话`、重复重说、长停顿、剪后空白、词边界保护 |
| `data/corrections.yaml` | ASR 错词、专名、热词、首选写法 |
| `data/subtitle_styles.yaml` | 字幕样式预设 |
| `data/asr_providers.yaml` | ASR 提供方配置 |
| `templates/SUBTITLE-PLAN.template.json` | 单条视频的口水词、重复和字幕拆分计划 |
| `templates/review_draft.md` | 语义剪辑人工评审草稿 |
| `scripts/export_hotwords.py` | 从 `corrections.yaml` 导出 ASR 热词 |
| `scripts/normalize_asr_result.py` | 把 ASR 原始结果归一成 `{duration, segments:[{start,end,text,words}]}` |
| `scripts/render_from_transcript.py` | 根据转写、`subtitle_plan.json`、停顿日志和字幕样式渲染清洗版视频 |
| `scripts/spoken_audio_qc.py` | 渲染前剪口音轨质检：标出接缝落在发声中的剪口和过长的残留静音，生成波形报告与复听表 |

全局可复用规则写进 `data/filler_rules.yaml` 或 `data/corrections.yaml`；单条视频的临时判断写进项目目录的 `aroll/subtitle_plan.json`。只有用户明确说“以后都这样处理”时，才改全局配置。

## ASR 与凭证

- 优先使用现有本地转写或项目里的 ASR 产物。
- 只有在音频地址经过用户认可且凭证已配置时，才使用云 ASR。
- 凭证通过环境变量或允许的密钥工具读取；不要把完整 API key 打印或写入日志、草稿、命令或 skill 文件。
- 原始 ASR JSON 保存在归一化转写旁边，方便审计。
- 尽量把转写归一成 `{duration, segments:[{start,end,text,words}]}`。
- 优先使用词级时间戳做清洗和字幕重建。
- 支持热词时，先运行 `scripts/export_hotwords.py --output aroll/hotwords.txt`。

## A-Roll 清洗

默认轻剪，先生成 `aroll/subtitle_plan.json`，再执行渲染：

- 保留原意、承诺和叙事顺序。
- 删除长静音、失败开头、明显重复重录片段、不完整片段、重复转场句。
- 使用“删前保后”：说话人重来一遍时，通常保留后面更完整的版本。
- 不要机械删除所有“嗯/啊/那个/就是”；如果删掉会让剪口不自然，就保留。
- 有语义风险的剪辑要生成评审草稿并获得确认。
- 自动删除主要限于长静音和完全重复。

屏录视频还必须按 `screen-recording-qa.md` 做画面状态审计。ASR 和波形只能判断声音，不能发现“滚上去又滚回来”、页面等待或重复展示。先确认动作是否产生观众需要的新信息，再裁剪无信息区间；有操作结果的静默画面不能仅因无口播而压到固定时长。每个画面剪口都要复查前后状态，并同步检查字幕、音频、遮罩和特效。

剪辑强度：

- `conservative`：只删长等待和完全重复。
- `standard`：再删明显口水词、残句、重复转场句。
- `aggressive`：短视频强节奏压缩；可能损失语义时必须评审。

## 口水词和口癖规则

读取 `data/filler_rules.yaml` 后判断：

- `safe_to_mark` 里的“嗯/呃/额/啊”等，只有不承载语义且剪口自然时才删。
- `discourse_markers_review` 里的“那个/这个/就是/然后/所以/其实”等，必须看前后 1-2 句，不能按关键词硬删。
- `X 的话` 只在纯口癖或拖尾时删除，例如“今天的话”“未来的话”“然后的话”；如果表达条件或假设，例如“如果这样的话”，必须保留。
- 重复词、结巴和前一句说一半又重来，优先“删前保后”。
- 删除真实说出口的词，必须写入 `subtitle_plan.json` 的 `word_cut_ranges`，不能只从字幕文本里删。

`subtitle_plan.json` 的核心字段：

```json
{
  "global_replacements": [{"from": "派森", "to": "Python", "reason": "ASR 音译错词"}],
  "word_cut_ranges": [{"start": 12.34, "end": 12.72, "text": "嗯", "reason": "无效语气词/口水话"}],
  "event_overrides": [{"range_start": 30.0, "range_end": 34.2, "parts": [{"text": "第一句"}, {"text": "第二句"}]}],
  "review_required": [{"range": "45.20-48.10", "text": "候选删除内容", "reason": "可能影响语义"}]
}
```

有语义风险时，创建 `review_draft.md`，写明源时间段、原因和置信度，并等用户确认后再最终渲染。

## 剪辑边界保护

按词级时间戳剪辑时：

- 第一个保留词前加少量前置保护（pre-roll），避免吞掉开头音节。
- 结尾短词需要时加尾音保护（tail guard）。
- 删除词级剪辑产生的边界无词空白。
- 除非人工验证，不要把剪点精确卡在 ASR 词边界上。
- 字级或词级删除后，必须复查相邻片段首尾是否留下无词音频、咽口水、呼吸或停顿；这些也要转成 cut range。
- 第一个保留词和片段末尾短词默认加保护，不要吞掉音头或尾音。

可选生成停顿日志：

```bash
ffmpeg -hide_banner -i <源视频> -af silencedetect=noise=-35dB:d=0.25 -f null - 2> aroll/silence.log
```

## 波形复核（必做，配置见 `filler_rules.yaml` 的 `waveform_verification` 等节）

> 来源：一次人工精剪与自动清洗版的对比。自动版被人工再剪 12 处共 16.7s，四类问题全部源于"只信 ASR 时间戳"。

**ASR 时间戳三不信**：

1. **长停顿后的词 start 不信**：mlx-whisper/FunASR 会把词前静音吞进词跨度，start 系统性前漂 0.3-0.6s。词前 ASR gap > 0.3s 时，必须用 RMS 包络找真实起音（幅度 ≥ 0.02 持续 ≥ 40ms，16k 单声道归一化）。
2. **结巴附近的词跨度不信**：结巴重复字会被 ASR 在文本层去重吸收（「做…做完」→ 一个「做」），文本比对和关键词表都发现不了。词跨度异常拉长且波形是双音团夹 ≥ 0.3s 静音谷 → 只算**候选**，必须再过局部 ASR 复核（见下）才能剪；确认后删前音团保后音团。
3. **尾句词 end 不信**：片尾词 end 同样漂移（实测「拜拜」漂 0.33s），结尾剪切点必须波形复核，否则切断尾音。

**执行流程**（在生成 cut ranges 之后、渲染之前）：

1. 提取 16k 单声道 wav，算 10ms hop 的 RMS 包络。
2. 用波形实测 gap（非 ASR gap）重建全片静音图谱；无词区间峰值 RMS < 0.09 的低音量杂音（键盘声/唇齿音/呼吸/咽口水）按静音同权处理。
3. 按 `pause_budget` 收紧：句间真实停顿 > 0.5s 才收紧到 ≈ 0.28s（前留 0.10 / 后留 0.15）；0.3-0.5s 的自然停顿保留（人工精剪版保留了 24 处 0.27-0.63s 停顿——**不是见静音就剪**）。段头在真实起音前最多留 0.20s。
4. 静默演示段先按 `screen-recording-qa.md` 检查画面动作：无新信息的等待或往返动作可按 `demo_segment_silence.cap_seconds` 压缩；真实操作结果要保留观众看懂所需的过程，不能套固定上限。
5. 逐词扫描跨度异常的词做结巴双音团检测；每个候选截取前音团 ±0.3s 用本地 ASR（如 FunASR paraformer-zh）单独转写复核：转写末字与静音后首字相同才判结巴（如「然后做」vs「做完」），转写出的是上一词尾音则是 ASR 下一词 start 前漂的误报，禁止剪。**不要用声学相似度替代这步**——实测不同字的音团频谱余弦也能到 0.9+，无区分力。
6. 渲染前跑剪口审计：每个剪口前后 0.3s 的峰值 RMS 列表，紧邻高能量（> 0.10）的剪口人工复核防切字。这一步由 `scripts/spoken_audio_qc.py` 完成，用法见下文「剪口音轨质检」。

## 碎词二次审计（standard 及以上强度必做，配置见 `filler_rules.yaml` 的 `residual_fragment_audit` / `splice_precheck`）

> 来源：一条视频 v1 交付后的返修复盘。人工仍指出 5 处一两字级碎词（口头禅「那个」、失败起头「要用」、碎字「我、好」、整组重说「其实还是」「想用好」），全部是被 ASR 吞进长词跨度的，正向清洗发现不了。

正向清洗（转写 → 找口水词 → 剪）之外，交付前补一轮**反向审计**：

1. **成片二次 ASR**：对清洗后的成片音频整段重新转写，逐句读一遍。碎词残留会以重复词或怪异断句暴露（「要用 一定要」「我,好,我刚才」）。
2. **双信号扫描**（在源转写上跑）：(a) 相邻词归一化文本重复（「往|往」）；(b) 词跨度异常——跨度 > 0.35s/字 且 > 0.5s 的词，说明 ASR 把口头禅/失败起头/碎字/重说吞进了该词。
3. **局部窗口 ASR 复核**：每个候选 ±1s 截音频单独转写，词时间映射回源时间，确认真实内容与边界；只有证实才剪。
4. **10ms RMS 细扫定边界**：全片 0.3s 阈值 gap 表对碎词太粗，剪切两端用 10ms hop 找静音谷，对准真实起音/尾音。
5. **剪接口拼接预检（splice check）**：渲染前把每个语义剪口两侧的保留音频拼成小段 wav 单独 ASR；读出的必须正好是目标句才允许渲染。实测 5 处剪口预检全过后成片零返工。
6. **成片复核收口**：重渲后再跑一次第 1 步整段转写，确认目标碎词全部消失、语义连贯，才算通过。

## word cut 导致的字幕事件分裂

单个 cut range 超过一致性检查的 `max_source_gap_seconds`（默认 1.2s）时，同一 ASR 源段会分裂成两个字幕事件。此时：

- `event_overrides` 必须按**分裂后**的事件分别写，`source_start` 对准每个分裂事件的首个保留词（先跑一次 `--skip-render` 看 `edited.srt` 确认分裂位置，再写 override）。
- 剪切边界落在 ASR 长词内部时，词的残余部分（真实发音）会保留在后一个事件里，形成很短的残余事件（如删「自己个人想用好」后残留 0.4s 的「好AI」）。处理法：给残余事件单独写 override 固定文本，让隐藏口播门禁通过；渲染后在最终 SRT/ASS 里把残余条目合并进前一条（文本去重拼接、结束时间取残余条目的 end）。
- 不要为了避免分裂而把剪切改小放过碎词；分裂是正常现象，按上面对位处理即可。

## 字幕规则

- 默认字幕样式为 `orange_rounded_black_white_outline`：`#FF8920` 橙色圆角背景、`#101820` 黑字、白色圆润描边；圆角半径为字幕容器高度的 25%，文字在背景内水平与垂直居中。
- 默认样式使用独立的 ASS 矢量圆角背景层和文字层，禁止用 `BorderStyle=3` 的直角文本框冒充圆角背景。
- 背景宽高随 1-2 行字幕内容自动收缩，保持上下内边距一致；最多两行，不能为了填满容器破坏语义分组。
- Remotion/Hyperframes 实现必须读取同一组视觉 token：`background_colour_hex`、`text_colour_hex`、`outline_colour_hex`、`corner_radius_ratio`、`text_stroke_line_join`、`text_stroke_line_cap`、`vertical_align` 和 `letter_spacing_px`。圆角按容器实时高度乘以 0.25 计算，不得把 CSS 百分比圆角当成等价实现。
- 默认字距为设计画布上的 `8px`，与 `3.25px` 白色描边配合，在相邻描边之间保留可见的橙色细缝；ASS 映射到 Style 的 `Spacing`，Remotion/Hyperframes 映射到 `letterSpacing`。背景宽度计算必须包含每个字间隙，禁止只拉开文字却不扩展容器。验收时以描边后的字符轮廓能够逐字辨认为准，不能只检查黑色字芯或配置值。
- 默认设计画布字号为 `50px`，白色描边为 `3.25px`，字距为 `8px`；单行最多 23 个字符，行高 `65px`。ASS、Remotion 和 Hyperframes 必须读取同一组 token。背景宽度计算必须包含字号、字距和内边距，禁止字号放大后仍沿用旧容器宽度。验收时以描边后的字符轮廓能够逐字辨认、文字不越过橙底为准。
- 旧样式继续保留为可选预设。需要切换时传入 `--style bilibili_white_heavy_outline`、`--style yellow_heavy_outline` 或 `--style screen_recording_compact`，不得修改全局默认值来完成单条视频覆写。
- 校正 ASR 错字、专名、大小写、空格和标点。
- 默认去掉每条字幕以及自动/手动换行后的每个显示行末尾的 `，。！？；：、…` 和英文对应符号（`,.!?;:`），连续尾部标点一并清理；保留句中标点、数字小数点和专名内部符号，不改文字与起止时间。
- 清理在最终分行后执行，并在计算字幕背景尺寸之前完成；转写导出 SRT/ASS 与 `--srt-input` 导入转 ASS 共用正式脚本规则。不得仅修改字幕文件而沿用旧的硬字幕 MP4。纯标点行必须停下复核，不能静默删除整个字幕条目。
- 专名优先于 ASR：作者名、产品名和术语以 `data/corrections.yaml` 的 `preferred_terms` 与热词为准，例如把 `派森` 改成 `Python`。
- 字幕保持 1-2 行，单行长度可读。
- 按完整语义组切分；不要因为自动换行就把两个完整想法粘在同一条字幕里。
- 不要用空格隐藏中文断句。
- 不要用 `...` 或 `…` 表示被隐藏的口播。
- 只改字幕的删除只允许用于 ASR/文案校正。如果从字幕删掉了真实说出口的词，也要从音视频里删掉。
- 不要把说话人改写成另一句话。不是错字、校正或废话删除的改动，留给人工评审。
- 字幕按完整意群拆分；自动换行不能把两个完整想法粘在一起。需要人工指定时写入 `event_overrides`。

## 渲染和复用

常用流程：

1. 原始 ASR 已有但格式不同：运行 `scripts/normalize_asr_result.py --input <raw.json> --output aroll/transcript.normalized.json --provider <provider>`。
2. 复制 `templates/SUBTITLE-PLAN.template.json` 到 `aroll/subtitle_plan.json`，由 Agent 根据真实转写填写候选删除、替换和字幕拆分。
3. 有停顿日志时，把 `--silence-log aroll/silence.log` 传给渲染脚本。
4. 用 `scripts/render_from_transcript.py` 生成清洗版：

```bash
python3 scripts/render_from_transcript.py \
  --video <源视频> \
  --transcript aroll/transcript.normalized.json \
  --subtitle-plan aroll/subtitle_plan.json \
  --work-dir aroll \
  --output aroll/cleaned-aroll.mp4 \
  --window 0:<源视频总时长>:full \
  --mode standard
```

不传 `--style` 时自动使用橙色圆角默认样式；只有项目明确要求其他视觉体系时才用 `--style <preset>` 切换。

已有 SRT 只需要重建样式时，必须走正式入口，不要复制渲染函数写一次性 Python：

```bash
python3 scripts/render_from_transcript.py \
  --srt-input aroll/subtitle.srt \
  --ass-output aroll/subtitle.ass
```

只重渲染包装、字幕或封面，不改变剪辑边界时，用 `--segments-from-decisions aroll/edit_decisions.json` 复用已确认边界。

## 剪口音轨质检（渲染前门禁）

`render_from_transcript.py` 在 `standard` 与 `aggressive` 强度下，渲染前会自动调用 `scripts/spoken_audio_qc.py`：

1. 解码原片音轨，按 10ms 步长计算 RMS 包络，逐个检查相邻保留片段的接缝。
2. 接缝两侧仍有语音能量（可能切掉字头字尾），或接缝处残留的静音超过停顿预算时，标为需要复听。阈值读取自 `data/filler_rules.yaml` 的 `waveform_verification`、`pause_budget` 和 `pre_render_cut_audit`。
3. 结果写到 `<work-dir>/checks/spoken-audio-qc/`：`audio-qc.json`（机器可读结论）、`waveform-report.html`（每个剪口一张包络图，被标出的用橙色边框高亮）、`review-template.json`（复听表）。
4. 没有被标出的剪口时直接通过。否则打开 `waveform-report.html`，逐个复听剪口前后各 1 秒，把 `review-template.json` 里的 `verdict` 填成 `ok`（可接受）或 `fix`（回到 `word_cut_ranges` 调整），然后带上 `--audio-qc-review <复听表>` 重跑。只要还有 `fix` 或未填写的条目，脚本就继续停在门禁。
5. 只有明确接受风险时才用 `--allow-unverified-audio-qc` 跳过，并在交付说明里写明“音轨质检未完成”。

单独运行：

```bash
python3 scripts/spoken_audio_qc.py analyze \
  --input <源视频> \
  --timeline aroll/edit_decisions.json \
  --transcript aroll/transcript.normalized.json \
  --stage pre-render \
  --output-dir aroll/checks/spoken-audio-qc
```

## 一致性门禁

渲染前：

1. 对比保留的词级 ASR 文本和最终字幕文本。
2. 任何被隐藏的真实口播，都必须被 `word_cut_ranges` 覆盖，或列为允许只改字幕的校正。
3. 如果不满足，停止渲染并产出 `hidden_speech_review.md` / `.json`。
4. 进入 `EFFECT-BEATS.md` 前，确认特效将使用清洗后的字幕和时间轴。

清洗阶段预期产物：

- 归一化转写 JSON。
- `aroll/subtitle_plan.json`。
- 生成字幕时的 SRT/ASS。
- `edit_decisions.json`。
- 有语义剪辑时的 `review_draft.md`。
- `hidden_speech_review.md` 和 `.json`。
- 干净 A-Roll 或重渲染视频。
