# EFFECT-BEATS：<选题>

- **源视频**：
- **字幕 / ASR 来源**：
- **成片时间轴说明**：
- **关联分镜**：`STORYBOARD.md`
- **项目视觉基线**：`BROLL-STYLE.md`
- **状态**：待评审 / 待实现 / 已实现 / 已抽帧检查

## 特效节拍表

| beat_id | 镜号 | start | duration | 字幕摘录 | 层级 | 叙事意图 | mode_id | snippet_path | content_slots | content_source | 素材文件 | 安全区 | 状态 | 备注 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| b1 | 1 | 0.30 | 4.80 | <真实字幕短摘录> | 节拍层 | 开场钩子 | stamp-hook | assets/style_library/snippets/stamp-hook.html | 标题=<短句>; 关键词=<词1/词2> | 字幕 | - | 避开字幕底部和人脸 | 待实现 | - |
| b2 | 3 | 12.10 | 6.20 | <真实字幕短摘录> | 容器层 | 对比 | bar-chart-compare | assets/style_library/snippets/bar-chart-compare.html | 左=<对比A>; 右=<对比B>; 数字=<来源数字> | 字幕 + 素材 | screen-001.mp4 | 避开产品关键 UI | 待素材 | 数字待核对 |

## 填充检查

- 是否所有 `mode_id` 都在 `registry.js` 中存在：
- 是否所有 snippet 示例文案都已替换：
- 是否所有数字/价格/限制条件都有来源：
- 是否存在真实字幕与分镜不一致：
- 是否有 `NEW:` 模式需要新设计：
- 节拍密度是否约每 10-20 秒一个，且钩子/对比/总结/CTA 已覆盖：
- 骨架层、节拍层、容器层、转场、片尾/产品卡是否互相遮挡：
- 每个已实现节拍是否 snapshot 抽 2-3 个关键时刻：

## 实现备注

-
