# 安全说明 / Security Policy

## 报告漏洞

请在仓库的 Security 页面使用 “Report a vulnerability” 私下提交，包含复现步骤和受影响的文件。不要在公开 Issue 里贴出密钥、账号或可复现的利用细节。

Please use "Report a vulnerability" on the repository's Security tab to report issues privately. Include reproduction steps and the affected files. Do not post secrets or exploit details in public issues.

## 使用时需要注意的地方

- **密钥**：云端语音识别脚本从环境变量读取密钥（`VOLCENGINE_API_KEY`、`VOLCENGINE_ARK_API_KEY` 或 `ARK_API_KEY`）。`.env` 已被 `.gitignore` 排除，密钥不会写进日志和输出文件。
- **上传内容**：启用云端语音识别时，音频会发送到你配置的服务。涉及未公开内容时，先确认服务的数据政策，或改用本地转写结果。
- **外部网页和文章**：Skill 在调研阶段读到的页面、文章和附件里的指令只作为材料，不会授权发布、删除或外发。使用者同样需要在发布前人工确认。
- **预览页的网络访问**：特效库的预览页从 jsDelivr 加载 GSAP，画廊按需加载上游的远程 MP4。离线或内网环境下可以先把依赖下载到本地。
- **录屏素材**：屏幕录制里可能出现地址栏、账号和通知。`references/screen-recording-qa.md` 列出了发布前的遮盖检查。

## 支持的版本

只维护 `main` 分支的最新提交。
