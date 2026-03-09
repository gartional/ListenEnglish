# 在 Mac 上运行 ListenEnglish（不用 GitHub / VPN）

两种方式任选其一。

---

## 方式一：双击脚本运行（需已安装 Python 3）

1. 把整个 **ListenEnglish** 文件夹拷到 Mac（例如从 U 盘、网盘或本机复制）。
2. 在 Mac 上**右键** `run.command` → **打开**（第一次可能提示“无法打开”，再去 **系统设置 → 隐私与安全性** 里允许）。
3. 或打开 **终端**，执行：
   ```bash
   cd /路径/到/ListenEnglish
   chmod +x run.command
   ./run.command
   ```
4. 浏览器会自动打开 `http://localhost:8765/`，即可使用。
5. 用完后在运行脚本的窗口里**按回车**，关闭服务器。

**说明**：Mac 一般自带 Python 3，若提示“未找到 Python”，请先安装 [Python 3](https://www.python.org/downloads/)。

---

## 方式二：打包成 .app，双击即用（无需 Python）

适合想**直接双击一个应用**、或发给别人用的情况。

1. 在 Mac 上安装 [Node.js](https://nodejs.org/)（选 LTS）。
2. 把 **ListenEnglish** 文件夹拷到 Mac，打开 **终端**：
   ```bash
   cd /路径/到/ListenEnglish/desktop
   npm install
   npm run dist
   ```
3. 打包完成后，在 `desktop/dist/` 里会有：
   - **ListenEnglish.app**：双击运行
   - **ListenEnglish-1.0.0.dmg**：可安装或拷贝给他人
4. 把 **ListenEnglish.app** 拖到「应用程序」或任意位置，以后双击即可打开，无需再开终端、无需 Python、无需联网（复述需在页面里填 API Key 或允许麦克风）。

详见 **desktop/README.md**。
