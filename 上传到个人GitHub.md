# 把项目上传到你自己（个人）的 GitHub

按下面顺序做即可，保证仓库建在**你的个人账号**下，而不是公司 Organization。

---

## 第一步：在 GitHub 上建一个「你自己的」仓库

1. 打开 **https://github.com**，用**个人账号**登录（不要用公司账号）。
2. 右上角点 **“+”** → **“New repository”**。
3. 填写：
   - **Repository name**：例如 `ListenEnglish`（或任意英文名）。
   - **Description**：可选，如「英语听力模拟试题 17/30 逐句复述」。
   - **Public** 选上（别人才能打开 GitHub Pages）。
   - **不要**勾选 “Add a README” / “Add .gitignore”（你本地已有文件）。
4. 点 **“Create repository”**。
5. 建好后会看到一个空仓库页面，记下**仓库地址**，形如：
   - `https://github.com/你的用户名/ListenEnglish`
   - 或 SSH：`git@github.com:你的用户名/ListenEnglish.git`

只要这个地址里的「你的用户名」是你个人账号，就是个人页面，不是公司的。

---

## 第二步：在电脑上用 Git 上传（二选一）

### 方式 A：用 Cursor / VS Code 的「源代码管理」上传

1. 在 Cursor 里打开本项目文件夹 `ListenEnglish`。
2. 左侧点 **“源代码管理”**（或 Git 图标）。
3. 若提示「未初始化 Git 仓库」：
   - 点 **“初始化存储库”**。
4. 在「消息」框里输入一次提交说明，如 `首次上传`，然后点 **✓ 提交**。
5. 点 **“发布分支”** 或 **“推送”**：
   - 若让你选远程：选 **GitHub**，然后选**你的个人账号**。
   - 选择刚建好的仓库（例如 `你的用户名/ListenEnglish`），确定。
6. 完成后，在浏览器里刷新你的 GitHub 仓库页面，就能看到代码。

### 方式 B：用命令行（需先安装 Git）

1. 安装 Git for Windows：https://git-scm.com/download/win  
   安装时若可选 “Add Git to PATH”，建议勾选。

2. 打开 **Git Bash** 或 **命令提示符**，进入项目目录：
   ```bash
   cd C:\Users\Abuomar\Documents\ListenEnglish
   ```

3. 若从未在本文件夹初始化过 Git：
   ```bash
   git init
   ```

4. 添加所有文件并第一次提交：
   ```bash
   git add .
   git commit -m "首次上传：模拟试题 17/30 逐句复述"
   ```

5. 把远程仓库设成**你自己的** GitHub 地址（把 `你的用户名` 和 `ListenEnglish` 换成你的）：
   ```bash
   git remote add origin https://github.com/你的用户名/ListenEnglish.git
   ```

6. 推送到 GitHub（分支名一般是 `main` 或 `master`）：
   ```bash
   git branch -M main
   git push -u origin main
   ```
   若提示登录，用浏览器或弹窗登录**你的个人 GitHub 账号**即可。

---

## 第三步：确认是个人页面而不是公司的

- 在浏览器打开：`https://github.com/你的用户名/ListenEnglish`
- 看页面左上角或仓库名下面：显示的是**你的个人头像和用户名**，就说明是个人仓库。
- 若你误选成了公司 Organization，在仓库 **Settings** 里一般无法直接“转移”到个人，需要重新在个人账号下 **New repository**，再用上面的步骤把本地 `origin` 改成新仓库地址后重新 `git push`。

---

## 第四步：开启 GitHub Pages（让别人能打开网页）

1. 在你的仓库页面点 **Settings**。
2. 左侧选 **Pages**。
3. 在 **Build and deployment** 里：
   - **Source** 选 **Deploy from a branch**。
   - **Branch** 选 `main`（或你推送的分支），右边选 **/ (root)**。
4. 点 **Save**。
5. 等一两分钟，访问：`https://你的用户名.github.io/ListenEnglish/`  
   就能看到「英语听力 · 模拟试题」导航页，别人用这个链接即可打开。

---

## 小结

| 要做的事           | 说明 |
|--------------------|------|
| 建仓库             | 在 **个人账号** 下 New repository，不要选公司。 |
| 上传代码           | Cursor 用「发布分支」到该仓库，或命令行 `git remote add origin` + `git push`。 |
| 确认是个人         | 仓库 URL 是 `github.com/你的用户名/...`。 |
| 让别人能打开       | Settings → Pages → 选 branch `main`、目录 `/ (root)`，用 `用户名.github.io/仓库名/` 访问。 |

如果你在某一步卡住（例如 Cursor 里没有 Git、或推送时问你要选哪个账号），可以说一下你卡在哪一步，我按那一步给你写具体操作。
