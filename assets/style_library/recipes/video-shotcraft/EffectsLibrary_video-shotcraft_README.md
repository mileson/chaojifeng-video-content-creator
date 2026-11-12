# EffectsLibrary · video-shotcraft 文件夹说明书

## 核心功能

保存 video-shotcraft 的固定公开快照、规范化 Remotion 配方数据、来源说明和许可证。

## 输入

上游 GitHub Pages `api/library.json`、固定 Git commit 和仓库根 LICENSE。

## 输出

- `source-library.json`：上游原始数据快照。
- `recipes.json`：统一配方合同数据。
- `recipes.js`：供本地 `file://` Gallery 读取的全局变量。
- `SOURCE.md` / `LICENSE`：来源、版本、媒体策略和授权依据。

## 定位

这是外部 Remotion 配方数据源，不是本地 HTML snippet，也不代表 209 个样式已在本机完成 Remotion 渲染。

## 依赖

来源仓库 `Vincentwei1021/video-shotcraft`，固定 commit `0d6f0b57f0d4d6700761644c07f7ef03c3e50234`；Gallery 的远程视频预览依赖网络。

## 维护规则

1. 只能用 `scripts/import_video_shotcraft_recipes.py` 重建规范化快照。
2. 更新前先核对上游许可证、字段、数量和提交版本。
3. 不在本目录批量保存上游 MP4、音乐、音效或品牌素材。
4. `recipes.json` 与 `recipes.js` 的统计和内容必须一致。
5. 上游预览只标记 `upstream-preview`，本地渲染通过后另行记录验证证据。
