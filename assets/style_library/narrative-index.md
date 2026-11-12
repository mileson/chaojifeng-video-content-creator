# 叙事手法反查表（narrative-index）

**用途**：梳理场景节拍表（SKILL.md 第 3 步）之前必读。这张表回答「这段口播在讲 X，画面该用什么手法」——从叙事意图反查库内模式 id，让节拍表在规划阶段就绑定可直接实现的特效，前期规划与后期制作无缝衔接。

使用方式：逐句过 transcript 时，先判断口播段落属于下面哪种**叙事意图**，再从该组挑 1 个模式填进节拍表的「特效模式」列。选型拿不准时读 `catalog.md` 对应条目的结构/动画要点，或打开 `gallery.html` 看动效原型。

> 维护规则：新模式入库时必须同步把 id 加进本表对应意图组（入库四件套的 catalog 步骤包含本表）。

## 开场钩子（前 5s，必做节拍）

| 模式 | 选型场景 |
| --- | --- |
| `stamp-hook` | 反差钩子：先立靶（贵？难？）再砸出反转（¥0.2） |
| `split-char-headline` | 逐字大标题钩子，质感开场 |
| `logo-reveal-impact` | 产品发布/品牌定调型开场 |
| `editorial-headline-scrim` | 概念定义型开场（杂志编辑风暗化大标） |
| `caption-kinetic-slam` | 高密度短词连砸（口播信息量大、节奏快时） |

## 自我介绍 / 人物出场

| 模式 | 选型场景 |
| --- | --- |
| `lower-third-id` | 广电级下三分条（开场 3~6s 或嘉宾出场） |
| `identity-tags-card` | 片尾人设强化（与 follow-pill 双件套） |

## 概念引入 / 章节宣告

| 模式 | 选型场景 |
| --- | --- |
| `typewriter-keyword-card` | 引出一个核心概念词（打字机逐字 + 变色确认） |
| `keyword-decode` | 揭示产品名/方案名（乱码解码，AI/黑客感） |
| `chapter-step-card` | 章节步骤宣告（STEP · N/M） |
| `block-headline-mixed` | 金句/俗语关键词色块强调 |
| `brand-banner` / `shine-banner-neon` | 宣布方法组合（A × B）/ 核心卖点大字 |

## 痛点 / 问题呈现

| 模式 | 选型场景 |
| --- | --- |
| `terminal-error-hell` | 技术痛点：手动配置跑一半报错（红光+震动三连） |
| `message-feed-stack` | 业务痛点：消息轰炸/待办堆积（也可反转为 AI 解决） |
| `persona-card-trio` | 受众痛点点名：「如果你是 XX」对号入座 |
| `quote-card` / `praise-stack` | 引用他人吐槽/抱怨佐证痛点 |
| `hud-numbered-rules` | 「规律一/二」结论列（直贴暗部，配截图浮窗成左结论右证据） |
| `opinion-clash-card` | 争议铺垫：两派观点相向对峙（评论类冲突开局） |
| `news-breaking-banner` | 资讯开场抛事件（「就在今天，XX 发布了 XX」） |
| `search-query-suggest` | 话题热度铺垫（「打开搜索全是它」） |
| `hud-cross-points` | 「连 XX 都没有/不需要 XX」红✕否定连发（直贴暗部，反常识情绪） |

## 对比 / 转化（旧 vs 新、贵 vs 便宜）

| 模式 | 选型场景 |
| --- | --- |
| `before-after-split` | 全屏分屏强对比 + 红线划掉旧方式（情绪最强） |
| `vs-compare` | 红绿双面板 + VS 圆章（数据型对比） |
| `dual-column-list` | 逐行属性/流程对比（信息密度高） |
| `before-after-flow` | 演进叙事：旧卡 → 箭头 → 新卡（强调方向） |
| `state-cards-arrow` | 多状态转化链（A → B → C） |
| `flow-panels` | 正确做法 vs 错误做法（机制解释） |

## 数据论证 / 算账

| 模式 | 选型场景 |
| --- | --- |
| `calc-card` | 逐行算式推导结论 |
| `money-count-burst` | 算账结论时刻（count-up + 粒子爆发，单片 ≤2 次） |
| `countup-price` / `stat-hero-number` | 单个数字就是论点（印章 / 210px 大数字） |
| `bar-chart-compare` / `combo-chart` | 差距可视化（单维条形 / 双维柱+线） |
| `line-chart-dynamic` | 趋势/价格下降叙事 |
| `progress-ring` | 额度/占比/配额 |
| `glow-timeline-vertical` | 分步算账/时间线递进 |
| `bento-dashboard` | 多指标全景 + 单指标推近 |
| `donut-share-chart` | 占比构成（市场份额/成本构成/来源分布） |
| `leaderboard-rank` | 排行榜名次揭晓（benchmark/榜单，第一名压轴） |
| `hud-giant-stat` | 巨号裸数字直贴画面（暗部构图，「一句话砸一个数」） |
| `gauge-ring-mini` | 阈值/比率轻量仪表（150px 小环，不抢人物） |
| `chart-forecast-curve` | 趋势预测（实线→虚线+置信徽章，预测类杀手锏） |
| `hud-progress-overlay` | 「越用越准/能力成长」进度条直贴版（↑ 高亮 + fill 生长 + chips） |

## 产品演示 / 操作引导（录屏段）

| 模式 | 选型场景 |
| --- | --- |
| `screen-studio-frame` | 包装录屏：壁纸框 + 自动变焦推近核心操作区 |
| `window-pip-desktop` / `device-pip-phone` | 桌面/手机画中画（内容必须「活」） |
| `screenshot-float-panel` | 通用截图浮窗（发光描边+漂浮，长短截图都能装） |
| `screenshot-takeover-wall` | 重点演示全貌：全屏接管 + 品牌水印墙（防搬运） |
| `hud-corner-brackets` | 圈出关键按钮（「看这里」，取景框+扫描线） |
| `cursor-click-spotlight` | 强化关键点击动作（光标礼仪：停顿 0.5s 再点） |
| `drift-camera-motion` | 给录屏/视频底片加「漂移运镜」：左右漂摆、轻旋转、前半段运动模糊 |
| `spotlight-dim` / `annotate-arrow-box` | 调暗聚焦 / 手绘箭头轻量标注 |
| `install-progress-checklist` | 「一键安装全自动」进度+打勾流 |
| `code-editor-typing` | 展示关键代码/命令（VS Code 风打字） |
| `code-diff-card` | 「把这行改成那行」红删绿增对比（修 bug/配置变更教程） |
| `file-tree-reveal` | 讲项目结构/「核心文件在哪」导览 |
| `keyboard-shortcut-combo` | 教快捷键/命令面板（键帽按压发光） |
| `typewriter-terminal` | 终端命令演示（宣布发布/上线） |
| `ai-chat-stream` | AI 问答演示/prompt 教学（流式逐字输出） |
| `timelapse-timer-badge` | 倍速演示段叠「真实计时」角标 |

## 架构 / 流程 / 多角色

| 模式 | 选型场景 |
| --- | --- |
| `agent-team-grid` | 多 Agent/多角色矩阵（运行状态呼吸） |
| `light-route-flow-panel` | 浅色路由流程浮层：先用左上横向总览列出多个场景，再用左侧竖向流程连续讲解当前步骤与角色 |
| `glass-panel-network` | 模块协作总览（玻璃面板+虚线网络） |
| `flow-decision-tree` | 「你该选哪个方案」决策树逐层展开 |
| `map-markers` | 多地分布/全球化 |

## 社会证明 / 引用佐证

| 模式 | 选型场景 |
| --- | --- |
| `social-post-card` | 引用大V/官方推文（比截图干净，带点赞微交互） |
| `praise-stack` / `evidence-grid-stamp` | 截图瀑布铺垫 / 多方证据+盖章定论 |
| `quote-card` / `excerpt-strip` | 单条引用大卡 / 左结论右证据摘录 |
| `macos-notification-stack` | 系统通知播报关键事件（真实感） |

## 卖点专项

| 模式 | 选型场景 |
| --- | --- |
| `data-shield-local` | 隐私/本地化卖点（盾牌+切断云端） |
| `glass-hud-card` | 信息容器（商业科技感引用/参数卡） |
| `icon-chip-row` | 罗列 2~5 个能力点 |
| `ui-3d-reveal-card` | 单个功能点发布会级出场（3D 透视翻入） |
| `app-triple-screens` | 产品多界面总览（三机浮动矩阵） |
| `pricing-tier-cards` | 公布定价/档位对比（推荐档高亮） |
| `app-store-rating` | 社证：评分+星星点亮+精选好评 |
| `changelog-ship-card` | 版本发布/Build in public 周报（SHIPPED 印章） |
| `github-repo-card` | 「我把它开源了」GitHub 仓库卡 + star 引导（开源宣布标准画面） |

## 情绪爆点（全片 ≤1 次）

| 模式 | 选型场景 |
| --- | --- |
| `particle-burst-keyword` | 关键词砸入+彩色粒子爆裂（唯一情绪最高点） |
| `caption-karaoke` | 一句核心论断逐词点亮（按口播时间戳） |

## 总结 / 片尾转化

| 模式 | 选型场景 |
| --- | --- |
| `summary-card` | 要点总结清单（卡片版） |
| `hud-takeaway-overlay` | 要点铺垫+结论标语压轴（无卡直贴版，「所以说」收口节拍） |
| `follow-pill` | 关注/订阅引导 |
| `url-cta-bar` | 官网+平台徽章+下载按钮（产品转化） |
| `logo-outro-assemble` | 片尾 5s 品牌定格装配 |
| `outro-author-works` | 固定作品墙片尾（不透明拼接段，教程/产品类选择性追加；合规无二维码无网址） |

## 片尾家族（按收尾意图选型，全部不透明拼接段）

| 收尾意图 | 模式 |
| --- | --- |
| 展示作品矩阵（通用） | `outro-author-works` |
| 展示作品矩阵（有主推产品/发布盘点） | `outro-bento-works` |
| 求关注转化 | `outro-follow-endscreen` |
| 追更钩子（下期预告） | `outro-next-episode` |
| 系列连载导航（第 N 集） | `outro-series-nav` |
| 干货回顾（完播价值感） | `outro-takeaway-recap` |
| 透明工具链（Build in Public） | `outro-credits-roll` |
| 本期数据复盘 | `outro-stats-recap` |
| 拉评论互动 | `outro-question-comment` |
| 产品搜索引导（合规转化） | `outro-search-cta` |
| 留住最后 5s（彩蛋） | `outro-countdown-tease` |
| 品牌收束兜底（接任何片尾后） | `outro-brand-signoff` |
| 克制签名（深度/情绪向） | `outro-minimal-signature` |

## 产品展示 / 讲到一款产品（预置卡，免找素材）

| 模式 | 选型场景 |
| --- | --- |
| `product-card-app` | 讲到一款 App（图标 + 名称 + iOS App 徽章 + 一句话） |
| `product-card-web` | 讲到一个网站或在线工具（网站徽章） |
| `product-card-opensource` | 讲到一个 GitHub 开源项目（开源徽章） |
| `product-card-desktop` | 讲到一款桌面客户端（客户端徽章） |

> 换成自己的产品：运行 `python3 assets/style_library/scripts/gen_product_cards.py --config products.json`，再按「入库四件套」登记。

## 骨架层（常驻，单独 track，教程类必配）

| 模式 | 选型场景 |
| --- | --- |
| `hud-title-corner` | 全片标题锚点（左上角，**卡片版**，亮色素材安全） |
| `hud-step-checklist` | 步骤渐进清单（01/02…） |
| `hud-progress-meter` | 指标进度驻留 |
| `kpi-ticker-strip` | 底部行情滚动条（数据氛围） |
| `hud-kicker-overlay` | 章节标识**无卡直贴版**（暗部构图素材专用） |
| `hud-icon-checklist-overlay` | 左列图标双语清单无卡直贴版（与 kicker 同屏组左列） |

## 转场（密度 ≤ 每 20s 一次，选型细则见 catalog「转场使用规则」）

- 覆盖式（不打断底片）：`transition-circle-iris` / `transition-countdown` / `transition-blinds`
- 全屏接管（CSS 系）：`transition-chapter-card` / `transition-wipe-band` / `transition-grid-flip` / `transition-pixel-dissolve`
- 全屏接管（shader 系，单片 ≤2 次）：`transition-shader-glitch` / `shader-whip-pan` / `shader-sdf-iris` / `shader-cinematic-zoom` / `shader-flash-white`
- 半接管（语义聚焦）：`transition-parallax-zoom`（全景矩阵→聚焦单项；reverse 反向 = 结尾缩回全景总结）
- 整帧组合（轻快切段）：`elastic-focus-zoom`（弹性伸缩）/ `continuous-slide-loop`（连续滑屏）/ `arc-sway-camera`（横摆运镜）

## 氛围工具（独立 track 叠加）

| 模式 | 选型场景 |
| --- | --- |
| `film-grain-vignette` | 片尾段/情绪段电影质感 |
| `motion-blur-util` | 高速横移元素加速度感 |
| `light-leak-overlay` | 胶片漏光暖意（情绪段/产品美图段，可与颗粒叠用） |
| `letterbox-cinema` | 情绪段/引言段切 2.35:1 电影画幅 + 底部引言 |
| `color-wash-mood` | 黑白闪回（回忆）/ 红色警示（踩坑）/ 青橙（高光时刻） |
| `mesh-gradient-bg` | 片头/片尾/全屏文字卡的流动渐变底 |
| `marquee-keyword-belt` | 开场关键词/技术栈跑马灯 ticker |

## 镜头语言工具（操控底片容器，独立调用）

| 模式 | 选型场景 |
| --- | --- |
| `zoom-punch-rig` | 讲到关键 UI/数据时推近强调（punchIn/punchOut） |
| `camera-shake-impact` | 报错/吓一跳/重点砸下的震屏（shakeAt） |
| `screen-flash-impact` | 反转/揭晓的白闪冲击帧（flashAt，同镜头 ≤2 次） |

## 视线引导工具（录屏/截图标注）

| 模式 | 选型场景 |
| --- | --- |
| `spotlight-follow-mask` | 依次聚焦多个 UI 区域（spotTo 编排） |
| `magnifier-loupe` | 小字/价格/角标放大细看 |
| `arrow-scribble-pack` | 手绘箭头指点/圈选/划重点 |
| `privacy-blur-patch` | 敏感信息打码（API Key/邮箱/金额） |

## 节奏点缀工具（情绪放大器）

| 模式 | 选型场景 |
| --- | --- |
| `speed-lines-radial` | 吐槽/惊讶的漫画式速度线 |
| `confetti-burst` | 上线/过审/破纪录的庆祝彩带 |
| `shimmer-sweep-util` | 文字/卡片/logo 高光扫过提质感 |
