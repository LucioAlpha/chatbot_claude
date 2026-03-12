"""
Gemini 2.5 Flash 多模態聊天機器人
支援：純文字、圖片 (JPG/PNG)、PDF、純文字檔 (.txt)
具備對話記憶與 JSON 持久化功能。
"""

import base64
import json
import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

# ── 載入環境變數 ──────────────────────────────────────────────────────────────
load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    print("❌ 找不到 API Key！請在 .env 中設定 GEMINI_API_KEY 或 GOOGLE_API_KEY。")
    sys.exit(1)

# ── 初始化模型 ────────────────────────────────────────────────────────────────
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=API_KEY,
    temperature=0.7,
)

# ── 系統提示 ──────────────────────────────────────────────────────────────────
SYSTEM_PROMPT = (
    "你是一位友善、專業的 AI 助理，擅長分析文字、圖片與文件。"
    "請用繁體中文回答問題，除非使用者以其他語言提問。"
)

# ── 對話紀錄 ──────────────────────────────────────────────────────────────────
conversation_history: list = [SystemMessage(content=SYSTEM_PROMPT)]
export_records: list[dict] = []


# ── 檔案處理工具函式 ──────────────────────────────────────────────────────────

def get_timestamp() -> str:
    return datetime.now().isoformat()


def load_image(file_path: str) -> dict:
    """將圖片編碼為 base64，回傳 LangChain image_url 格式的 content 區塊。"""
    suffix = Path(file_path).suffix.lower()
    mime_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png"}
    mime = mime_map.get(suffix, "image/jpeg")
    with open(file_path, "rb") as f:
        b64 = base64.standard_b64encode(f.read()).decode("utf-8")
    return {
        "type": "image_url",
        "image_url": {"url": f"data:{mime};base64,{b64}"},
    }


def load_pdf(file_path: str) -> str:
    """使用 PyPDFLoader 讀取 PDF，回傳合併的純文字內容。"""
    loader = PyPDFLoader(file_path)
    pages = loader.load()
    return "\n\n".join(
        f"[第 {i+1} 頁]\n{page.page_content}" for i, page in enumerate(pages)
    )


def load_txt(file_path: str) -> str:
    """讀取純文字檔，自動偵測編碼。"""
    for enc in ("utf-8", "utf-8-sig", "big5", "gbk"):
        try:
            with open(file_path, "r", encoding=enc) as f:
                return f.read()
        except (UnicodeDecodeError, LookupError):
            continue
    raise ValueError(f"無法解碼文字檔：{file_path}")


def detect_file(text: str) -> str | None:
    """
    若使用者輸入看起來是一個存在的檔案路徑，回傳正規化後的路徑，否則回傳 None。
    支援帶/不帶引號的路徑。
    """
    candidate = text.strip().strip("\"'")
    if os.path.isfile(candidate):
        return candidate
    return None


# ── 核心對話函式 ──────────────────────────────────────────────────────────────

def chat_with_file(file_path: str, user_text: str) -> str:
    """處理含有檔案附件的對話輪次。"""
    suffix = Path(file_path).suffix.lower()
    file_name = Path(file_path).name

    if suffix in (".jpg", ".jpeg", ".png"):
        # ── 圖片：使用多模態 content list ────────────────────────────────────
        image_block = load_image(file_path)
        prompt_text = user_text if user_text else "請描述並分析這張圖片的內容。"
        content = [{"type": "text", "text": prompt_text}, image_block]
        human_msg = HumanMessage(content=content)
        export_text = f"[圖片：{file_name}] {prompt_text}"

    elif suffix == ".pdf":
        # ── PDF：提取文字後合併為純文字訊息 ──────────────────────────────────
        print(f"  📄 正在讀取 PDF：{file_name} ...")
        pdf_text = load_pdf(file_path)
        prompt_text = user_text if user_text else "請摘要並分析以下 PDF 文件內容。"
        combined = f"{prompt_text}\n\n--- PDF 內容（{file_name}）---\n{pdf_text}"
        human_msg = HumanMessage(content=combined)
        export_text = f"[PDF：{file_name}] {prompt_text}"

    elif suffix == ".txt":
        # ── 純文字檔 ──────────────────────────────────────────────────────────
        print(f"  📝 正在讀取文字檔：{file_name} ...")
        txt_content = load_txt(file_path)
        prompt_text = user_text if user_text else "請摘要並分析以下文字檔內容。"
        combined = f"{prompt_text}\n\n--- 文字檔內容（{file_name}）---\n{txt_content}"
        human_msg = HumanMessage(content=combined)
        export_text = f"[文字檔：{file_name}] {prompt_text}"

    else:
        raise ValueError(f"不支援的檔案類型：{suffix}（僅支援 JPG、PNG、PDF、TXT）")

    conversation_history.append(human_msg)
    export_records.append({
        "timestamp": get_timestamp(),
        "role": "user",
        "content": export_text,
        "file": file_path,
        "file_type": suffix.lstrip("."),
    })

    response = llm.invoke(conversation_history)
    ai_content = response.content

    conversation_history.append(AIMessage(content=ai_content))
    export_records.append({
        "timestamp": get_timestamp(),
        "role": "ai",
        "content": ai_content,
    })

    return ai_content


def chat(user_input: str) -> str:
    """純文字對話輪次。"""
    conversation_history.append(HumanMessage(content=user_input))
    export_records.append({
        "timestamp": get_timestamp(),
        "role": "user",
        "content": user_input,
    })

    response = llm.invoke(conversation_history)
    ai_content = response.content

    conversation_history.append(AIMessage(content=ai_content))
    export_records.append({
        "timestamp": get_timestamp(),
        "role": "ai",
        "content": ai_content,
    })

    return ai_content


def save_conversation() -> str:
    """將對話紀錄儲存為 JSON 檔案，回傳檔名。"""
    if not export_records:
        return ""

    filename = datetime.now().strftime("chat_%Y%m%d_%H%M%S.json")
    filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)

    data = {
        "model": "gemini-2.5-flash",
        "system_prompt": SYSTEM_PROMPT,
        "total_turns": len(export_records),
        "messages": export_records,
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return filename


# ── 主程式 ────────────────────────────────────────────────────────────────────

HELP_TEXT = """
  支援的指令：
  ┌─────────────────────────────────────────────────────┐
  │  直接輸入文字          → 純文字對話                  │
  │  輸入檔案路徑          → 自動偵測並分析檔案          │
  │  輸入檔案路徑 + 問題   → 先貼路徑，下一行輸入問題    │
  │  exit / quit           → 儲存對話並結束              │
  └─────────────────────────────────────────────────────┘
  支援格式：JPG、PNG、PDF、TXT
"""


def main():
    print("=" * 57)
    print("  🤖  Gemini 2.5 Flash 多模態聊天機器人")
    print("  輸入 'exit' 或按 Ctrl+C 結束並儲存對話紀錄")
    print("=" * 57)
    print(HELP_TEXT)

    pending_file: str | None = None   # 暫存上一輪偵測到的檔案路徑

    try:
        while True:
            try:
                user_input = input("👤 你: ").strip()
            except EOFError:
                break

            if not user_input:
                continue

            if user_input.lower() in ("exit", "quit"):
                break

            # ── 判斷是否為檔案路徑 ────────────────────────────────────────────
            detected = detect_file(user_input)

            if detected:
                # 使用者直接貼了檔案路徑，提示輸入問題（或 Enter 略過）
                pending_file = detected
                suffix = Path(detected).suffix.lower()
                print(f"  📎 偵測到檔案：{Path(detected).name}（{suffix}）")
                follow_up = input("  💬 請輸入問題（直接按 Enter 使用預設分析）: ").strip()
                print("\n🤖 AI: ", end="", flush=True)
                try:
                    reply = chat_with_file(pending_file, follow_up)
                    print(reply)
                except Exception as e:
                    print(f"❌ 處理檔案時發生錯誤：{e}")
                pending_file = None

            else:
                # 純文字對話
                print("\n🤖 AI: ", end="", flush=True)
                try:
                    reply = chat(user_input)
                    print(reply)
                except Exception as e:
                    print(f"❌ 發生錯誤：{e}")

            print()  # 空行分隔

    except KeyboardInterrupt:
        print("\n\n⚠️  偵測到 Ctrl+C，正在儲存對話紀錄...")

    finally:
        saved_file = save_conversation()
        if saved_file:
            print(f"\n✅ 對話紀錄已儲存至：{saved_file}")
        else:
            print("\nℹ️  沒有對話紀錄可儲存。")
        print("👋 再見！")


if __name__ == "__main__":
    main()
