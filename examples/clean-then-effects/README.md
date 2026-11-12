# 样例工程：口播视频，先清洗再加特效

一条约 43 秒的教程视频，从选题到分镜的完整阶段产物，格式与 `templates/` 里的模板一致。

| 文件 | 阶段 | 内容 |
| --- | --- | --- |
| `topic-brief.md` | 0 选题 | 选题句、受众、平台、未知问题 |
| `research.md` | 1 调研 | 核心论点及依据、可引用数字、素材候选、未验证的主张 |
| `BRIEF.md` | 2 策略 | 核心信息、叙事弧、钩子策略、画幅 |
| `SCRIPT.md` | 3 口播稿 | 约 165 字口播稿，标明口述状态 |
| `STORYBOARD.md` | 4 分镜 | 12 镜分镜表，绑定特效库里真实存在的模式 id，附自检结果 |
| `transcript.json` | 6 清洗 | 15 秒口播的词级转写，含口水词、重复词和一个被引用的“嗯” |
| `subtitle_plan.json` | 6 清洗 | 清洗决策：词级剪切、字幕文字覆盖、待复核项 |
| `edited.srt` | 6 清洗 | 按上面两份文件生成的清洗后字幕 |

## 复现阶段 6 的字幕

任意准备一段 15 秒的视频（只用来读取时长），在仓库根目录运行：

```bash
python3 scripts/render_from_transcript.py \
  --video /path/to/any-15s-video.mp4 \
  --transcript examples/clean-then-effects/transcript.json \
  --subtitle-plan examples/clean-then-effects/subtitle_plan.json \
  --work-dir /tmp/clean-then-effects \
  --output /tmp/clean-then-effects/out.mp4 \
  --window 0:15:full \
  --skip-render
```

`/tmp/clean-then-effects/edited.srt` 应与本目录的 `edited.srt` 一致：删掉的“然后的话”“呃”“都”“整条”同时从时间轴和字幕里消失，作为被引用词的“嗯”保留。去掉 `--skip-render` 后，渲染前还要完成音轨波形质检与人工复听，流程见 `references/cleanup-and-subtitles.md`；视频编码器用 `--video-encoder` 指定，macOS 默认 `h264_videotoolbox`，其他系统默认 `libx264`。
