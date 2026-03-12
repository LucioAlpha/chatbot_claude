# AI Chatbot 聊天機器人 based on Google Gemini 2.5 Flash

## 小組：第四組

### 組員：

* D1249756 黃柏豪

## 專案簡介

本專案是一個使用 Streamlit 製作的 AI 聊天機器人，具備基本的對話與記憶功能。

## 目前功能
1. 基礎對話功能
使用者可以在畫面上的輸入框與 AI 聊天，AI 會回覆使用者的問題。

2. 檔案上傳功能
使用者可以將圖片、PDF、文字檔上傳至 AI，AI 會分析檔案的內容並回覆使用者。

3. 角色設定功能
在新增對話並開始輸入文字前，使用者可以設定 AI 的角色。以利 AI 能夠更準確地回覆使用者的問題。

4. 記憶功能
每次對話結束後，使用者可以選擇是否將對話紀錄儲存到 JSON 檔案中，以利使用者在下次使用時可以繼續對話。

5. 回朔功能
在對話紀錄中，使用者可以選擇回朔到某一次對話，並針對該訊息進行修改或刪除，以利使用者可以重新對話，獲取更加精準的回覆。

## 執行方式

1. 使用 git clone 下載專案
2. 根據 requirements.txt 安裝依賴
3. 使用 streamlit run app.py 執行專案

範例指令：

```bash
git clone https://github.com/LucioAlpha/chatbot_claude.git
pip install -r requirements.txt
streamlit run app.py
```

---

## 環境變數說明

請自行建立 `.env` 檔案，並填入自己的 API key。

範例：
1. 在 Google AI Studio 中，找到 API key
2. 在根目錄中建立 `.env` 檔案
3. 將 API key 複製到 `.env` 檔案中

`.env` 檔案內容：
```env
GEMINI_API_KEY=your_api_key_here
```

## 遇到的問題與解法

### 問題 1

問題：檔案運行後無法正常顯示在本地網址
解法：檢查是否安裝了 streamlit，未安裝請使用 pip install streamlit 安裝

### 問題 2

問題：機器人未回應
解法：
1. 在 Google AI Studio 中，檢查 API KEY 是否正確

---

## 學習心得

> 請簡要寫出本次作業的學習心得。

---

## GitHub 專案連結

請填入小組各組員 GitHub repository 網址。