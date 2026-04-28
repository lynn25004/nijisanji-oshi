# 🌈 彩虹社推し選擇器

選擇你推的彩虹社（NIJISANJI）成員，並查看其最新在架商品。

## 功能
- 全分部成員列表（JP / EN / KR / ID），按出道日期排列
- 搜尋 + 分部篩選
- 點選成員後自動從官方商店載入在架商品
- 每日自動更新成員資料
- 支援電腦和手機

## 如何部署（GitHub Pages）

1. 在 GitHub 建立新的 repository，名稱任意（例如 `nijisanji-oshi`）
2. 將這個資料夾的所有內容上傳
3. 前往 Repository → Settings → Pages
4. Source 選擇 `Deploy from a branch`，Branch 選 `main`，資料夾選 `/（root）`
5. 儲存後等 1-2 分鐘，會得到類似 `https://你的名字.github.io/nijisanji-oshi/` 的網址
6. 這個網址可以直接傳給朋友使用

## 自動更新

GitHub Actions 已設定每天台灣時間早上 8:00 自動執行 `scripts/update_data.py`，
抓取最新成員資料並更新 `data/members.json`。

也可以手動觸發：Repository → Actions → 每日更新彩虹社成員資料 → Run workflow

## 本地使用

直接用瀏覽器開啟 `index.html` **不行**，因為瀏覽器會阻擋本地檔案的 fetch 請求。

需要一個簡單的本地伺服器：
```bash
# Python（推薦）
cd nijisanji-oshi
python -m http.server 8080
# 然後開啟 http://localhost:8080
```

或用 VS Code 的 Live Server 擴充功能。

## 商品資料來源

商品直接從 [nijisanji-store.com](https://nijisanji-store.com) 的 Shopify API 即時載入，
不需要後端，資料永遠是最新的。
