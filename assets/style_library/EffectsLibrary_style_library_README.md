# EffectsLibrary · style_library 文件夹说明书

## 核心功能

保存 chaojifeng-video-content-creator 的统一动效配方体系：148 个本地原生 HTML/GSAP 模式、152 张 Remotion 配方卡、209 个 Remotion 样式，以及可通过 `file://` 打开的统一 Gallery。

## 输入

- `registry.json`：本地原生特效事实源。
- `recipes/*/recipes.json`：外部或其他引擎的规范化配方快照。
- `snippets/`、`previews/`、`official/`：本地实现和预览材料。
- `snippets/light-route-flow-panel.html`：浅色路由流程浮层，包含横向场景总览与左侧竖向流程两种布局。

## 输出

- `gallery.html` / `index.html`：配方浏览入口。
- `registry.js` 与 `recipes/*/recipes.js`：兼容 `file://` 的浏览器数据。
- 可复制给 Agent 的双引擎配方调用说明。

## 定位

这是视频内容 Skill 的动效知识层与浏览入口，不是具体视频项目。具体项目仍在 `broll-overlay/` 或 Remotion 工程内实现并验证。

## 依赖

- 原生路线：HTML、CSS、GSAP、Hyperframes。
- Remotion 路线：React、Remotion 帧驱动组件及其项目运行环境。
- 上游配方：各 `recipes/<source>/SOURCE.md` 和 `LICENSE` 定义来源与授权。

## 维护规则

1. 原生模式变更必须同步 registry、snippet、preview、catalog 和 narrative-index。
2. 外部配方必须固定版本、保留许可证、生成来源说明，并明确本地或上游验证状态。
3. Gallery 不得一次性加载全部 iframe 或远程视频；保持 IntersectionObserver 按需加载。
4. 配方数据、页面结构或脚本职责变化时同步更新本文与相关文件说明书。
5. 架构变化需检查 `SKILL.md` 和 `references/assets-and-effects.md` 是否需要反向更新。

## 主要结构

```text
style_library/
├── gallery.html / gallery.css / gallery.js
├── registry.json / registry.js
├── recipe-system.md
├── snippets/ / previews/ / official/
├── recipes/video-shotcraft/
└── scripts/
```
