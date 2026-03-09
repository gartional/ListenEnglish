# ListenEnglish 打包成 Mac 应用

无需 GitHub / VPN，在 Mac 上直接运行。

## 方式一：先试运行（不打包）

在项目**上一级**目录打开终端，进入 `ListenEnglish`，再进 `desktop`：

```bash
cd ListenEnglish/desktop
npm install
npm start
```

会打开一个窗口，即练习页面。此时是从上一级目录读文件，无需先 `npm run copy`。

## 方式二：打包成 .app / .dmg（可发给别人）

在 `desktop` 目录下：

```bash
npm install
npm run dist
```

完成后在 `desktop/dist/` 里会有：

- **ListenEnglish.app**：双击即可运行
- **ListenEnglish-1.0.0.dmg**：可拖到「应用程序」或复制给他人

把整个 **ListenEnglish.app** 或 **.dmg** 拷到 Mac 上，双击即可使用，无需 Python、无需联网（复述需自己填 API Key 或使用浏览器麦克风）。

## 要求

- Mac 电脑
- 已安装 [Node.js](https://nodejs.org/)（建议 LTS）
