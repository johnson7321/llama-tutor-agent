import subprocess
import whisper
import os

url = "https://www.youtube.com/watch?v=PvqVY7cELIA"

# 下載音訊
print("開始下載音訊...")
result = subprocess.run([
    "yt-dlp",
    "-x",
    "--audio-format", "mp3",
    "--ffmpeg-location=C:\\ffmpeg-7.1.1-full_build\\ffmpeg-7.1.1-full_build\\bin",
    "-o", "%(title)s.%(ext)s",
    url
], capture_output=True, text=True)

# 檢查是否成功
if result.returncode != 0:
    print("yt-dlp 發生錯誤：")
    print(result.stdout)
    print(result.stderr)
else:
    print("下載完成！")

# 找到 mp3 檔案
for file in os.listdir():
    if file.endswith(".mp3"):
        audio_file = file
        print(f"發現音訊檔案：{audio_file}")

        # Whisper 辨識
        print("語音辨識中...")
        model = whisper.load_model("small")
        result = model.transcribe(audio_file)
        print("\n辨識結果：")
        print(result["text"])
        break
else:
    print("未找到 mp3 音訊檔案，請確認下載是否成功")
