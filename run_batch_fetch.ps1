# 批量抓取 mock01..48，跳过翻译。
# 若提示“禁止运行脚本”，请改用 run_batch_fetch.bat 或终端执行: python tools/batch_fetch_mocks.py --skip-translate
Set-Location $PSScriptRoot
python tools/batch_fetch_mocks.py --skip-translate
Read-Host "按回车关闭"
