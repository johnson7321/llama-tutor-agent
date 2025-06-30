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

def check_and_get_video_id(url: str) -> str:
    """
    從 URL 擷取 YouTube 影片 ID，若失敗則印錯誤訊息並退出程式

    Args:
        url (str): YouTube 影片網址

    Returns:
        str: 擷取到的影片 ID
    """
    video_id = extract_youtube_id(url)
    if not video_id:
        print("❌ 無法擷取影片 ID")
        sys.exit(1)
    return video_id

def get_video_title(url: str) -> str:
    """
    使用 yt-dlp 取得 YouTube 影片標題

    Args:
        url (str): YouTube 影片網址

    Returns:
        str: 影片標題（若失敗會中止程式）
    """
    try:
        title = subprocess.check_output([
            "yt-dlp", "--get-filename", "-o", "%(title)s", url
        ], stderr=subprocess.STDOUT).decode("mbcs", errors="replace").strip()
        return title
    except subprocess.CalledProcessError as e:
        print("❌ 無法取得影片標題")
        print(e.output.decode("mbcs", errors="replace"))
        sys.exit(1)
        
# ✅ 嘗試擷取 YouTube 字幕        
def try_download_youtube_subtitle(video_id: str, cc_converter=None, srt_path: Path = None) -> str:
    """
    嘗試下載 YouTube 原生字幕，儲存為 .srt 檔案

    Args:
        video_id (str): YouTube 影片 ID
        cc_converter: 轉換簡繁體用的物件（例如 OpenCC），可為 None 表示不轉換
        srt_path (Path): 字幕檔名（不含資料夾）

    Returns:
        str: 字幕內容（若失敗則回傳空字串）
    """
    try:
        print("📋 嘗試取得 YouTube 原字幕...")

        transcript = YouTubeTranscriptApi.get_transcript(
            video_id,
            languages=['zh-TW', 'zh-Hant', 'zh-Hans', 'zh', 'en']
        )

        script_dir = Path(__file__).resolve().parent
        subtitle_folder = script_dir / "subtitles"
        subtitle_folder.mkdir(parents=True, exist_ok=True)
        srt_path = subtitle_folder / srt_path

        lines = []
        with open(srt_path, "w", encoding="utf-8") as f:
            for entry in transcript:
                text = entry["text"].strip()
                if cc_converter:
                    text = cc_converter.convert(text)
                lines.append(text)
                f.write(text + "\n")

        print(f"✅ 已使用 YouTube 字幕並輸出：{srt_path.name}")
        return "\n".join(lines)

    except (NoTranscriptFound, TranscriptsDisabled):
        print("⚠️ 沒有原字幕，改用 Whisper 處理")
        return ""
    except Exception as e:
        print(f"❌ 取得字幕時發生錯誤：{e}")
        return ""
    
def download_audio_if_needed(video_title: str, url: str, ffmpeg_path: str, output_dir: Path = None) -> Path:
    """
    檢查並下載 YouTube 音訊檔（mp3 格式），儲存在指定資料夾

    Args:
        video_title (str): 音訊檔命名用的標題
        url (str): YouTube 影片網址
        ffmpeg_path (str): ffmpeg 可執行檔路徑
        output_dir (Path, optional): mp3 輸出目錄，預設為專案目錄下的 'mp3_files'

    Returns:
        Path: 下載後或已存在的 mp3 檔案完整路徑
    """
    # 取得專案目錄
    script_dir = Path(__file__).resolve().parent

    # 設定輸出資料夾
    mp3_folder = output_dir or (script_dir / "mp3_files")
    mp3_folder.mkdir(parents=True, exist_ok=True)

    # 設定檔案名稱與路徑
    audio_filename = f"{video_title}.mp3"
    audio_path = mp3_folder / audio_filename

    if not audio_path.exists():
        print("🎧 下載音訊中...")
        result = subprocess.run([
            "yt-dlp", "-x", "--audio-format", "mp3",
            "--no-overwrites",
            f"--ffmpeg-location={ffmpeg_path}",
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

    return audio_path
# ✅ Whisper 辨識
def transcribe_audio_to_txt(audio_path: Path, cc_converter=None, output_dir: Path = None, model_size: str = "base") -> Path:
    """
    使用 Whisper 轉錄音訊並輸出為字幕 .srt 檔案（純文字）

    Args:
        audio_path (Path): 音訊檔路徑（.mp3）
        cc_converter: OpenCC 物件（可選）用來簡轉繁或繁轉簡
        output_dir (Path, optional): 輸出字幕的資料夾，預設為專案中的 'subtitles'
        model_size (str): Whisper 模型大小，例如 base, small, medium, large

    Returns:
        Path: 儲存好的字幕檔案路徑
    """
    print(f"🎤 使用 Whisper 模型轉錄音訊：{audio_path.name}")

    # 1. 載入模型
    try:
        model = whisper.load_model(model_size)
    except Exception as e:
        print(f"❌ Whisper 模型載入失敗：{e}")
        sys.exit(1)

    # 2. 執行轉錄
    try:
        result = model.transcribe(str(audio_path))
    except Exception as e:
        print(f"❌ 轉錄失敗：{e}")
        sys.exit(1)

    # 3. 準備輸出資料夾與檔案路徑
    script_dir = Path(__file__).resolve().parent
    subtitle_folder = output_dir or (script_dir / "subtitles")
    subtitle_folder.mkdir(parents=True, exist_ok=True)
    srt_path = subtitle_folder / audio_path.with_suffix(".txt").name

    # 4. 將字幕寫入檔案（純文字模式）
    with open(srt_path, "w", encoding="utf-8") as f:
        for i, seg in enumerate(result["segments"], start=1):
            text = seg["text"].strip()
            if cc_converter:
                text = cc_converter.convert(text)
            f.write(text + "\n")

    print(f"✅ Whisper 完成！字幕儲存為：{srt_path.name}")
    return srt_path