# ListenEnglish · App（子项目）

ListenEnglish 下的前端/应用子项目，用于浏览和练习 VOA Learning English 内容。

## 与主项目关系

- **内容来源**：使用主项目抓取并生成的字幕数据，路径为 `../content/voa/`。
- **根目录**：`voa-practice.html`、`start-server.bat` 等为原有入口，本子项目可逐步承接或扩展为独立应用。

## 目录结构

```
app/
├── README.md       # 本说明
├── index.html      # 应用入口
└── (后续可加) src/、static/、package.json 等
```

## 本地运行

在 ListenEnglish 根目录已有 `start-server.bat` 时，启动后访问子项目入口，例如：

- 在项目根目录运行 `start-server.bat` 后访问：`http://127.0.0.1:8000/app/`
- 或用 VS Code Live Server 等直接打开 `app/index.html`

## 后续可做

- 从 `../content/voa/index.json` 读取条目列表，做选篇/列表页；
- 复用或迁移根目录的 `voa-practice.html` 播放与字幕逻辑；
- 按需引入构建工具（如 npm/Vite）与 `package.json`。
