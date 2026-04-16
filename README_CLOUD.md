# 教學策略研究：雲端自動化版部署指南

恭喜！雲端版的程式碼已經準備就緒。請依照以下步驟完成部署，實現每日全自動掃描。

## 第一步：準備 GitHub 倉庫
1. 在您的 [GitHub](https://github.com/) 建立一個全新的私有倉庫 (Private Repository)，命名為 `stock-analysis-cloud`。
2. 將 `股票分析_雲端版` 資料夾中的所有檔案上傳到該倉庫：
   - `cloud_scanner.py`
   - `requirements_cloud.txt`
   - `.github/workflows/daily_scan.yml`
   - `cloud_index.html`

## 第二步：設定 GitHub Secrets (最重要)
在 GitHub 倉庫頁面，進入 **Settings > Secrets and variables > Actions**，新增以下 **Repository secrets**：

| Secret 名稱 | 來源 / 說明 |
| :--- | :--- |
| `SUPABASE_URL` | 您的 Supabase 專案 URL |
| `SUPABASE_SERVICE_ROLE_KEY` | 您的 Supabase Service Role API Key (具有寫入權限) |
| `TELEGRAM_BOT_TOKEN` | 您原本的 Telegram Bot Token |
| `TELEGRAM_CHAT_ID` | 您原本的 Telegram Chat ID |

## 第三步：部署網頁 (Vercel)
1. 登入 [Vercel](https://vercel.com/)。
2. 點擊 **Add New > Project**，導入您的 GitHub 倉庫。
3. 在部署前，將 `cloud_index.html` 改名為 `index.html` (Vercel 預設讀取 index.html)。
4. 在 Vercel 的環境變數設定中不需額外設定，但請手動修改 `index.html` 中的 `SUPABASE_URL` 與 `SUPABASE_ANON_KEY` 為您的公開資訊。

## 第四步：測試運行
1. 在 GitHub 倉庫點擊標籤 **Actions**。
2. 選擇左側的 **Daily Stock Scan** 工作流。
3. 點擊 **Run workflow** 手動觸發一次掃描。
4. 觀察 Log 是否成功上傳至 Supabase 並發送 Telegram。

---

### 注意事項
- **執行時間**：目前的排程設定為台北時間每日 **15:15** 執行。
- **維護**：由於雲端環境與本地不同，若 `yfinance` 發生 API 變更，只需在 GitHub 修改代碼即可。
