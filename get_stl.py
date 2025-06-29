import os
import sys
import re
import subprocess
from pathlib import Path
import whisper
from opencc import OpenCC
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled
# -*- coding: utf-8 -*-


cc = OpenCC('s2t')
os.chdir(os.path.dirname(os.path.abspath(sys.argv[0])))

def extract_youtube_id(url):
    pattern = r"(?:v=|\/)([0-9A-Za-z_-]{11})(?:\?|&|$)"
    match = re.search(pattern, url)
    return match.group(1) if match else None

url = input("請輸入 YouTube 影片網址：").strip()
video_id = extract_youtube_id(url)

if not video_id:
    print("❌ 無法擷取影片 ID")
    sys.exit(1)

# # ✅ 嘗試取得影片標題
try:
    video_title = subprocess.check_output([
        "yt-dlp", "--get-filename", "-o", "%(title)s", url
    ], stderr=subprocess.STDOUT).decode("mbcs", errors="replace").strip()
    # video_title = "測試影片"
except subprocess.CalledProcessError:
    print("❌ 取得影片標題失敗")
    sys.exit(1)

# ✅ 嘗試擷取 YouTube 字幕
try:
    print("📋 嘗試取得 YouTube 原字幕...")
    transcript = YouTubeTranscriptApi.get_transcript(
        video_id,
        languages=['zh-TW', 'zh-Hant', 'zh-Hans', 'zh', 'en']
    )

    # def format_time(t):
    #     h = int(t // 3600)
    #     m = int((t % 3600) // 60)
    #     s = int(t % 60)
    #     ms = int((t - int(t)) * 1000)
    #     return f"{h:02}:{m:02}:{s:02},{ms:03}"

    srt_path = Path(f"{video_title}.srt")
    with open(srt_path, "w", encoding="utf-8") as f:
        for i, entry in enumerate(transcript, start=1):
            # start = format_time(entry["start"])
            # end = format_time(entry["start"] + entry["duration"])
            text = cc.convert(entry["text"].strip())
            # f.write(f"{i}\n{start} --> {end}\n{text}\n\n")
            f.write(text+"\n")


    print(f"✅ 已使用 YouTube 字幕並輸出：{srt_path.name}")
    sys.exit(0)

except (NoTranscriptFound, TranscriptsDisabled):
    print("⚠️ 沒有原字幕，改用 Whisper 處理")

# ✅ 音檔檢查與下載
# 1. 取得目前程式所在的資料夾路徑（專案根目錄）
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# 2. 定義放 mp3 的資料夾路徑，放在專案資料夾底下
mp3_folder = Path(SCRIPT_DIR) / "mp3_files"

# 3. 確保資料夾存在，不存在就建立
mp3_folder.mkdir(parents=True, exist_ok=True)

# 4. 影片標題和檔名
audio_filename = f"{video_title}.mp3"
audio_path = mp3_folder / audio_filename

if not audio_path.exists():
    print("🎧 下載音訊中...")
    result = subprocess.run([
        "yt-dlp", "-x", "--audio-format", "mp3",
        "--no-overwrites",
        f"--ffmpeg-location=C:\\ffmpeg-7.1.1-full_build\\ffmpeg-7.1.1-full_build\\bin",
        "-o", str(mp3_folder / "%(title)s.%(ext)s"),
        url
    ], capture_output=True, text=True)

    if result.returncode != 0:
        print("❌ yt-dlp 發生錯誤：")
        print(result.stdout)
        print(result.stderr)
        sys.exit(1)
    else:
        print("✅ 音訊下載完成")
else:
    print("✅ mp3 已存在")

# ✅ Whisper 辨識
print("🧠 使用 Whisper 轉錄中...")
model = whisper.load_model("base")
result = model.transcribe(str(audio_path))#出錯

# def format_timestamp(seconds: float) -> str:
#     h = int(seconds // 3600)
#     m = int((seconds % 3600) // 60)
#     s = int(seconds % 60)
#     ms = int((seconds - int(seconds)) * 1000)
#     return f"{h:02}:{m:02}:{s:02},{ms:03}"

# 1. 取得專案根目錄（假設和你前面一樣）
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# 2. 定義字幕資料夾
subtitle_folder = Path(SCRIPT_DIR) / "subtitles"
subtitle_folder.mkdir(parents=True, exist_ok=True)  # 確保存在

# 3. 產生字幕檔完整路徑，副檔名改成 .srt
srt_path = subtitle_folder / audio_path.with_suffix(".srt").name

print(srt_path)

# 4. 寫入字幕檔案
with open(srt_path, "w", encoding="utf-8") as f:
    for i, seg in enumerate(result["segments"], start=1):
        # start = format_timestamp(seg["start"])
        # end = format_timestamp(seg["end"])
        text = cc.convert(seg["text"].strip())
        # f.write(f"{i}\n{start} --> {end}\n{text}\n\n")
        f.write(text + "\n")
print(f"✅ Whisper 完成！字幕儲存為：{srt_path.name}")