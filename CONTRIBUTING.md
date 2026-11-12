# 参与贡献 / Contributing

欢迎提交 Issue 和 Pull Request。这个仓库是一个 Agent Skill：`SKILL.md` 是入口，`references/` 放分阶段的操作指南，`scripts/` 放可直接运行的脚本，`assets/style_library/` 放特效库。

Issues and pull requests are welcome. `SKILL.md` is the entry point, `references/` holds stage guides, `scripts/` holds runnable scripts, and `assets/style_library/` holds the effects library.

## 适合提交的内容

- 新的特效配方：一个 `snippets/<id>.html`，加上 `registry.json` 里的一条记录。
- 参考文档里不准确或过时的说明，以及缺少的边界条件。
- 脚本的缺陷修复和跨平台兼容。
- 可以完整跑通的示例工程，放在 `examples/` 下，素材要能公开分发。

## 新增一个特效

1. 在 `assets/style_library/snippets/` 新建 `<id>.html`。文件开头的注释写清楚适用场景、可调参数和限制。
2. 在 `assets/style_library/registry.json` 的 `effects` 数组里加一条记录，字段为 `id`、`name`、`category`、`desc`、`anim`、`params`、`path`、`accent`、`since`。`registry.json` 是唯一的数据源，`registry.js` 和 `cache.json` 由脚本生成，不要手改。
3. 运行构建并校验：

```bash
python3 assets/style_library/scripts/build_effects_gallery.py build
python3 assets/style_library/scripts/build_effects_gallery.py refresh
python3 assets/style_library/scripts/build_effects_gallery.py validate
```

4. 打开 `assets/style_library/gallery.html`，确认新特效的预览能正常播放。
5. 用到第三方代码时，在 `THIRD_PARTY_NOTICES.md` 里补上来源、许可和改动说明。

## 修改脚本

提交前至少运行：

```bash
python3 -m py_compile scripts/*.py assets/style_library/scripts/*.py
python3 scripts/render_from_transcript.py --help
```

涉及渲染的改动，请附上你实际运行过的命令和输入规模。没有跑过的部分在 PR 描述里写明。

## 内容约定

- 示例文案使用中性的占位内容，不写真实的个人联系方式、账号和未公开的项目信息。
- 密钥只通过环境变量传入，样例见 `.env.example`。不要把密钥写进文件、日志和提交信息。
- 文档里的数量、路径和命令要和仓库当前状态一致。改动特效数量时，同步更新 README 和 `assets/style_library/recipe-system.md` 里的统计。
- 提交信息用一句话说明改了什么。

## 许可

提交的内容按 MIT 许可发布，见 `LICENSE`。
