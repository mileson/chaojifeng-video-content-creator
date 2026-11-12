# EffectsLibrary · scripts 文件夹说明书

## 核心功能

维护本地原生预览与外部 Remotion 配方快照，提供构建、刷新、校验和导入入口。

## 输入

`registry.json`、原生 snippets、外部公开配方 JSON、固定上游 commit 与许可证。

## 输出

原生 previews/cache/registry.js，以及 `recipes/<source>/` 下的规范化 JSON、JS、LICENSE 和 SOURCE.md。

## 定位

统一配方库的离线维护工具目录；脚本生成结果供 Gallery 和 Agent 使用，不负责具体视频渲染。

## 依赖

Python 3 标准库；原生预览页运行时使用浏览器和 GSAP。脚本不得隐式安装依赖或启动常驻服务。

## 维护规则

1. 脚本字段映射变化时同步更新 `recipe-system.md` 和 style_library 文件夹说明书。
2. 导入外部来源必须固定版本并保留许可证。
3. 不得用远程预览替代本地渲染验证。
4. 代码变更后运行 `py_compile` 和对应 validate/count 检查。

## 脚本索引

- `build_effects_gallery.py`：构建和校验本地原生 previews，刷新 `cache.json` 与 `registry.js`；默认处理 `assets/style_library`，可用 `--effects-dir` 指向其他目录。
- `gen_product_cards.py`：按产品列表生成 `product-card-*` 片段，默认输出 4 张通用卡片，可用 `--config` 传入自己的产品清单。
- `import_video_shotcraft_recipes.py`：导入固定 video-shotcraft 配方快照，不修改原生 registry。
