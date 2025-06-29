import get_stl
import build_vct_db
import os
from pathlib import Path
import os
import sys
import re
import subprocess
from pathlib import Path
import whisper
from opencc import OpenCC
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled
import prompt
import conversation
# -*- coding: utf-8 -*-


cc = OpenCC('s2t')
os.chdir(os.path.dirname(os.path.abspath(sys.argv[0])))

#url = input("請輸入 YouTube 影片網址：").strip()
url = "https://www.youtube.com/watch?v=yWxsl48iGeo"
video_id = get_stl.extract_youtube_id(url)

if not video_id:
    print("❌ 無法擷取影片 ID")
    sys.exit(1)

video_title = get_stl.get_video_title(url)

subtitle_dir = Path(f"{video_title}.srt")

srt_content = get_stl.try_download_youtube_subtitle(video_id,cc,subtitle_dir)

if not srt_content:
    ffmpeg_path = "C:\\ffmpeg-7.1.1-full_build\\ffmpeg-7.1.1-full_build\\bin"

    audio_path = get_stl.download_audio_if_needed(video_title, url, ffmpeg_path)

    print("🧠 使用 Whisper 轉錄中...")

    srt_path = get_stl.transcribe_audio_to_srt(audio_path, cc_converter=cc)

    # 取得目前這支腳本所在的資料夾（專案根目錄）
    SCRIPT_DIR = Path(__file__).resolve().parent

    # 定位字幕資料夾與目標 srt 檔案
    srt_folder = SCRIPT_DIR / "subtitles"
    subtitles = srt_folder / f"{video_title}.srt"  # 這裡換成你實際的檔名

    # 確保檔案存在再讀取
    if subtitles.exists():
        with open(subtitles, "r", encoding="utf-8") as f:
            srt_content = f.read()
            # print("✅ 字幕內容如下：")
            # print(srt_content)
    else:
        print(f"❌ 找不到檔案：{subtitles}")

messages = [{"role": "system", "content": prompt.tutor_guideline}]
MODEL_NAME = 'llama3.1:latest'

build_vct_db.build_db(str(srt_content))

print("🎥 字幕系統已啟動，輸入 quit,exit,bye 離開")

while True:
    user_input = input("🙋 你：").strip()
    if user_input.lower() in ["quit", "exit", "bye"]:
        print("👋 再見，祝學習愉快！")
        break
    if not user_input:
        continue
    build_vct_db.rag(user_input,messages,str(srt_content))
    response = conversation.chat_with_ollama(user_input,messages,MODEL_NAME)
    print("\n🤓家教老師：", response)
