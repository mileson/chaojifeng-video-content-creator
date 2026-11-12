# 剪辑评审草稿

源视频：{{video}}

模式：{{mode}}

## 摘要

- 原始时长：{{original_duration}}
- 预计导出时长：{{proposed_duration}}
- 封面片头时长：{{cover_duration}}
- 字幕样式：{{subtitle_style}}

## 建议保留片段

| # | 源时间段 | 输出时间段 | 原因 |
|---|---|---|---|
{{keep_rows}}

## 建议删除片段

| # | 源时间段 | 原因 | 置信度 |
|---|---|---|---|
{{delete_rows}}

## 人工评审备注

- 最终渲染前，先确认可能影响语义的删除。
- 专名和错词修正来自 `data/corrections.yaml`。
- 口水词、重复和节奏规则来自 `data/filler_rules.yaml`。
