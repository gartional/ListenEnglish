#!/bin/bash
# 在 Mac 上双击运行：启动本地服务器并打开浏览器，无需 GitHub / VPN。
# 需要已安装 Python 3（Mac 通常自带）。

cd "$(dirname "$0")"
PORT=8765

# 查找 python3
if command -v python3 &>/dev/null; then
  PY=python3
elif command -v python &>/dev/null; then
  PY=python
else
  echo "未找到 Python，请先安装 Python 3。"
  read -p "按回车关闭..."
  exit 1
fi

# 启动带 Range 支持的服务器（便于音频拖拽）
"$PY" tools/serve_range.py $PORT &
PID=$!
sleep 1
if ! kill -0 $PID 2>/dev/null; then
  echo "端口 $PORT 可能被占用，或 serve_range.py 未找到。"
  read -p "按回车关闭..."
  exit 1
fi

open "http://localhost:$PORT/"
echo "已在浏览器打开。关闭本窗口将停止服务器。"
read -p "按回车停止服务器并关闭..."
kill $PID 2>/dev/null
exit 0
