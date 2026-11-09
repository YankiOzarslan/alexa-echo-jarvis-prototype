import os
import json
import random
import logging
from pathlib import Path
from datetime import datetime
import httpx
from . import config

logger = logging.getLogger("JarvisGitHubScout")

HISTORY_FILE = Path(__file__).resolve().parent.parent / "github_project_history.json"

# Curated fallback knowledge base of cutting-edge open source projects
CURATED_PROJECTS = [
    {
        "name": "short-video-maker",
        "full_name": "gyoridavid/short-video-maker",
        "html_url": "https://github.com/gyoridavid/short-video-maker",
        "description": "Automated short video generator utilizing AI scripts, text-to-speech, and FFmpeg video assembly.",
        "stars": 2400,
        "language": "Python",
        "topics": ["video-automation", "ffmpeg", "tiktok", "shorts", "edge-tts"],
        "project_idea": "Auto-Clipper & Viral Hook SaaS",
        "skills_learned": ["FFmpeg Filter Graphs", "SubRip / ASS Subtitle Alignment", "Audio Processing (Sidechain/Ducking)", "Async Video Pipelines"],
        "mvp_steps": [
            "1. Adım: Bir YouTube veya Twitch yayın kaydını yt-dlp ile indirip Whisper ile transkribe et.",
            "2. Adım: En komik/heyecanlı 60 saniyelik anı LLM ile tespit edip 9:16 oranında kırp (crop).",
            "3. Adım: Hormozi tarzı renkli kelime kelime altyazı ve telifsiz arka plan fon müziği ekle.",
            "4. Adım: Çıktıyı doğrudan Telegram'a veya TikTok taslaklarına aktaran bir webhook oluştur."
        ],
        "monetization": "İçerik üreticilerine ve yayıncılara otomatik klip çıkaran aylık abonelikli bir Micro-SaaS ($19/ay) veya portföy için yıldız proje."
    },
    {
        "name": "browser-use",
        "full_name": "browser-use/browser-use",
        "html_url": "https://github.com/browser-use/browser-use",
        "description": "Make websites accessible for AI agents. Open-source web automation library powered by LLMs.",
        "stars": 32000,
        "language": "Python",
        "topics": ["ai-agents", "playwright", "automation", "browser"],
        "project_idea": "Kişisel Otonom Başvuru & Fiyat Takip Ajanı",
        "skills_learned": ["Playwright / CDP (Chrome DevTools Protocol)", "DOM Tree & Accessibility Tree Parsing", "Vision LLM Action Planning", "State Machines"],
        "mvp_steps": [
            "1. Adım: Playwright ile headless bir Chromium tarayıcısı ayağa kaldır ve sayfa ekran görüntüsü al.",
            "2. Adım: Gemini Flash Vision'a tıklanabilir elementleri işaretletip (Bbox) sonraki aksiyonu planlat.",
            "3. Adım: Kullanıcının verdiği bir görevi (örn: 'En ucuz Berlin uçak biletini bul ve sepeti aç') otonom tamamlat.",
            "4. Adım: İşlem bittiğinde Mac bildirim sesi çalsın ve Telegram'a rapor atsın."
        ],
        "monetization": "E-ticaret fiyat takipçisi, LinkedIn otomatik networking veya emlak fırsat radarı olarak freelance/SaaS potansiyeli çok yüksek."
    },
    {
        "name": "crawl4ai",
        "full_name": "unclecode/crawl4ai",
        "html_url": "https://github.com/unclecode/crawl4ai",
        "description": "Open-source LLM-friendly web crawler & scraper designed for AI pipelines and RAG.",
        "stars": 28000,
        "language": "Python",
        "topics": ["scraping", "rag", "markdown", "crawling"],
        "project_idea": "Canlı Borsa & Kripto Haber RAG Ajanı",
        "skills_learned": ["High-Performance Async Scraping", "HTML-to-Markdown Temizleme", "ChromaDB / Qdrant Vektör Arama", "RAG Pipeline Tasarımı"],
        "mvp_steps": [
            "1. Adım: Belirlediğin 5 finans/teknoloji sitesini periyodik olarak arka planda tara.",
            "2. Adım: Sayfadaki reklamları ve menüleri temizleyip salt markdown içeriğe dönüştür.",
            "3. Adım: Metinleri chunk'lara bölüp yerel bir vektör veri tabanına (ChromaDB) göm.",
            "4. Adım: Jarvis'e 'Bugün Apple hissesi hakkında ne yazıldı?' diye sorunca anlık kaynaklı özet al."
        ],
        "monetization": "Hedge fonları veya yatırımcılar için anlık duygu (sentiment) analiz bülteni veya kurumsal bilgi tabanı botu."
    },
    {
        "name": "livekit-agents",
        "full_name": "livekit/agents",
        "html_url": "https://github.com/livekit/agents",
        "description": "Build real-time voice and multimodal AI agents with ultra-low latency WebRTC.",
        "stars": 9500,
        "language": "Python",
        "topics": ["realtime-ai", "voice-assistant", "webrtc", "vad"],
        "project_idea": "Sıfır Gecikmeli Sesli Mülakat & Pratik Partneri",
        "skills_learned": ["WebRTC Protokolü", "VAD (Voice Activity Detection - Silero)", "Streaming STT & TTS", "Full-Duplex İletişim"],
        "mvp_steps": [
            "1. Adım: Tarayıcıdan mikrofon akışını WebRTC ile FastAPI sunucuna aktar.",
            "2. Adım: Silero VAD ile kullanıcının susup konuşmayı bıraktığı anı 100ms içinde yakala.",
            "3. Adım: Deepgram / Whisper stream ile metne döküp LLM yanıtını anında Edge-TTS stream ile geri çal.",
            "4. Adım: Kullanıcı konuşmaya başladığı anda Jarvis'in sesini kes (Barge-in yeteneği)."
        ],
        "monetization": "Yazılımcılar için İngilizce teknik mülakat simülatörü veya çağrı merkezleri için yapay zeka santrali."
    },
    {
        "name": "openmanus",
        "full_name": "OpenManus/OpenManus",
        "html_url": "https://github.com/OpenManus/OpenManus",
        "description": "Open-source autonomous general-purpose agent framework inspired by Manus AI.",
        "skills_learned": ["Multi-Agent Orchestration", "Dynamic Tool Calling", "Sandboxed Code Execution", "Self-Correction Loops"],
        "stars": 18000,
        "language": "Python",
        "topics": ["ai-agents", "autonomous", "tools", "planning"],
        "project_idea": "Kendi Başına İş Bitiren Mac Masaüstü Ajanı",
        "mvp_steps": [
            "1. Adım: Bir görev verildiğinde (örn: 'X konusunu araştır ve PDF raporu oluştur') adımları planlayan bir Planner Ajanı yaz.",
            "2. Adım: Her adımda terminalde komut çalıştırabilen veya kod yazabilen bir Executor Ajanı entegre et.",
            "3. Adım: Hata aldığında terminal çıktısını okuyup kodu kendi kendine düzelten bir Reflector döngüsü kur.",
            "4. Adım: Sonuç raporunu otomatik masaüstüne PDF olarak kaydedip Mac'te açtır."
        ],
        "monetization": "Freelance işleri (veri toplama, raporlama, excel temizleme) otonom yapan dijital asistan servisi."
    },
    {
        "name": "fastapi",
        "full_name": "tiangolo/fastapi",
        "html_url": "https://github.com/tiangolo/fastapi",
        "description": "Modern, fast web framework for building APIs with Python and async support.",
        "stars": 82000,
        "language": "Python",
        "topics": ["api", "asyncio", "backend", "pydantic"],
        "project_idea": "Dağıtık Arka Plan Görev Motoru (Celery Alternatifi)",
        "skills_learned": ["FastAPI BackgroundTasks & WebSockets", "Redis Pub/Sub ve Queue Yönetimi", "Worker Process Havuzu", "Gerçek Zamanlı İlerleme Çubuğu"],
        "mvp_steps": [
            "1. Adım: Kullanıcının ağır işleri (video render, büyük dosya işleme) gönderdiği bir POST endpoint'i aç.",
            "2. Adım: Bu işi Redis kuyruğuna at ve kullanıcıya anında bir `job_id` dön.",
            "3. Adım: Arka planda çalışan bağımsız bir Python worker'ı bu işi kuyruktan alıp işlesin.",
            "4. Adım: WebSocket üzerinden tarayıcıya veya istemciye anlık yüzde (%10, %50, %100) ilerleme bildirimi gönder."
        ],
        "monetization": "Herhangi bir SaaS ürününün ölçeklenebilir omurgası. CV'de ve backend mülakatlarında doğrudan kıdemli seviye gösterir."
    }
]

def load_history() -> list:
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_history(history: list):
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error saving GitHub scout history: {e}")

async def fetch_github_trending(topic: str = None) -> list:
    """Fetches trending or popular repos from GitHub API across key learning domains."""
    topics = [
        "ai-agents", "video-automation", "voice-ai", "browser-automation",
        "fastapi", "mcp-server", "llm-tools"
    ]
    chosen_topic = topic or random.choice(topics)
    url = f"https://api.github.com/search/repositories?q={chosen_topic}+stars:>500&sort=stars&order=desc&per_page=10"
    headers = {
        "User-Agent": "Jarvis-GitHub-Scout/1.0",
        "Accept": "application/vnd.github.v3+json"
    }

    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                items = data.get("items", [])
                if items:
                    return items
    except Exception as e:
        logger.warning(f"Live GitHub fetch failed ({e}). Falling back to curated projects.")

    return []

async def get_daily_project_idea(topic_filter: str = None) -> dict:
    """
    Selects or synthesizes a high-impact daily project idea.
    Avoids recent repeats and formats into an inspiring action roadmap.
    """
    history = load_history()
    used_names = {entry.get("name") for entry in history[-10:]}

    # 1. Filter curated projects not recently shown
    available_curated = [p for p in CURATED_PROJECTS if p["name"] not in used_names]
    if not available_curated:
        available_curated = CURATED_PROJECTS

    # If topic specified, try matching
    if topic_filter:
        matched = [p for p in available_curated if any(topic_filter.lower() in t for t in p.get("topics", []))]
        if matched:
            project = random.choice(matched)
        else:
            project = random.choice(available_curated)
    else:
        project = random.choice(available_curated)

    # Record to history
    history.append({
        "name": project["name"],
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "title": project["project_idea"]
    })
    save_history(history)

    # Format text outputs
    spoken_text = (
        f"Günün açık kaynak proje fikrini hazırladım efendim: {project['project_idea']}. "
        f"Bu proje, GitHub'daki popüler {project['full_name']} reposundan ilham alıyor. "
        f"Özellikle {', '.join(project['skills_learned'][:2])} konularında kendinizi geliştirmeniz ve "
        f"harika bir portföy projesi üretmeniz için tasarlandı. Detaylı yol haritasını Telegram'a ve ekrana aktardım."
    )

    steps_md = "\n".join(project["mvp_steps"])
    skills_md = " • ".join(project["skills_learned"])

    markdown_card = (
        f"🚀 *GÜNÜN GİTHUB PROJE FİKRİ & GELİŞİM REHBERİ*\n\n"
        f"📌 *Proje:* `{project['project_idea']}`\n"
        f"🌟 *İlham Kaynağı Repo:* [{project['full_name']}]({project['html_url']}) ⭐ {project['stars']:,}\n"
        f"📖 *Repo Özeti:* _{project['description']}_\n\n"
        f"🛠️ *Sana Ne Öğretir? (Kazanılacak Yetenekler):*\n"
        f"👉 *{skills_md}*\n\n"
        f"🗺️ *1 Günde MVP Nasıl İnşa Edilir?*\n"
        f"{steps_md}\n\n"
        f"💰 *Portföy ve Gelir Potansiyeli:*\n"
        f"{project['monetization']}\n\n"
        f"💡 *Jarvis İpucu:* 'Bu projeyi kodlamaya başlayalım' derseniz, temel iskelet kodunu hemen Desktop'ta oluşturup VS Code'da açabilirim, Sir!"
    )

    return {
        "project": project,
        "spoken": spoken_text,
        "markdown": markdown_card
    }

async def send_daily_project_to_telegram(chat_id: str = None) -> bool:
    """Sends the formatted project idea directly to the user's Telegram."""
    token = config.get_telegram_token()
    target_chat = chat_id or config.get_telegram_chat_id()
    if not token or not target_chat:
        logger.warning("Telegram credentials missing for GitHub scout delivery.")
        return False

    idea_data = await get_daily_project_idea()
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": target_chat,
        "text": idea_data["markdown"],
        "parse_mode": "Markdown",
        "disable_web_page_preview": False
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code == 200:
                logger.info("Daily GitHub project idea successfully delivered to Telegram!")
                return True
            else:
                logger.error(f"Telegram API error {resp.status_code}: {resp.text}")
    except Exception as e:
        logger.error(f"Failed to send project idea to Telegram: {e}")

    return False
