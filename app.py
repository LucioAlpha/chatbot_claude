"""
Gemini 2.5 Flash Streamlit 多模態聊天 GUI
支援：純文字、圖片 (JPG/PNG)、PDF、純文字檔 (.txt)
具備對話記憶、JSON 持久化讀取/儲存、修改系統提示、以及編輯/重新產生歷史訊息功能。
"""

import base64
import glob
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

# ── 頁面基本設定 ──────────────────────────────────────────────────────────────
st.set_page_config(page_title="Gemini 2.5 Flash Chatbot", page_icon="🤖", layout="wide")

# ── 載入環境變數 ──────────────────────────────────────────────────────────────
@st.cache_resource
def init_llm():
    load_dotenv()
    API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not API_KEY:
        st.error("❌ 找不到 API Key！請在 .env 中設定 GEMINI_API_KEY 或 GOOGLE_API_KEY。")
        st.stop()
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=API_KEY,
        temperature=0.7,
    )

llm = init_llm()

# ── 狀態初始化 ────────────────────────────────────────────────────────────────
if "system_prompt" not in st.session_state:
    st.session_state["system_prompt"] = (
        "你是一位友善、專業的 AI 助理，擅長分析文字、圖片與文件。"
        "請用繁體中文回答問題，除非使用者以其他語言提問。"
    )

if "export_records" not in st.session_state:
    st.session_state["export_records"] = []

if "messages" not in st.session_state:
    st.session_state["messages"] = [SystemMessage(content=st.session_state["system_prompt"])]

if "edit_idx" not in st.session_state:
    st.session_state["edit_idx"] = None  # To track which message is being edited

if "processed_file_id" not in st.session_state:
    st.session_state["processed_file_id"] = None  # 追蹤已處理的上傳檔案，防止 rerun 重複送出

# ── 輔助函式 ──────────────────────────────────────────────────────────────────
HISTORY_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "StreamHistory")
os.makedirs(HISTORY_DIR, exist_ok=True)

def get_timestamp() -> str:
    return datetime.now().isoformat()

def get_json_files() -> list[str]:
    """獲取 StreamHistory 目錄下的所有 chat_*.json 檔案"""
    files = glob.glob(os.path.join(HISTORY_DIR, "chat_*.json"))
    return sorted([os.path.basename(f) for f in files], reverse=True)

def parse_base64_from_data_url(data_url: str) -> str:
    """從 data:image/...;base64,xxxx 格式中提取 base64 字串"""
    if "base64," in data_url:
        return data_url.split("base64,")[1]
    return ""

def process_uploaded_file(uploaded_file) -> tuple:
    """處理 Streamlit 上傳的檔案，回傳 (LangChain message 區塊/文字, 顯示用的字串, file_type)"""
    file_bytes = uploaded_file.read()
    suffix = Path(uploaded_file.name).suffix.lower()
    file_name = uploaded_file.name

    if suffix in (".jpg", ".jpeg", ".png"):
        mime_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png"}
        mime = mime_map.get(suffix, "image/jpeg")
        b64 = base64.standard_b64encode(file_bytes).decode("utf-8")
        block = {
            "type": "image_url",
            "image_url": {"url": f"data:{mime};base64,{b64}"},
        }
        return block, f"[圖片：{file_name}]", suffix.lstrip(".")

    elif suffix == ".pdf":
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name
        
        loader = PyPDFLoader(tmp_path)
        pages = loader.load()
        pdf_text = "\n\n".join(f"[第 {i+1} 頁]\n{page.page_content}" for i, page in enumerate(pages))
        os.unlink(tmp_path)
        
        return f"\n\n--- PDF 內容（{file_name}）---\n{pdf_text}", f"[PDF：{file_name}]", "pdf"

    elif suffix == ".txt":
        for enc in ("utf-8", "utf-8-sig", "big5", "gbk"):
            try:
                txt_content = file_bytes.decode(enc)
                return f"\n\n--- 文字檔內容（{file_name}）---\n{txt_content}", f"[文字檔：{file_name}]", "txt"
            except UnicodeDecodeError:
                continue
        return f"\n\n--- 文字檔內容未解析 ---", f"[未解析文字檔：{file_name}]", "txt"
    else:
        st.error(f"不支援的檔案類型：{suffix}")
        st.stop()

def save_current_chat():
    """儲存對話到 JSON"""
    if not st.session_state["export_records"]:
        return None
        
    filename = datetime.now().strftime("chat_%Y%m%d_%H%M%S.json")
    filepath = os.path.join(HISTORY_DIR, filename)
    
    data = {
        "model": "gemini-2.5-flash",
        "system_prompt": st.session_state["system_prompt"],
        "total_turns": len(st.session_state["export_records"]),
        "messages": st.session_state["export_records"]
    }
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        
    return filename

def load_chat(filepath: str):
    """從 JSON 載入對話紀錄到 session_state"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        st.session_state["system_prompt"] = data.get("system_prompt", st.session_state["system_prompt"])
        st.session_state["export_records"] = data.get("messages", [])
        
        # 重建 LangChain message 歷史 (簡化處理，因為從純文字重建有些難以 100% 恢復多模態影像)
        # 這裡以文字方式重建上下文
        messages = [SystemMessage(content=st.session_state["system_prompt"])]
        for rec in st.session_state["export_records"]:
            if rec["role"] == "user":
                # 若為載入的歷史，僅作為上下文文字
                messages.append(HumanMessage(content=rec["content"]))
            elif rec["role"] == "ai":
                messages.append(AIMessage(content=rec["content"]))
                
        st.session_state["messages"] = messages
        st.session_state["edit_idx"] = None
        return True
    except Exception as e:
        st.error(f"讀取錯誤：{e}")
        return False

# ── 側邊欄 UI ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ 設定與紀錄")
    
    # 改變 System Prompt，會重設歷史紀錄中的第一則訊息
    new_system_prompt = st.text_area("初始角色設定 (System Prompt)", st.session_state["system_prompt"], height=150)
    if new_system_prompt != st.session_state["system_prompt"]:
        st.session_state["system_prompt"] = new_system_prompt
        # 更新目前訊息列表中的第一個 SystemMessage
        if len(st.session_state["messages"]) > 0 and isinstance(st.session_state["messages"][0], SystemMessage):
            st.session_state["messages"][0] = SystemMessage(content=new_system_prompt)
        st.success("角色設定已更新！")
    
    st.divider()
    
    # 對話控制開關
    if st.button("📝 建立新對話", use_container_width=True, type="primary"):
        # 先儲存當前對話
        save_current_chat()
        # 清空畫面與狀態
        st.session_state["export_records"] = []
        st.session_state["messages"] = [SystemMessage(content=st.session_state["system_prompt"])]
        st.session_state["edit_idx"] = None
        st.rerun()

    col1, col2 = st.columns(2)
    if col1.button("🗑️ 清空畫面(不存檔)"):
        st.session_state["export_records"] = []
        st.session_state["messages"] = [SystemMessage(content=st.session_state["system_prompt"])]
        st.session_state["edit_idx"] = None
        st.rerun()
        
    if col2.button("💾 手動儲存紀錄"):
        saved_file = save_current_chat()
        if saved_file:
            st.success(f"已儲存：{saved_file}")
        else:
            st.warning("沒有對話可儲存")
            
    st.divider()
    
    # 讀取歷史
    st.subheader("📁 讀取對話紀錄")
    json_files = get_json_files()
    if json_files:
        selected_file = st.selectbox("選擇檔案", ["(請選擇)"] + json_files)
        if selected_file != "(請選擇)":
            if st.button("載入此紀錄"):
                filepath = os.path.join(HISTORY_DIR, selected_file)
                if load_chat(filepath):
                    st.success("載入成功！")
                    st.rerun()
    else:
        st.info("尚無 JSON 對話紀錄檔。")
        
    st.divider()
    
    # 檔案上傳設定
    st.subheader("📎 附件上傳")
    uploaded_file = st.file_uploader("支援 JPG, PNG, PDF, TXT", type=["jpg", "jpeg", "png", "pdf", "txt"])

# ── 主畫面對話 UI ────────────────────────────────────────────────────────────
st.title("🤖 Gemini 2.5 Flash 多模態助理")

# 顯示對話歷史
for idx, rec in enumerate(st.session_state["export_records"]):
    with st.chat_message("user" if rec["role"] == "user" else "assistant"):
        st.markdown(rec["content"])
        # 在使用者訊息旁加上「編輯並重試」按鈕
        if rec["role"] == "user":
            if st.button("✍️ 重新編輯並修改這句話", key=f"edit_{idx}"):
                st.session_state["edit_idx"] = idx
                st.rerun()

# 如果處於編輯模式
if st.session_state["edit_idx"] is not None:
    edit_idx = st.session_state["edit_idx"]
    original_text = st.session_state["export_records"][edit_idx]["content"]
    st.warning("✏️ 正在編輯歷史訊息... (修改後將截斷此處之後的所有對話)")
    
    edited_text = st.text_area("修改訊息內容：", original_text)
    colA, colB = st.columns([1, 10])
    
    if colA.button("取消"):
        st.session_state["edit_idx"] = None
        st.rerun()
        
    if colB.button("✅ 儲存並重新產生", type="primary"):
        # 截斷 export_records 和 messages
        st.session_state["export_records"] = st.session_state["export_records"][:edit_idx]
        
        # 尋找對應的 messages 位置。因為 export_records 從 0 開始，對應到 messages (有 index 0 是 SystemMessage) 的位置
        # 需要跳過 idx 中的 SystemMessage，並將 Langchain Messages 同樣截短
        # 最簡單的方法：這是一對一映射，user/ai 交替
        st.session_state["messages"] = [st.session_state["messages"][0]]
        for rec in st.session_state["export_records"]:
            if rec["role"] == "user":
                st.session_state["messages"].append(HumanMessage(content=rec["content"]))
            elif rec["role"] == "ai":
                st.session_state["messages"].append(AIMessage(content=rec["content"]))
                
        st.session_state["edit_idx"] = None
        # 觸發發送流程
        st.session_state["resubmit_text"] = edited_text
        st.rerun()

# 根據是否剛編輯完成而帶入 text
user_prompt = None
if "resubmit_text" in st.session_state:
    user_prompt = st.session_state.pop("resubmit_text")
    did_upload = False
else:
    # 判斷是否有尚未處理的新上傳檔案
    if uploaded_file is not None:
        file_id = (uploaded_file.name, uploaded_file.size)
        did_upload = (file_id != st.session_state["processed_file_id"])
    else:
        did_upload = False

    # 若有待處理檔案，提示使用者輸入問題
    if did_upload:
        st.info(f"📎 **{uploaded_file.name}** 已就緒，請在下方輸入框輸入您的問題後送出。")

    user_prompt = st.chat_input(
        f"請輸入問題（附帶：{uploaded_file.name}）..." if did_upload else "請輸入您的問題..."
    )

# 只有使用者主動送出 prompt 才處理（不再因為純上傳就自動送出）
if user_prompt:
    actual_prompt = user_prompt if user_prompt else ""
    
    human_msg_content = []
    export_text = actual_prompt
    file_type = None
    file_name = None
    
    if uploaded_file:
        file_block, display_prefix, ftype = process_uploaded_file(uploaded_file)
        file_type = ftype
        file_name = uploaded_file.name
        
        if file_type in ("jpg", "jpeg", "png"):
            # 圖片模式，Langchain 要 List[Dict]
            human_msg_content = [{"type": "text", "text": actual_prompt}, file_block]
            export_text = f"{display_prefix} {actual_prompt}"
        else:
            # 文字模式附加
            human_msg_content = f"{actual_prompt}{file_block}"
            export_text = f"{display_prefix} {actual_prompt}"
    else:
        human_msg_content = actual_prompt
        export_text = actual_prompt

    # 1. 更新前端顯示紀錄 (user)
    st.session_state["export_records"].append({
        "timestamp": get_timestamp(),
        "role": "user",
        "content": export_text,
        "file": file_name,
        "file_type": file_type,
    })
    
    with st.chat_message("user"):
        st.markdown(export_text)
        
    # 2. 準備 Langchain 訊息，呼叫模型
    msg = HumanMessage(content=human_msg_content)
    st.session_state["messages"].append(msg)
    
    with st.chat_message("assistant"):
        with st.spinner("AI 思考中..."):
            response = llm.invoke(st.session_state["messages"])
            ai_content = response.content
            st.markdown(ai_content)
            
    # 3. 儲存 AI 回應
    st.session_state["messages"].append(AIMessage(content=ai_content))
    st.session_state["export_records"].append({
        "timestamp": get_timestamp(),
        "role": "ai",
        "content": ai_content,
    })
    
    # 標記此檔案已處理，防止下次 rerun 重複送出
    if uploaded_file is not None:
        st.session_state["processed_file_id"] = (uploaded_file.name, uploaded_file.size)
    st.rerun()

