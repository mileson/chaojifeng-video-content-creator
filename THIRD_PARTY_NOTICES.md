# Third-Party Notices / 第三方内容说明

This repository is released under the MIT License (see `LICENSE`). The material listed below was created by others and keeps its own license.

本仓库以 MIT 许可发布（见 `LICENSE`）。下列内容来自第三方，各自保留原有许可。

## 1. video-shotcraft recipe library (Apache-2.0)

- Upstream: <https://github.com/Vincentwei1021/video-shotcraft>
- Pinned commit: `0d6f0b57f0d4d6700761644c07f7ef03c3e50234`
- Location: `assets/style_library/recipes/video-shotcraft/` (`recipes.json`, `recipes.js`, `source-library.json`, `LICENSE`, `SOURCE.md`)
- Local changes: field normalization, absolute-link completion, and engine/verification labels. See `SOURCE.md` in that folder.
- Media: no upstream video, music or sound effects are copied. The gallery loads remote MP4 previews on demand.
- License: Apache License 2.0. The upstream license text is kept at `assets/style_library/recipes/video-shotcraft/LICENSE`.

## 2. Hyperframes catalog components (Apache-2.0)

- Upstream: <https://github.com/heygen-com/hyperframes> (Copyright 2026 HeyGen, Inc.)
- License text: `licenses/Hyperframes-LICENSE.txt`
- Files that include or are adapted from Hyperframes catalog components:
  - `assets/style_library/official/` (all six pages: `motion-blur`, `glitch`, `whip-pan`, `sdf-iris`, `cinematic-zoom`, `flash-through-white`)
  - `assets/style_library/snippets/motion-blur-util.html`
  - `assets/style_library/snippets/transition-shader-pack.html`
  - `assets/style_library/snippets/transition-shader-glitch.html`
  - `assets/style_library/snippets/shader-whip-pan.html`
  - `assets/style_library/snippets/shader-sdf-iris.html`
  - `assets/style_library/snippets/shader-cinematic-zoom.html`
  - `assets/style_library/snippets/shader-flash-white.html`
  - structure or ideas borrowed from Hyperframes catalog components and re-implemented in `assets/style_library/snippets/`: `caption-karaoke` (caption-highlight), `caption-kinetic-slam`, `keyword-decode` (caption-matrix-decode), `combo-chart` (data-chart), `logo-outro-assemble` (logo-outro), `lower-third-id` (yt-lower-third), `macos-notification-stack` (macos-notification), `money-count-burst` (apple-money-count), `shimmer-sweep-util` (shimmer-sweep), `social-post-card` (x-post), `transition-pixel-dissolve` (grid-pixelate-wipe)
  - the generated previews with the same file names under `assets/style_library/previews/`
- Changes: adapted to a 1920x1080 overlay workflow, split into single-effect snippets, and wrapped in preview pages. The `motion-blur` component keeps its original API comments.

## 3. GSAP (not redistributed)

Preview pages load GSAP and SplitText from the jsDelivr CDN when opened in a browser (`https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/`). No GSAP files are stored in this repository. GSAP is subject to its own license: <https://gsap.com/community/standard-license/>.

## 4. Tools you install separately

FFmpeg / ffprobe, the Hyperframes CLI (`npx hyperframes`) and cloud speech recognition services are not bundled. Install and license them on your own machine. Each has its own terms of use.

## 5. Public article used as a source of experience

`references/distribution-risk-knowledge.md` organizes the experience described in a public post by its author, with a link and a note on how far the evidence goes. The post stays the property of its author: <https://x.com/hmq1048762/status/2107043028229906793>.
