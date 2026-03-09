# 把 ListenEnglish 推到 GitCode

## 1. 在 GitCode 上新建仓库

1. 登录 https://gitcode.com
2. 右上角 **「+」→「新建仓库」**
3. 仓库名填：`ListenEnglish`（或任意，记住即可）
4. 可见性选 **公开**
5. **不要**勾选「使用 Readme 初始化」
6. 创建后，记下仓库地址，形如：  
   `https://gitcode.com/你的用户名/ListenEnglish`

---

## 2. 在本地添加 GitCode 远程并推送

在项目目录 `ListenEnglish` 下打开终端，执行（把 `你的用户名` 换成你在 GitCode 的登录名）：

```bash
# 添加 GitCode 为远程，名字叫 gitcode
git remote add gitcode https://gitcode.com/你的用户名/ListenEnglish.git

# 推送当前 main 分支到 GitCode（首次推送）
git push -u gitcode main
```

如果 GitCode 仓库名不是 `ListenEnglish`，把上面两行里的 `ListenEnglish` 改成你的仓库名。

---

## 3. 以后同时推送到 GitHub 和 GitCode

```bash
# 推送到 GitHub
git push origin main

# 推送到 GitCode
git push gitcode main
```

---

## 4. 若有未提交的修改，先提交再推送

```bash
git add .
git commit -m "同步到 GitCode"
git push -u gitcode main
```

推送时若提示输入账号密码，请用 GitCode 的 **用户名** 和 **私人令牌**（在 GitCode 设置 → 安全设置 → 私人令牌 里生成），不要用登录密码。
