@echo off
chcp 65001 >nul
cd /d D:\lynn-agent\nijisanji-oshi

echo ===================================================
echo  nijisanji-oshi GitHub Pages 部署腳本
echo  GitHub: lynn25004/nijisanji-oshi
echo ===================================================
echo.

echo [1/4] 清理舊的 .git 目錄（若存在）...
if exist ".git" (
    rd /s /q .git
    echo      清理完成
) else (
    echo      無需清理
)

echo [2/4] 初始化 Git Repo...
git init -b main
git config user.name "Lynn"
git config user.email "a0423354860@gmail.com"

echo [3/4] 加入所有檔案並 commit...
git add .
git status --short
git commit -m "Initial commit: nijisanji-oshi VTuber web app with 245 members"

echo [4/4] 設定 remote 並推送...
git remote add origin https://github.com/lynn25004/nijisanji-oshi.git
git push -u origin main

if %errorlevel% == 0 (
    echo.
    echo ===================================================
    echo  ✓ 推送成功！
    echo.
    echo  正在自動開啟 GitHub Pages 設定頁面...
    start https://github.com/lynn25004/nijisanji-oshi/settings/pages
    echo.
    echo  請在瀏覽器中：
    echo  1. Source 選 "Deploy from a branch"
    echo  2. Branch 選 "main"，路徑選 "/ (root)"
    echo  3. 點 Save
    echo.
    echo  網址（約 1-2 分鐘後生效）：
    echo  https://lynn25004.github.io/nijisanji-oshi/
    echo ===================================================
) else (
    echo.
    echo  推送失敗！請確認 GitHub repo 已建立：
    echo  https://github.com/new
    echo  名稱輸入: nijisanji-oshi
    echo  然後重新執行本腳本
)
echo.
pause
