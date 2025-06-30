import get_stl
import build_vct_db
import os
import sys
from pathlib import Path
from opencc import OpenCC
import prompt
import get_stl
import build_vct_db
import conversation

# 若有用到 ollama、openpyxl、re 可保留，否則可移除
# import ollama
# from datetime import datetime
# from openpyxl import Workbook, load_workbook
# import re

# 若有用到 langchain 相關功能可保留，否則可移除
# from langchain.docstore.document import Document
# from langchain_ollama import OllamaEmbeddings
# from langchain_chroma import Chroma
# from langchain.text_splitter import RecursiveCharacterTextSplitter
# from langchain.chains import RetrievalQA
# from langchain_ollama import ChatOllama

# 若有用到 youtube_transcript_api 可保留，否則可移除
# from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled

# 若有用到 shutil 可保留，否則可移除
# import shutil

# 編碼宣告可移除，Python 3 預設 utf-8
# # -*- coding: utf-8 -*-

# 確保使用 OpenCC 轉換簡體到繁體
cc = OpenCC('s2t')

os.chdir(os.path.dirname(os.path.abspath(sys.argv[0])))

url = input("請輸入 YouTube 影片網址：").strip()
#url = "https://www.youtube.com/watch?v=BfNgCs9KnXE"
video_id = get_stl.extract_youtube_id(url)

if not video_id:
    print("❌ 無法擷取影片 ID")
    sys.exit(1)

# 取得影片標題
video_title = get_stl.get_video_title(url)
# 取得影片的字幕內容
subtitle_dir = Path(f"{video_title}.txt")
# 嘗試從 YouTube 下載字幕
srt_content = get_stl.try_download_youtube_subtitle(video_id,cc,subtitle_dir)
if not isinstance(srt_content, str):
    print("❌ 字幕內容型態錯誤，請檢查 get_stl.try_download_youtube_subtitle 回傳值")
    sys.exit(1)
# 如果字幕內容為空，則使用 Whisper 進行轉錄
if not srt_content:
    # 如果字幕不存在，則使用 Whisper 進行轉錄
    ffmpeg_path = "C:\\ffmpeg-7.1.1-full_build\\ffmpeg-7.1.1-full_build\\bin"
    # 確保 ffmpeg 路徑正確
    audio_path = get_stl.download_audio_if_needed(video_title, url, ffmpeg_path)

    print("🧠 使用 Whisper 轉錄中...")

    srt_path = get_stl.transcribe_audio_to_txt(audio_path, cc_converter=cc)

    # 取得目前這支腳本所在的資料夾（專案根目錄）
    SCRIPT_DIR = Path(__file__).resolve().parent

    # 定位字幕資料夾與目標 srt 檔案
    srt_folder = SCRIPT_DIR / "subtitles"
    subtitles = srt_folder / f"{video_title}.txt"  # 這裡換成你實際的檔名

    # 確保檔案存在再讀取
    if subtitles.exists():
        with open(subtitles, "r", encoding="utf-8") as f:
            srt_content = f.read()
            # print("✅ 字幕內容如下：")
            # print(srt_content)
    else:
        print(f"❌ 找不到檔案：{subtitles}")

srt_lines = [line.strip() for line in srt_content.splitlines() if line.strip()]
print("✅ 字幕前10句：")
for i, line in enumerate(srt_lines[:10], 1):
    print(f"{i:02d}. {line}")
print("✅ 字幕後10句：")
for i, line in enumerate(srt_lines[-10:], len(srt_lines)-9):
    print(f"{i:02d}. {line}")

messages = []
messages = [{"role": "system", "content": prompt.tutor_guideline}]
MODEL_NAME = 'llama3.1:latest'

build_vct_db.build_db_once(str(srt_content)) # 建立向量資料庫

build_vct_db.rag("50字講述這支影片的主題",messages,str(srt_content)) # 測試 RAG 功能

print("🎥 字幕系統已啟動，輸入 quit,exit,bye 離開")

while True:
    user_input = input("🙋 你：").strip()
    if user_input.lower() in ["quit", "exit", "bye"]:
        print("👋 再見，祝學習愉快！")
        break
    if not user_input:
        continue

    # 1. 先用 retriever 檢索相關內容
    retriever = build_vct_db.build_db_once(str(srt_content))
    related_docs = retriever.invoke(user_input)[:3]
    context_chunks = [
        f"[來自：{doc.metadata.get('source', '未知')}]\n{doc.page_content}"
        for doc in related_docs
    ]
    context_text = "\n---\n".join(context_chunks)

    # 2. 組合 RAG prompt
    rag_prompt = f"""以下是影片字幕內容摘要，請根據這些內容來回答問題：\n\n{context_text}\n\n使用者問題：{user_input}\n請用繁體中文詳細解釋，並舉例子說明。"""

    # 3. 將 RAG prompt 加入 messages
    messages.append({"role": "user", "content": rag_prompt})

    # 4. 呼叫 LLM
    response = conversation.chat_with_ollama(rag_prompt, messages, MODEL_NAME)
    messages.append({"role": "assistant", "content": response})

    print("\n🤓家教老師：", response)
