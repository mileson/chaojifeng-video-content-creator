<!-- 提示：做新效果前先运行 `npx hyperframes catalog` 查官方组件库（shader 转场、caption 特效、shimmer-sweep、motion-blur 等），
     `npx hyperframes docs gsap` 是官方 GSAP 集成规范；`npx hyperframes snapshot . --at <秒>` 可不渲染快速抓帧 QA。 -->

# GSAP 官方最佳实践（overlay 场景蒸馏版）

提炼自 GSAP 官方 skills 仓库（gsap-core / gsap-timeline / gsap-utils / gsap-performance / SplitText），按本 skill 的离线渲染场景（hyperframes 逐帧渲染 HTML+GSAP → 透明 WebM，无滚动、无交互、无 React）裁剪。**写 composition 前先扫一遍本文，每条都是可直接落地的代码规则。**

## 1. 属性选择铁律（性能 + 渲染确定性）

| 用 | 不用 | 原因 |
| --- | --- | --- |
| `x` / `y` | `left` / `top` / `margin` | transform 走合成层，不触发 layout；逐帧渲染下结果更确定 |
| `scale` / `scaleX` / `scaleY` | `width` / `height` | 同上；缩放文字不会触发 reflow 重排 |
| `rotation` | CSS `transform: rotate()` 动画 | GSAP 统一管理 transform，避免互相覆盖 |
| `autoAlpha` | `opacity` | autoAlpha 到 0 时自动加 `visibility: hidden`，彻底消除半透明残影（抽帧 QA 高频问题） |

补充规则：

- 动画元素在 CSS 里声明 `will-change: transform`，**只给真正动的元素加**，不要全局撒
- 出场用 `autoAlpha: 0` 替代 `opacity: 0`，可消灭「出场尾帧残影」这类返工
- 布局（居中、堆叠）全部交给 CSS（flex / margin auto / inset），**transform 完全留给 GSAP**（与 hyperframes-lessons 的 transform 冲突规则同源）

## 2. Timeline 编排框架（节拍模块化）

### 2.1 defaults：统一手感

```js
const tl = gsap.timeline({ paused: true, defaults: { duration: 0.5, ease: "power3.out" } });
```

所有子 tween 继承 defaults，单条覆盖即可。一个 composition 的「动画手感」由 defaults 定基调，避免每条 tween 手抄 ease。

### 2.2 每个节拍一个子 timeline（嵌套结构）

节拍多于 4 个时，扁平大 timeline 难维护。官方推荐嵌套：

```js
function beatHook(t0) {
  const b = gsap.timeline({ defaults: { ease: "power3.out" } });
  b.from("#b1 .title", { y: 60, autoAlpha: 0, duration: .5 })
   .from("#b1 .tag",   { scale: 0, ease: "back.out(2)" }, "-=0.2")
   .addLabel("hold")
   .to("#b1", { autoAlpha: 0, duration: .4, ease: "power2.in" }, "+=2.5");
  return b;
}
tl.add(beatHook(), 3.2);   // 节拍内部用相对时序，挂载点用绝对秒
```

好处：**节拍内部全用相对时序（`"-=0.2"` / `"+=1"` / label），只有挂载点是绝对秒**。改节拍 start 只动一个数字，内部编排不用重算——这是对旧「全绝对秒」写法的直接升级。

### 2.3 position 参数完整语法

| 写法 | 含义 |
| --- | --- |
| `3.2` | 绝对秒（相对所属 timeline 起点） |
| `"+=0.5"` / `"-=0.2"` | 相对上一条动画**结束点**偏移 |
| `"<"` | 与上一条动画**同时开始**（多元素齐入场必备） |
| `"<0.15"` | 上一条开始后 0.15s（紧跟节奏的层叠入场） |
| `">"` | 上一条结束时（默认行为） |
| `"label"` / `"label+=0.3"` | 锚定到 `addLabel()` 的标签 |

`"<"` 和 `"<0.15"` 是做「主体 + 装饰物几乎同时入场」的正确姿势，比手算绝对秒可读得多。

## 3. Easing 语义表

| 场景 | ease | 备注 |
| --- | --- | --- |
| 入场（卡片/横幅） | `power3.out` / `expo.out` | 快进慢停，干净利落 |
| 入场（活泼/弹性） | `back.out(1.3~2)` | 过冲回弹；参数越大越夸张 |
| 入场（重点强调物） | `elastic.out(1, 0.5~0.6)` | 弹簧感；只给一两个主角用，多了廉价 |
| 砸下/盖章 | `power4.in` | 加速砸落，落点接小回弹 |
| 出场（统一） | `power2.in` | 慢起快走；出场永远比入场低调 |
| 强调脉冲 | `power1.inOut` + `repeat: 3~5, yoyo: true` | scale 1.04~1.08 |
| 数字滚动 | `power1.inOut` 或 `power2.out` | 线性会显得机械 |

原则：**一个 composition 入场 ease 不超过 3 种**，否则手感杂乱。

## 4. Stagger 高级用法

数值 stagger（`stagger: 0.12`）只是入门。官方对象写法：

```js
// 从中心向两侧荡开（网格/瀑布卡片入场质感升级）
gsap.from(".card", {
  y: 40, autoAlpha: 0, duration: .5,
  stagger: { each: 0.12, from: "center" }   // "start"|"center"|"end"|"edges"|"random"|索引
});

// amount 模式：不管几个元素，总耗时锁定 0.6s（节拍时长固定时用）
gsap.from(".item", { y: 30, autoAlpha: 0, stagger: { amount: 0.6, from: "edges" } });
```

配套 `distribute`：按位置分布数值（中心大、两侧小的缩放入场）：

```js
gsap.from(".card", {
  scale: gsap.utils.distribute({ base: 0.7, amount: 0.5, from: "center" }),
  autoAlpha: 0, stagger: { each: 0.1, from: "center" }
});
```

## 5. utils 工具箱（overlay 高频四件套）

```js
// ① interpolate + 数字滚动（算账卡/价格 count-up 的标准范式，见 §6）
gsap.utils.interpolate(0, 135, 0.5)            // 67.5；也支持颜色与对象

// ② random：贴纸/装饰物有机感（每个元素角度/位移略不同）
gsap.from(".sticker", { rotation: "random(-12, 12)", y: "random(40, 80)", autoAlpha: 0, stagger: 0.08 });

// ③ snap：数值滚动时吸附到步进（价格只显示一位小数）
gsap.utils.snap(0.1, 0.27)                      // 0.3

// ④ clamp / mapRange：素材尺寸自适应换算
gsap.utils.mapRange(0, 136, 0, 1, t)            // 时间 → 进度
```

## 6. 数字滚动（count-up）标准范式

算账卡、价格、百分比的质感升级——不要直接淡入终值，让数字滚上去：

```js
const priceObj = { v: 0 };
tl.to(priceObj, {
  v: 0.2, duration: 1.2, ease: "power2.out",
  onUpdate() {
    document.querySelector("#price").textContent = "¥" + priceObj.v.toFixed(1);
  }
}, t0 + 1.0);
```

要点：

- 容器必须 `font-variant-numeric: tabular-nums`，否则数字宽度跳动
- hyperframes 逐帧渲染会逐帧执行 `onUpdate`，所见即所得，放心用
- 大数字（播放量、金额）配 `Math.floor` + 千分位格式化

## 7. SplitText 逐字入场（标题质感天花板）

GSAP 3.13+ 起 SplitText 免费。CDN 直接加载（与 gsap 同版本号）：

```html
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/SplitText.min.js"></script>
<script>
  gsap.registerPlugin(SplitText);
  const split = SplitText.create("#b1 .headline", { type: "chars" });
  tl.from(split.chars, {
    y: 80, autoAlpha: 0, rotationX: -90, duration: .5,
    ease: "back.out(1.7)", stagger: { each: 0.035, from: "start" }
  }, t0 + 0.2);
</script>
```

要点：

- 中文按 chars 切分自然（无连字问题）；英文长句建议 `type: "words"` 防止断词怪异
- 只 split 真正要逐字动画的标题，正文卡片不要滥用（渲染节点数暴涨）
- `mask: "chars"` 可做「从遮罩里升起」的高级 reveal（每字裹一层 `overflow: clip`）
- split 后的 char 是 `display: inline-block`，自带 transform 能力，可直接动 `y/rotationX`

## 8. 离线渲染特有技法（与浏览器运行时的关键差异）

hyperframes 是逐帧离线渲染，性能规则的定位和浏览器运行时不同：

- **§1 的 transform 规则保留的理由是「确定性 + 避免 CSS/GSAP 冲突」**，不是帧率——离线渲染不掉帧
- 因此可以放心使用运行时昂贵的视觉属性：多层 `text-shadow` 霓虹 glow、`linear-gradient` 发光条、大范围 `box-shadow`、`filter` 等，**质感优先**
- **`backdrop-filter` 在透明 overlay 上完全无效**：底层视频不在 DOM 里，没有东西可以模糊。毛玻璃必须伪造：半透明深色底（`rgba(16,18,26,.82~.92)`）+ 1.5px 白描边（`rgba(255,255,255,.14~.18)`）+ 黑色大外发光 + 品牌色 glow
- **聚焦调暗万能洞**：透明 div + `box-shadow: 0 0 0 9999px rgba(0,0,0,.5)`，洞外全暗。节拍容器加 `data-layout-allow-overflow`、洞框加 `data-layout-ignore`
- **打字机**：对象属性 + `onUpdate` 做字符串 slice，`ease: "none"` 匀速才像打字；光标用 `repeat + yoyo` 闪烁
- **高光扫过（shine sweep）**：容器 `overflow: hidden`，内部放斜渐变条，`fromTo` x 从容器左外扫到右外，`power2.inOut`

## 9. 落地检查清单（写完 composition 自查）

- [ ] 所有位移/缩放走 `x/y/scale`，没有动 `left/top/width/height`
- [ ] 出场全部 `autoAlpha`，不是 `opacity`
- [ ] timeline 有 `defaults`；入场 ease ≤ 3 种；出场统一 `power2.in`
- [ ] 节拍 ≥ 4 个时用「子 timeline + 绝对秒挂载」结构
- [ ] 多元素入场用 stagger 对象（`from: "center"/"edges"`），不是手抄 delay
- [ ] 数字类内容用 count-up 范式 + `tabular-nums`
- [ ] 动画元素 CSS 有 `will-change: transform`
