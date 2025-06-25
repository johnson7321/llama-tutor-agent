from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled
import sys
import io
import re

# 解決 Windows 終端機無法顯示 utf-8 字符問題（例如顯示「蠦」會錯）
#sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 擷取 YouTube 影片 ID 的函式
def extract_youtube_id(url):
    pattern = r"(?:v=|\/)([0-9A-Za-z_-]{11})(?:\?|&|$)"
    match = re.search(pattern, url)
    if match:
        return match.group(1)
    return None

# 要求使用者輸入網址
url = input("請輸入 YouTube 網址：")
video_id = extract_youtube_id(url)

# 如果無法解析 ID，就直接退出
if not video_id:
    print("❌ 無法從網址中擷取影片 ID，請確認網址格式。")
    sys.exit(1)

try:
    # 取得字幕清單
    transcripts = YouTubeTranscriptApi.list_transcripts(video_id)

    print("\n📋 可用字幕列表：")
    for t in transcripts:
        print(f"語言代碼: {t.language_code}, 語言: {t.language}, 自動字幕: {t.is_generated}")

    # 嘗試抓取繁體中文或英文字幕（依優先順序）
    transcript = YouTubeTranscriptApi.get_transcript(
        video_id, 
        languages=['zh-TW', 'zh-Hant', 'zh-Hans', 'zh', 'en']
    )

    print("\n📝 字幕內容：")
    # for entry in transcript:
    #     start = entry['start']
    #     end = start + entry['duration']
    #     text = entry['text']
    #     print(f"{start:.2f}s - {end:.2f}s: {text}")
    subtitles = [entry["text"] for entry in transcript]
    print(subtitles)
    
except NoTranscriptFound:
    print("⚠️ 此影片無任何字幕（包括自動字幕）")
except TranscriptsDisabled:
    print("⚠️ 此影片的字幕功能已被禁用")
except Exception as e:
    print(f"❌ 發生錯誤：{e}")
