## ListenEnglish（内容抓取起步版）

- **子项目**：`app/` 为前端/应用子项目，入口为 `app/index.html`，详见 [app/README.md](app/README.md)。

这个仓库目前先解决一件事：把 **VOA Learning English** 的可用内容（文本 + MP3）**抓到本地**，让学生马上能练起来。

### 合规说明（必须看）

- **VOA Learning English** 明确说明其 Learning English 的文本/MP3/图片/视频属于 public domain，可用于教育和商业用途，但 **来自通讯社（AP/Reuters/AFP 等）的稿件/图片/视频属于版权内容，不能再发布**。
- 本项目脚本默认会**检测并跳过**含 “Associated Press / Reuters / AFP / AP Photo / via AP” 等痕迹的页面，避免踩线。

条款页面（VOA 官方）：`https://learningenglish.voanews.com/p/6861.html`

### 你会得到什么

运行一次抓取脚本后，会生成：

- `content/voa/index.json`：全部条目的索引（含跳过原因）
- `content/voa/items/<id>/meta.json`：单条元数据
- `content/voa/items/<id>/transcript.txt`：正文/稿件（纯文本段落）
- `content/voa/items/<id>/audio.mp3`：音频（优先 HQ）

### 运行方式（PowerShell）

在项目根目录运行：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\fetch_voa_learning_english.ps1 -MaxItemsPerFeed 30
```

如果你只想先“多抓一点”，把 `-MaxItemsPerFeed` 调大即可。

### 关于“音频有了但原文没抓到”

VOA 的 RSS 里经常混有一种页面：形如 `https://learningenglish.voanews.com/a/8008674.html` 这种 **纯音频剪辑页**，通常只有播放器没有正文，所以“原文”在页面里并不存在。

本项目脚本默认开启 `-RequireTranscript`，会跳过这类“无正文”的条目，确保你抓下来的内容是 **音频 + 英文原文**成对的。

### 让字幕“读到哪句高亮哪句”（强制对齐 / 最一致）

要做到音频与字幕同步，需要把每一句加上时间戳（生成 `captions.vtt` 或 `cues.json`）。

本项目提供两种方式：
- **Forced Alignment（理论上最一致）**：`scripts/align_voa_item.ps1`（当前在部分样本上可能失败，需要继续调参/诊断）
- **ASR + 原文对齐（推荐先跑起来）**：先做语音识别拿到“词级时间戳”，再把你的原文按词序对齐回去，最终字幕文本仍然是原文，但时间戳来自 ASR

#### 生成某一条内容的字幕

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\align_voa_item.ps1 -ItemDir .\content\voa\items\877f906f3748
```

生成：
- `content/voa/items/<id>/captions.vtt`
- `content/voa/items/<id>/cues.json`

#### 用 ASR 方式生成（先推荐这个）

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\align_voa_item_asr.ps1 -ItemDir .\content\voa\items\877f906f3748
```

#### 批量生成（先跑少量验证）

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\align_voa_all.ps1 -Limit 3
```

---

### 上传到网上让别人也能打开（模拟试题 17/30）

项目里的 **index.html、mock17-practice.html、mock30-practice.html** 以及 **content/mock17/**、**content/mock30/**（含音频、cues.json、cues-i18n.json）都是静态文件，可以上传到任意静态网站托管。

#### 方式一：GitHub Pages（免费）

1. 在 GitHub 新建一个仓库，把本项目代码推上去（可忽略 `.mamba`、大文件等，用 `.gitignore`）。
2. 仓库 → **Settings** → **Pages** → Source 选 **GitHub Actions** 或 **Deploy from a branch**，分支选 `main`，目录选 `/ (root)`。
3. 若用分支部署：根目录要作为站点根，访问地址为 `https://<用户名>.github.io/<仓库名>/`，首页为 `index.html`，别人打开即可看到「模拟试题 17 / 30」导航。

**注意**：音频需要支持「断点续传」（Range），GitHub Pages 对静态文件的 Range 支持因 CDN 而异；若进度条拖拽异常，可换下面的方式。

#### 方式二：Netlify / Vercel（免费，拖拽上传）

1. 打开 [Netlify](https://www.netlify.com/) 或 [Vercel](https://vercel.com/)。
2. 注册/登录后，选择 **Add new site** → **Deploy manually**（Netlify）或 **Import Project**（Vercel 可连 GitHub）。
3. **Netlify**：把整个项目文件夹拖进页面（或指定发布目录为项目根目录），等部署完成，会得到一个 `https://xxx.netlify.app` 的地址。
4. **Vercel**：若用 GitHub，选仓库后根目录即项目根，部署后得到 `https://xxx.vercel.app`。

两者默认对静态资源支持 Range，音频进度条拖拽一般正常。

#### 方式三：自己的服务器 / 虚拟主机

- 把 **index.html**、**mock17-practice.html**、**mock30-practice.html** 和 **content** 目录一起上传到网站根目录。
- 若用 Nginx：无需特别配置即可支持 Range；若用 Apache，一般也支持。
- 若只有 Python 环境：在服务器上运行 `python tools/serve_range.py 8000`，再用 Nginx 反向代理到 8000 端口即可。

#### 安全提醒（必读）

- **mock17-practice.html** 和 **mock30-practice.html** 里写入了默认的 **OpenAI API Key**（用于语音识别和翻译）。一旦上传到公开网站，任何人打开页面都能看到该 Key，可能被滥用、扣费。
- **建议**：
  - 若只是给熟人用、且能接受风险：可暂时保留，或定期在 OpenAI 后台轮换 Key。
  - 若要对陌生人开放：请删除 HTML 里的 `DEFAULT_STT_API_KEY`（及默认 URL），让他人自己填写自己的 Key，或改为用你自己的**后端接口**转发语音识别请求，Key 只存在服务器上。

