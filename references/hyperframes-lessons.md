# Hyperframes 踩坑经验

来自真实项目的验证结论，动手写 composition 前先扫一遍。

## lint / validate 类

| 报错 / 警告 | 原因 | 处理 |
| --- | --- | --- |
| `gsap_css_transform_conflict` | CSS 用 `transform: translateX(-50%)` 居中，GSAP 又动画 `x/y/scale`，两者都写 transform 会互相覆盖 | 居中改用 `left: 0; right: 0; margin: 0 auto; width: fit-content;`，把 transform 全部留给 GSAP |
| `text_box_overflow` | 元素故意超出容器（如删除线贯穿整个词、贴纸出血） | 容器加 `data-layout-allow-overflow`，装饰子元素加 `data-layout-ignore`，明确告诉检查器这是有意为之 |
| `font_family_without_font_face` | 用系统字体（PingFang SC）没声明 @font-face | 本地渲染可忽略；如改用 Docker 渲染必须打包字体文件 |
| `timeline_track_too_dense` | 单 track 上 clip 多 | 口播 B-Roll 节拍天然密集，确认节拍间无重叠即可接受 |
| 对比度 contrast 警告 | 检查器采样到了透明/隐藏状态的元素 | 目检实际渲染帧确认可读后可接受，属误报 |

## 布局类

- **字幕碰撞是最高频返工原因**。设计稿阶段就把底部 920px（1080p 基准）划为禁区；卡片堆叠先按「窄而高」排，不要「宽而矮」
- 多行大标题想单行展示：直接 `white-space: nowrap` + 加宽容器，比调字号试错快
- 垂直堆叠多个居中元素（按钮 + 副标语）：用 `display: flex; flex-direction: column; align-items: center; gap` 一次到位，不要分别绝对定位再各自 transform 居中
- 元素带旋转（`rotate`）时写在 CSS 里没问题，但该元素的 GSAP 动画里如果再写 `rotation`，入场要用 `from` 的相对值，确认结束态与 CSS 一致

## 渲染 / 合成类

- 1080p 设计 + 渲染，再在 FFmpeg 合成时 `scale` 到 4K：速度快数倍，文字大字号下放大无可见劣化
- alpha WebM 在 FFmpeg 输入端**必须** `-c:v libvpx-vp9`，否则透明变黑底
- `overlay=0:0:shortest=1`：overlay 时长应等于成片时长（composition `data-duration` 直接写成片秒数），避免尾部黑帧或提前消失

## 时间轴类

- 节拍 start/duration 从**成片字幕**取，不要从原始未剪视频取
- 最后一个节拍（关注引导）允许淡出收尾压线到 `data-duration`，其余节拍出场动画要在 clip 结束前完成
- 强调循环（yoyo）次数 3~5 次足够，过多会抢口播注意力
