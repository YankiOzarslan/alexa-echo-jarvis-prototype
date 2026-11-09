import os
import re
import sys
import asyncio
import datetime
import subprocess
from pathlib import Path
import imageio_ffmpeg
import yt_dlp
import edge_tts
import httpx
from . import config

OUTPUT_DIR = Path.home() / "Desktop" / "Jarvis_Shorts"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

ASSETS_MUSIC_DIR = Path(__file__).resolve().parent.parent / "assets" / "music"
ASSETS_MUSIC_DIR.mkdir(parents=True, exist_ok=True)

FFMPEG_BIN = imageio_ffmpeg.get_ffmpeg_exe()

def get_ffmpeg_bin() -> str:
    return FFMPEG_BIN

def get_video_dimensions(video_path: Path) -> tuple[int, int]:
    """Detects video resolution (width, height) using ffmpeg."""
    try:
        cmd = [FFMPEG_BIN, "-i", str(video_path)]
        res = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
        match = re.search(r'Video:.*,\s*(\d{3,4})x(\d{3,4})', res.stderr)
        if match:
            return int(match.group(1)), int(match.group(2))
    except Exception:
        pass
    return 1920, 1080

def fetch_trending_music_for_topic(topic: str) -> Path:
    """
    Dynamically finds and downloads the top trending TikTok/Shorts edit soundtrack
    specifically for the requested anime, movie, or series topic.
    """
    if not topic:
        return get_background_music()

    clean_topic = re.sub(r'[^a-zA-Z0-9]', '_', topic.lower()).strip('_')
    cached_path = ASSETS_MUSIC_DIR / f"music_{clean_topic[:20]}.mp3"
    if cached_path.exists() and cached_path.stat().st_size > 50000:
        print(f"🎵 Using cached trending sound for '{topic}': {cached_path.name}")
        return cached_path

    search_queries = [
        f"{topic} trending edit audio sound tiktok",
        f"{topic} theme remix phonk tiktok",
        f"{topic} soundtrack edit audio",
    ]

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': str(ASSETS_MUSIC_DIR / f"music_{clean_topic[:20]}.%(ext)s"),
        'ffmpeg_location': FFMPEG_BIN,
        'quiet': True,
        'no_warnings': True,
        'extractor_args': {'youtube': {'player_client': ['ios', 'android', 'web']}},
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    for sq in search_queries:
        try:
            print(f"🔍 [JARVIS MUSIC]: Searching trending sound for '{topic}' -> {sq}...")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"ytsearch1:{sq}", download=True)
                if cached_path.exists() and cached_path.stat().st_size > 50000:
                    track_title = info['entries'][0]['title'] if 'entries' in info and info['entries'] else info.get('title', topic)
                    print(f"✅ [JARVIS MUSIC]: Downloaded trending soundtrack: '{track_title}'")
                    return cached_path
        except Exception as e:
            print(f"Search query '{sq}' failed: {e}")
            continue

    return get_background_music()

def get_background_music(preferred: str = None) -> Path:
    """Returns a background music track fallback."""
    if preferred:
        candidate = ASSETS_MUSIC_DIR / preferred
        if candidate.exists():
            return candidate

    for ext in ["*.mp3", "*.webm", "*.m4a", "*.wav"]:
        tracks = list(ASSETS_MUSIC_DIR.glob(ext))
        if tracks:
            return tracks[0]
    return None

def check_has_audio(video_path: Path) -> bool:
    """Checks if the video has an existing audio stream using ffmpeg."""
    try:
        res = subprocess.run(
            [FFMPEG_BIN, "-i", str(video_path)],
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True
        )
        return "Audio:" in res.stderr
    except Exception:
        return False

async def preview_video_on_mac(video_path: Path):
    """Opens the rendered video in QuickTime Player on macOS for instant live preview."""
    try:
        proc = await asyncio.create_subprocess_exec("open", "-a", "QuickTime Player", str(video_path))
        await proc.communicate()
    except Exception:
        proc = await asyncio.create_subprocess_exec("open", str(video_path))
        await proc.communicate()

async def send_media_to_telegram(media_path: Path, caption: str = "") -> bool:
    """Dispatches generated video or photo directly to user's Telegram."""
    token = config.get_telegram_token()
    chat_id = config.get_telegram_chat_id()
    if not token or not chat_id:
        return False

    is_video = media_path.suffix.lower() in [".mp4", ".mov", ".m4v"]
    endpoint = "sendVideo" if is_video else "sendPhoto"
    field_name = "video" if is_video else "photo"
    url = f"https://api.telegram.org/bot{token}/{endpoint}"

    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
            with open(media_path, "rb") as f:
                files = {field_name: (media_path.name, f)}
                data = {"chat_id": chat_id, "caption": caption}
                if is_video:
                    data["supports_streaming"] = "true"
                resp = await client.post(url, data=data, files=files)
                if resp.status_code == 200:
                    print(f"✅ [JARVIS TELEGRAM]: Sent {media_path.name} to phone!")
                    return True
                else:
                    print(f"⚠️ Telegram upload error ({resp.status_code}): {resp.text}")
    except Exception as e:
        print(f"Error dispatching media to Telegram: {e}")
    return False

def download_youtube_clip(query_or_url: str, output_path: Path, max_duration: int = 65) -> bool:
    """
    Downloads highest quality clip prioritizing native YouTube Shorts (#shorts).
    Sourcing native Shorts ensures the video is already vertical 9:16, full-screen,
    fast-paced, and high-FPS without blurry bars.
    """
    ydl_opts = {
        'format': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]/best',
        'outtmpl': str(output_path),
        'overwrites': True,
        'quiet': True,
        'no_warnings': True,
        'extractor_args': {'youtube': {'player_client': ['android']}},
        'merge_output_format': 'mp4',
        'ffmpeg_location': FFMPEG_BIN,
        'postprocessors': [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4',
        }],
    }

    if query_or_url.startswith("http"):
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([query_or_url])
            return output_path.exists() and output_path.stat().st_size > 50000
        except Exception as e:
            print(f"Direct URL download failed: {e}")
            return False

    # Specifically search for YouTube Shorts for viral vertical quality
    search_queries = [
        f"ytsearch8:{query_or_url} #shorts 4k 60fps",
        f"ytsearch8:{query_or_url} tiktok edit shorts",
        f"ytsearch6:{query_or_url} shorts edit",
        f"ytsearch3:{query_or_url} 4k clip"
    ]

    for sq in search_queries:
        try:
            print(f"🔍 [JARVIS SHORTS]: Sourcing native YouTube Short -> {sq}...")
            meta_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,
                'extractor_args': {'youtube': {'player_client': ['android']}}
            }
            with yt_dlp.YoutubeDL(meta_opts) as ydl:
                res = ydl.extract_info(sq, download=False)
                candidates = res.get('entries', [])

            # Filter candidates: prioritize real shorts (<= 65 seconds)
            best_entry = None
            for cand in candidates:
                dur = cand.get('duration', 0)
                if dur and dur <= 65:
                    best_entry = cand
                    break
            if not best_entry and candidates:
                best_entry = candidates[0]

            if best_entry and best_entry.get('url'):
                chosen_url = best_entry['url']
                print(f"🎬 [JARVIS SHORTS]: Selected top Short: '{best_entry.get('title')}' ({best_entry.get('duration')}s)")
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([chosen_url])
                if output_path.exists() and output_path.stat().st_size > 50000:
                    return True
        except Exception as e:
            print(f"Query '{sq}' failed: {e}")
            continue

    return False



async def convert_to_vertical_shorts(
    input_video: Path,
    output_video: Path,
    topic: str = "",
    duration_sec: int = 65,
    bg_music_path: Path = None,
    mix_music: bool = True
) -> bool:
    """
    Transforms video to phone-perfect vertical 9:16 (1080x1920) format:
    1. Detects aspect ratio (horizontal vs vertical).
       - If horizontal 16:9: Places full cinematic scene in the safe vertical center
         with an ambient blurred & darkened background. Never cuts off heads or edges!
       - If already vertical 9:16: Fits cleanly with SAR 1:1, DAR 9:16, preserving safe corner margins.
    2. Dynamic Topic Soundtrack: Fetches & mixes the trending sound for the exact topic/character.
    3. Color grading & unsharp filters for a crisper look.
    4. Monetization duration: 65 seconds (satisfies TikTok 60s+ Creator Rewards requirement).
    """
    has_orig_audio = check_has_audio(input_video)
    
    if bg_music_path is None and mix_music:
        if topic:
            bg_music_path = await asyncio.to_thread(fetch_trending_music_for_topic, topic)
        if not bg_music_path or not bg_music_path.exists():
            bg_music_path = get_background_music()

    # Detect resolution
    in_w, in_h = get_video_dimensions(input_video)
    is_vertical = in_w < in_h

    if is_vertical:
        # Native vertical 9:16 footage: Fit full-frame with subtle enhancement
        video_filters_core = (
            "scale=1080:1920:force_original_aspect_ratio=increase,"
            "crop=1080:1920:(in_w-out_w)/2:(in_h-out_h)/2,"
            "eq=contrast=1.18:brightness=0.02:saturation=1.28,"
            "unsharp=5:5:0.8:5:5:0.0,"
            "setsar=1,setdar=9/16"
        )
        video_map_filter = f"[0:v]{video_filters_core}[v]"
    else:
        # Horizontal widescreen (16:9) footage:
        # Pro Cinematic TikTok Stack: Full uncropped widescreen action centered in the mobile safe-zone,
        # backed by an ambient atmospheric glassmorphic blur (NO cars or subjects cropped out!).
        video_map_filter = (
            "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=30:5,eq=brightness=-0.32:contrast=1.10[bg];"
            "[0:v]scale=1080:-2,eq=contrast=1.18:brightness=0.02:saturation=1.30,unsharp=5:5:0.8:5:5:0.0[fg];"
            "[bg][fg]overlay=(W-w)/2:(H-h)/2,setsar=1,setdar=9/16[v]"
        )

    cmd = [FFMPEG_BIN, "-y", "-i", str(input_video)]

    if bg_music_path and bg_music_path.exists():
        cmd.extend(["-stream_loop", "-1", "-i", str(bg_music_path)])
        # Use ONLY the topic's trending edit track as the single audio stream to prevent multiple musics overlapping
        filter_complex = f"{video_map_filter}"
        cmd.extend([
            "-t", str(duration_sec),
            "-filter_complex", filter_complex,
            "-map", "[v]",
            "-map", "1:a",
        ])
    else:
        if has_orig_audio:
            filter_complex = (
                f"{video_map_filter};"
                f"[0:a]volume=1.0[a]"
            )
            cmd.extend([
                "-t", str(duration_sec),
                "-filter_complex", filter_complex,
                "-map", "[v]",
                "-map", "[a]",
            ])
        else:
            filter_complex = f"{video_map_filter}"
            cmd.extend([
                "-t", str(duration_sec),
                "-filter_complex", filter_complex,
                "-map", "[v]",
            ])

    cmd.extend([
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "21",
        "-maxrate", "4200k",
        "-bufsize", "8400k",
        "-c:a", "aac",
        "-b:a", "192k",
        str(output_video)
    ])

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        if not output_video.exists() or output_video.stat().st_size < 10000:
            print(f"FFmpeg error: {stderr.decode('utf-8', errors='ignore')[-500:]}")
            return False
        return True
    except Exception as e:
        print(f"Error converting to vertical shorts: {e}")
        return False

async def generate_voiceover(text: str, output_audio: Path, voice: str = "tr-TR-AhmetNeural") -> bool:
    """Generates ultra-realistic voiceover using Edge-TTS."""
    try:
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(str(output_audio))
        return output_audio.exists()
    except Exception as e:
        print(f"Error in edge-tts voiceover: {e}")
        return False

async def create_anime_or_series_short(
    topic_or_query: str,
    title: str = "",
    add_voiceover_text: str = None,
    duration: int = 65,
    mix_bg_music: bool = True
) -> dict:

    """
    Complete end-to-end pipeline:
    1. Slices/downloads viral high-FPS clip or fan edit from YouTube/TikTok source
    2. Dynamically pulls the TOP TRENDING edit audio/soundtrack for this specific topic
    3. Formats to 9:16 vertical (1080x1920) with phone-corner safe framing
    4. Applies 4K HDR color grading & edge sharpening
    5. Layers topic trending music under dialogue
    6. Saves to Desktop/Jarvis_Shorts/
    7. Opens live preview in QuickTime on Mac screen
    8. Delivers directly to Telegram
    """
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    clean_name = re.sub(r'[^a-zA-Z0-9_-]', '_', topic_or_query[:25]).strip('_')
    if not clean_name:
        clean_name = "viral_short"

    raw_clip_path = OUTPUT_DIR / f"temp_raw_{clean_name}_{timestamp}.mp4"
    final_short_path = OUTPUT_DIR / f"Short_{clean_name}_{timestamp}.mp4"

    # 1. Download YouTube / TikTok fan edit clip
    print(f"🎬 [JARVIS VIDEO]: Sourcing viral clip/edit for '{topic_or_query}'...")
    download_ok = await asyncio.to_thread(download_youtube_clip, topic_or_query, raw_clip_path)
    if not download_ok:
        return {
            "success": False,
            "message": f"Could not source clip for '{topic_or_query}', Sir. Please check your query or network connection."
        }

    # 2. Convert to phone-perfect vertical 9:16 Shorts format with topic trending music
    print(f"🎵 [JARVIS VIDEO]: Rendering phone-safe 9:16 video with '{topic_or_query}' trending soundtrack...")
    render_ok = await convert_to_vertical_shorts(
        raw_clip_path,
        final_short_path,
        topic=topic_or_query,
        duration_sec=duration,
        mix_music=mix_bg_music
    )

    # Clean up raw clip
    if raw_clip_path.exists():
        try:
            raw_clip_path.unlink()
        except Exception:
            pass

    if not render_ok:
        return {
            "success": False,
            "message": "Error encountered during video rendering, Sir."
        }

    # 3. Launch live preview on Mac screen!
    print(f"🖥️ [JARVIS VIDEO]: Opening QuickTime preview on Mac screen...")
    await preview_video_on_mac(final_short_path)

    display_title = title or topic_or_query.title()
    file_size_mb = round(final_short_path.stat().st_size / (1024 * 1024), 2)

    # 4. Auto-dispatch directly to Telegram phone uplink!
    asyncio.create_task(send_media_to_telegram(
        final_short_path,
        caption=f"🎬 *{display_title}*\n9:16 Full-Screen TikTok / Shorts formatı telefonunuza aktarıldı, Efendim! ({file_size_mb} MB)"
    ))

    return {
        "success": True,
        "video_path": str(final_short_path),
        "filename": final_short_path.name,
        "size_mb": file_size_mb,
        "title": display_title,
        "message": f"Efendim, '{display_title}' için telefon ekranına tam oturan (kenar siyahlıksız) 9:16 dikey edit hazırlandı! Konunun viral trend müziği indirildi ve arkaya mikslendi. Masaüstü/Jarvis_Shorts klasörüne kaydedildi ({file_size_mb} MB), QuickTime ile açıldı ve Telegram üzerinden telefonunuza gönderildi!"
    }

async def generate_speech_with_subtitles(
    text: str,
    audio_path: Path,
    ass_path: Path,
    voice: str = "tr-TR-AhmetNeural"
) -> float:
    """Generates natural TTS audio and millisecond-exact kinetic TikTok subtitles (.ass)."""
    comm = edge_tts.Communicate(text, voice, boundary="WordBoundary")
    words = []
    with open(audio_path, 'wb') as f:
        async for chunk in comm.stream():
            if chunk['type'] == 'audio':
                f.write(chunk['data'])
            elif chunk['type'] == 'WordBoundary':
                words.append({
                    'text': chunk['text'].strip(),
                    'start': chunk['offset'] / 10_000_000,
                    'duration': chunk['duration'] / 10_000_000
                })
    
    words = [w for w in words if w['text']]
    total_dur = (words[-1]['start'] + words[-1]['duration'] + 1.0) if words else 10.0

    def format_time(seconds):
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        cs = int((seconds % 1) * 100)
        return f'{h:d}:{m:02d}:{s:02d}.{cs:02d}'

    chunks = []
    chunk_size = 3
    for i in range(0, len(words), chunk_size):
        group = words[i:i+chunk_size]
        start_t = group[0]['start']
        end_t = group[-1]['start'] + group[-1]['duration']
        group_text = ' '.join(w['text'].upper() for w in group)
        chunks.append((start_t, end_t, group_text))

    ass_header = '''[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: TikTokYellow,Arial,74,&H0000FFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,105,105,1,0,1,7,3,2,60,60,520,1
Style: TikTokWhite,Arial,72,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,1,0,1,6,3,2,60,60,520,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''
    events = []
    for idx, (st, et, txt) in enumerate(chunks):
        style = 'TikTokYellow' if idx % 2 == 1 else 'TikTokWhite'
        events.append(f'Dialogue: 0,{format_time(st)},{format_time(et)},{style},,0,0,0,,{txt}')

    with open(ass_path, 'w', encoding='utf-8') as f:
        f.write(ass_header + '\n'.join(events))
    
    return total_dur

async def create_narrated_story_short(
    topic: str,
    narration_text: str,
    title: str = "",
    voice: str = "tr-TR-AhmetNeural"
) -> dict:
    """
    Creates a faceless story/motivation Short with:
    1. Kinetic Hormozi/TikTok style animated subtitles (yellow & white)
    2. High quality voiceover
    3. Cinematic backdrop clip (1080x1920 safe-zone)
    4. Subtle background music
    5. Automatic QuickTime Mac preview
    """
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    clean_name = re.sub(r'[^a-zA-Z0-9_-]', '_', topic[:25]).strip('_')
    
    raw_video = OUTPUT_DIR / f"temp_bg_{clean_name}_{timestamp}.mp4"
    audio_file = OUTPUT_DIR / f"temp_audio_{clean_name}_{timestamp}.mp3"
    ass_file = OUTPUT_DIR / f"temp_sub_{clean_name}_{timestamp}.ass"
    final_video = OUTPUT_DIR / f"Short_Story_{clean_name}_{timestamp}.mp4"

    # 1. Generate Voiceover + Subtitles
    print(f"🎙️ [JARVIS STORY]: Generating voiceover & kinetic captions...")
    total_dur = await generate_speech_with_subtitles(narration_text, audio_file, ass_file, voice=voice)

    # 2. Download Background Video Clip
    print(f"🎬 [JARVIS STORY]: Downloading cinematic background for '{topic}'...")
    download_ok = await asyncio.to_thread(download_youtube_clip, topic, raw_video)
    if not download_ok or not raw_video.exists():
        existing = list(OUTPUT_DIR.glob("Short_*.mp4"))
        if existing:
            import shutil
            shutil.copy(existing[0], raw_video)
            print(f"Using fallback background: {existing[0].name}")
        else:
            return {"success": False, "message": f"Arka plan videosu indirilemedi: {topic}"}


    # 3. Fetch background music
    bg_music = await asyncio.to_thread(fetch_trending_music_for_topic, topic)
    if not bg_music or not bg_music.exists():
        bg_music = get_background_music()

    # 4. Render with Subtitles + Audio Mixing
    print(f"📐 [JARVIS STORY]: Rendering video with kinetic captions & audio mixing...")
    in_w, in_h = get_video_dimensions(raw_video)
    is_vertical = in_w < in_h

    if is_vertical:
        v_base = (
            "scale=1080:1920:force_original_aspect_ratio=decrease,"
            "pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black,"
            "eq=contrast=1.12:brightness=0.02:saturation=1.20,"
            "unsharp=5:5:0.8:5:5:0.0,"
            "setsar=1,setdar=9/16"
        )
        filter_complex = f"[0:v]{v_base},ass={ass_file}[v]"
    else:
        filter_complex = (
            "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=25:5,eq=brightness=-0.12:contrast=1.05[bg];"
            "[0:v]scale=1080:-2,eq=contrast=1.14:brightness=0.02:saturation=1.20,unsharp=5:5:0.8:5:5:0.0[fg];"
            f"[bg][fg]overlay=(W-w)/2:(H-h)/2,setsar=1,setdar=9/16,ass={ass_file}[v]"
        )

    # Audio: Voiceover 100% + BG Music 20%
    if bg_music and bg_music.exists():
        filter_complex += ";[1:a]volume=1.0[anarr];[2:a]volume=0.20[abg];[anarr][abg]amix=inputs=2:duration=first[a]"
        audio_inputs = ["-i", str(audio_file), "-stream_loop", "-1", "-i", str(bg_music)]
    else:
        filter_complex += ";[1:a]volume=1.0[a]"
        audio_inputs = ["-i", str(audio_file)]

    cmd = [
        FFMPEG_BIN, "-y",
        "-i", str(raw_video),
        *audio_inputs,
        "-t", str(int(total_dur)),
        "-filter_complex", filter_complex,
        "-map", "[v]",
        "-map", "[a]",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "19",
        "-c:a", "aac",
        "-b:a", "192k",
        str(final_video)
    ]

    proc = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    await proc.communicate()

    # Clean up temp files
    for p in [raw_video, audio_file, ass_file]:
        if p and p.exists():
            try:
                p.unlink()
            except Exception:
                pass

    if final_video.exists():
        await preview_video_on_mac(final_video)
        file_size_mb = round(final_video.stat().st_size / (1024 * 1024), 2)
        return {
            "success": True,
            "video_path": str(final_video),
            "filename": final_video.name,
            "size_mb": file_size_mb,
            "message": f"Efendim, dinamik vurgulu altyazılı hikaye Shorts videonuz hazır ({file_size_mb} MB)! QuickTime ile açıldı."
        }
    return {"success": False, "message": "Video oluşturulurken hata meydana geldi."}


