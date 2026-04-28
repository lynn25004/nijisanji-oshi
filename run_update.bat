@echo off
cd /d "%~dp0"
echo 正在更新彩虹社成員資料...
python scripts\update_data.py
echo.
echo 完成！按任意鍵關閉。
pause
