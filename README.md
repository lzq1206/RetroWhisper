# RetroWhisper

RetroWhisper 是一个复古开源推荐墙：从 GitHub 发现游戏、模拟器、像素编辑器和复古工具，并用瀑布流呈现。默认进入 Win 98 风格，也可以切换到 Pixel 或 Vista Aero：

- 像素终端：8-bit 点块、硬边框、跳色、像素网格和等宽字形，不使用连续照片封面。
- Win 98：青绿色桌面、灰色凸起面板、蓝色标题栏和经典按钮边框。
- Vista 玻璃：Aero 半透明玻璃、天空/草地渐变、拟物按钮、多层阴影和玻璃高光。

## 设计参考

三套风格的实现参考了 [98.css](https://github.com/jdan/98.css/) 的 Windows 98 凸起/凹陷控件语言、[Pixel-art-8-bit](https://github.com/Team-Parashuram/Pixel-art-8-bit) 的硬边框与像素网格，以及 [Frutiger Aero design guide](https://github.com/lumusitech/AI/blob/main/skills/design-it/frutiger-aero/SKILL.md) 的玻璃、天空/草地渐变和顶部高光。页面保留 RetroWhisper 自己的信息架构，没有直接复制第三方页面模板。

## 本地预览

这是一个无依赖的静态站点。进入仓库目录后运行任意静态文件服务器即可，例如：

```bash
python -m http.server 4173
```

然后打开 <http://localhost:4173>。

## 自动抓取

`.github/workflows/fetch-repositories.yml` 每 6 小时运行一次，也可以在 Actions 页面手动触发。它会：

1. 使用 GitHub Search API 搜索 retro、retrogaming、pixel-art、emulator 等信号。
2. 结合热度、主题标签、更新活跃度和人工精选项目，筛选 10 个公开仓库。
3. 将结果写入 `data/repositories.json`。
4. 如果数据发生变化，由 `github-actions[bot]` 自动提交回仓库。

GitHub Pages 的部署由 `.github/workflows/deploy-pages.yml` 负责。首次使用时，请在仓库的 **Settings → Pages** 中将构建来源设为 **GitHub Actions**。

## 目录

```text
index.html                     页面结构
styles.css                     三套风格和响应式布局
app.js                         瀑布流、筛选、搜索和风格切换
data/repositories.json         当前十条推荐
scripts/fetch_repositories.py  GitHub API 抓取器
.github/workflows/              定时抓取与 Pages 部署
```
