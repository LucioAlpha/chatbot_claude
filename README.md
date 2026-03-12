# AI Chatbot 聊天機器人 based on Google Gemini 2.5 Flash

## 小組：第四組

### 組員：

* D1249756 黃柏豪

## 專案簡介

本專案是一個使用 Streamlit 製作的 AI 聊天機器人，具備基本的對話與記憶功能。

## 目前功能
1. **基礎對話功能**:
    
    使用者可以在畫面上的輸入框與 AI 聊天，AI 會回覆使用者的問題。

2. **檔案上傳功能**

    使用者可以將圖片、PDF、文字檔上傳至 AI，AI 會分析檔案的內容並回覆使用者。

3. **角色設定功能**

    在新增對話並開始輸入文字前，使用者可以設定 AI 的角色。以利 AI 能夠更準確地回覆使用者的問題。

4. **記憶功能**

    每次對話結束後，使用者可以選擇是否將對話紀錄儲存到 JSON 檔案中，以利使用者在下次使用時可以繼續對話。
    這些 JSON 檔案會統一儲存在 `StreamHistory` 資料夾中。

5. **回朔功能**

    在對話紀錄中，使用者可以選擇回朔到某一次對話，並針對該訊息進行修改或刪除，以利使用者可以重新對話，獲取更加精準的回覆。

## 實際運行畫面與說明

![default_main](/asset/imgs/default_main.png)
程式運行的第一畫面
- 右側為聊天室
- 左側為功能選單
    - 第一個功能是聊天機器人的初始設定
    - 第二個功能是聊天紀錄存檔與新增
    - 第三個功能是調取已存的聊天紀錄
    - 第四個功能是上傳檔案  

![LoadHistory](/asset/imgs/LoadHistory.png)

調取已存的聊天紀錄的範例畫面

![UploadFile](/asset/imgs/UploadFile.png)

上傳檔案的範例畫面

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

問題：app.py 無法正常運行，會直接閃退或中止

解法：

檢查是否安裝了 streamlit，未安裝請使用 pip install streamlit 安裝

### 問題 2

問題：機器人未回應、回應時間過長

解法：
1. 在 Google AI Studio 中，檢查 API KEY 是否正確
2. 在 chatbot.py 中找尋以下程式碼區塊，並確認模型名稱有在 AI Studio 支援的清單中

    ```python
    # ── 初始化模型 ──
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash", # 請確認模型名稱有在 AI Studio 支援的清單中
        google_api_key=API_KEY,
        temperature=0.7,
    )

    ```

---

## 學習心得

### 黃柏豪

這次的專案讓我學習到如何使用 Streamlit 建立一個 AI 聊天機器人，也讓我更熟悉了 Antigravity 和 GitHub 的使用方法。

目前，雖然是剛接觸 Git，但已經感受到版本控制與協作的重要性，我們總不能守著同一台電腦去做版本控制，更多時候是要以群組的形式進行協作。

另外，我認為專案本身所提供的技術文件 `README.MD` 更是至關重要的一部分，不僅省下大量閱讀程式碼的時間，更是輕而易舉的知道如何使用專案。

而我也因此收穫 Git 多用戶單一裝置控制的技巧。

---

## GitHub 專案連結

### 黃柏豪
https://github.com/LucioAlpha/chatbot_claude.git