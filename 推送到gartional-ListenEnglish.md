# 推送到 gartional/ListenEnglish

你的仓库地址：**https://github.com/gartional/ListenEnglish**

按下面做即可把本地项目推上去。

---

## 在 Cursor 里（推荐）

1. 左侧点 **源代码管理**（或按 `Ctrl+Shift+G`）。
2. 若提示「未初始化 Git 仓库」→ 点 **初始化存储库**。
3. 在「更改」里勾选要上传的文件（或点 **+** 全选），在「消息」框输入：`首次上传`，点 **✓ 提交**。
4. 点 **「发布分支」** 或 **「推送」**：
   - 若让你选远程：选 **GitHub**，仓库选 **gartional/ListenEnglish**。
   - 或先点 **「⋯」** → **「远程」** → **「添加远程」**，名称填 `origin`，URL 填：
     ```
     https://github.com/gartional/ListenEnglish.git
     ```
     再推送。

---

## 用命令行（Git Bash 或 命令提示符）

在项目目录下执行（一行一行来）：

```bash
cd C:\Users\Abuomar\Documents\ListenEnglish
git init
git add .
git commit -m "首次上传：模拟试题 17/30 逐句复述"
git remote add origin https://github.com/gartional/ListenEnglish.git
git branch -M main
git push -u origin main
```

若提示登录，用浏览器弹出登录 **gartional** 账号即可。

---

## 推完后

- 打开：https://github.com/gartional/ListenEnglish  
  能看到代码就说明成功了。

- 若要别人能打开网页：仓库 **Settings** → **Pages** → Source 选 **Deploy from a branch**，Branch 选 `main`，目录选 **/ (root)**，保存。  
  访问：**https://gartional.github.io/ListenEnglish/**
