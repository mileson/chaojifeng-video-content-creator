# 统一动效配方体系

## 一句话定义

配方描述“这个镜头为什么动、怎么动、有哪些变体”；引擎负责“用什么运行时把它可靠地渲染出来”。先选配方，再选引擎。

## 当前规模

| 来源 | 配方卡 | 样式 | 引擎 | 当前状态 |
| --- | ---: | ---: | --- | --- |
| chaojifeng-video-content-creator 原生库 | 148 | 148 | HTML/GSAP + Hyperframes | `local-ready`，有本地 snippet 和 preview |
| video-shotcraft 固定快照 | 152 | 209 | Remotion | `upstream-source`，有上游源码和远程 preview |
| 统一 Gallery | 300 | 357 | 双引擎 | ID 无同名；仍需按视觉语义查重 |

## 配方合同

统一配方至少包含：

- `id` / `namespace`：稳定身份，跨来源用 namespace 避免冲突。
- `name` / `summary` / `intention` / `use`：用户可理解的名字、叙事意图和适用场景。
- `category` / `tags`：既保留骨架、容器、节拍等制作层级，也支持文字、镜头、数据、交互等运动维度。
- `engine`：`native` 或 `remotion`；Hyperframes 是 native HTML/GSAP 的离线渲染执行层。
- `runtimeStatus`：`local-ready` 或 `upstream-source`。
- `verification`：本地预览、上游预览、本地抽帧或本地成片等证据等级。
- `styles`：同一配方下的一个或多个具体运动样式。
- `source` / `preview` / `implementation`：来源说明、预览入口和实现入口，三者不可互相冒充。

## 引擎选择

优先用 `native`：口播字幕、HUD、产品卡、轻量容器和需要透明叠加的短节拍。它无需 React 工程，现有 Hyperframes 管线可直接复用。

优先用 `remotion`：复杂 2.5D/3D 镜头、粒子系统、数据场景、UI 多阶段编舞和需要严格按帧重放的配方。动画必须由 `useCurrentFrame()`、`interpolate()` 或 `spring()` 等帧驱动逻辑决定，不能依赖 CSS transition/animation。

## 验证状态

- `local-ready`：本机有实现与预览，但进入具体视频后仍需替换真实内容并抽帧。
- `upstream-source`：配方、源码和远程预览可查；尚未证明已在本机工程渲染。
- Remotion 配方完成本地接入与抽帧后，可另记本地实现状态；不得覆盖上游来源记录。
- 远程 MP4 能播放，只能证明上游提供了样片，不能替代本机渲染证据。

## 外部配方来源

video-shotcraft 快照固定到 commit `0d6f0b57f0d4d6700761644c07f7ef03c3e50234`。许可证、原始数据、规范化数据与来源说明位于 `recipes/video-shotcraft/`。本地不复制其音乐、音效或 209 个预览视频；Gallery 只在卡片接近视口或打开大图时按需读取远程 MP4。

## 原创转译

把 Remotion 配方转成原生 HTML/GSAP 时：

1. 先做视觉语义查重，确认原生库没有等价配方。
2. 保留叙事意图，重设中文名、参数和默认节奏。
3. 不复制品牌素材、第三方音频或无关示例文案。
4. 新增 native snippet、registry、preview 和叙事索引，不删除原 Remotion 配方。
5. 完成本地 preview、2–3 个关键帧和真实成片合成检查后，才能标成 `local-ready`。
