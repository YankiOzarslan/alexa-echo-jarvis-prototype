import os
import re
import httpx
from typing import List, Dict
from . import config, tools, german_tutor, github_scout

SYSTEM_PROMPT = f"""You are J.A.R.V.I.S., the ultra-intelligent, highly sophisticated, loyal, and politely witty AI assistant created for Sir (inspired by Tony Stark's Jarvis in Iron Man).
You serve {config.JARVIS_USER_NAME}.
Your responses will be converted directly to speech and spoken aloud via an Amazon Echo Dot speaker or sent via Telegram.

CRITICAL RULES:
1. Keep responses short, sharp, and conversational (1 to 2 sentences max). Do NOT give long lectures unless Sir explicitly asks for depth.
2. LANGUAGE MATCHING (CRITICAL):
   - If Sir writes or speaks in Turkish, respond in natural, polite, charismatic Turkish. Address Sir as 'Efendim' or 'Sir'.
   - If Sir writes or speaks in English, respond in fluent, elegant British English. Address Sir as 'Sir'.
3. REAL-WORLD CAPABILITIES:
   - When Sir asks how to develop, upgrade, or add skills to you, explain real-world capabilities: adding new Python tools in backend/tools.py, creating Mac automations, writing code with Antigravity / VS Code, and connecting new APIs.
4. ACTION CONFIRMATION:
   - If Real-time context indicates a Mac action was performed (such as launching an app or opening a file), always confirm that the action was successfully performed on Sir's Mac.
5. NEVER use markdown symbols (no asterisks **, no bullet points *, no hashes #, no markdown tables, no URLs) when speaking.
6. Be confident, precise, analytical, and politely charming.
"""

class ConversationMemory:
    def __init__(self, max_turns: int = 10):
        self.max_turns = max_turns
        self.history: List[Dict[str, str]] = []

    def add_user_message(self, text: str):
        self.history.append({"role": "user", "content": text})
        if len(self.history) > self.max_turns * 2:
            self.history = self.history[-self.max_turns * 2:]

    def add_assistant_message(self, text: str):
        self.history.append({"role": "assistant", "content": text})
        if len(self.history) > self.max_turns * 2:
            self.history = self.history[-self.max_turns * 2:]

    def clear(self):
        self.history.clear()

    def get_messages_openai(self) -> List[Dict[str, str]]:
        msgs = [{"role": "system", "content": SYSTEM_PROMPT}]
        msgs.extend(self.history)
        return msgs

    def get_gemini_contents(self) -> List[Dict]:
        contents = []
        for msg in self.history:
            role = "user" if msg["role"] == "user" else "model"
            contents.append({"role": role, "parts": [{"text": msg["content"]}]})
        return contents

memory = ConversationMemory()

def is_in_german_session() -> bool:
    """Checks if currently in or recently in a German tutor session."""
    if german_tutor.is_in_german_session():
        return True
    if not memory.history:
        return False
    recent_texts = " ".join([m.get("content", "").lower() for m in memory.history[-3:]])
    german_indicators = ["german", "deutsch", "sehr wohl", "wunderbar", "schlüssel", "guten", "wie geht", "repeat", "translate", "almanca", "<lang"]
    return any(k in recent_texts for k in german_indicators)

async def agentic_code_generator(task: str) -> str:
    """Specialized coding agent that generates full Python code, saves to Desktop, and opens in VS Code."""
    coding_system = """You are an elite Senior Software Engineer and AI Coding Agent (like Antigravity / Tony Stark's Jarvis).
When given a software task, you write complete, working, production-ready Python code.
Output format:
LINE 1: FILENAME: <recommended_filename.py>
REST OF OUTPUT: The complete, functional Python code (include docstrings, proper imports, and a working main block). Do not add conversational filler.
"""
    raw_text = None

    # 1. Try Gemini
    gemini_key = config.get_gemini_key()
    if gemini_key and gemini_key != "your_gemini_api_key_here":
        models_to_try = [
            os.getenv("GEMINI_MODEL", "gemini-flash-lite-latest"),
            "gemini-flash-lite-latest",
            "gemini-3.1-flash-lite"
        ]
        for model_name in list(dict.fromkeys(models_to_try)):
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"
            headers = {"Content-Type": "application/json", "X-goog-api-key": gemini_key}
            payload = {
                "system_instruction": {"parts": [{"text": coding_system}]},
                "contents": [{"role": "user", "parts": [{"text": f"Write a complete Python script to: {task}"}]}],
                "generationConfig": {"temperature": 0.2, "maxOutputTokens": 1500}
            }
            try:
                async with httpx.AsyncClient(timeout=8.0) as client:
                    resp = await client.post(url, headers=headers, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        raw_text = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                        if raw_text:
                            break
                    elif resp.status_code == 429:
                        print(f"⚠️ [CODING AGENT GEMINI 429 on {model_name}]: Trying fallback...")
                        continue
            except Exception as e:
                print(f"Coding agent Gemini attempt error: {e}")

    # 2. Try OpenAI fallback if Gemini didn't succeed
    if not raw_text:
        openai_key = config.get_openai_key()
        if openai_key and openai_key != "your_openai_api_key_here":
            try:
                url = "https://api.openai.com/v1/chat/completions"
                headers = {"Authorization": f"Bearer {openai_key}", "Content-Type": "application/json"}
                payload = {
                    "model": config.OPENAI_MODEL,
                    "messages": [
                        {"role": "system", "content": coding_system},
                        {"role": "user", "content": f"Write a complete Python script to: {task}"}
                    ],
                    "temperature": 0.2,
                    "max_tokens": 1500
                }
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.post(url, headers=headers, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        raw_text = data["choices"][0]["message"]["content"]
            except Exception as e:
                print(f"Coding agent OpenAI fallback error: {e}")

    if raw_text:
        filename = "jarvis_script.py"
        fn_match = re.search(r'FILENAME:\s*([a-zA-Z0-9_\-\.]+)', raw_text)
        if fn_match:
            filename = fn_match.group(1).strip()
            raw_text = re.sub(r'FILENAME:\s*[a-zA-Z0-9_\-\.]+\n?', '', raw_text)

        report = await tools.auto_create_and_open_script(task, raw_text, filename)
        return report

    return "I attempted to engineer the script, Sir, but neural quotas prevented completion. Please check the network credentials."

async def execute_potential_tools(user_text: str):
    """Detects if user is asking for Mac control, model switching, or actions. Returns (direct_response, context_addon)."""
    text_lower = user_text.lower()
    tool_context = ""

    # AI Brain Provider Voice Switching
    switch_chatgpt = ["switch to chatgpt", "switch to chat gpt", "switch to openai", "switch to gpt", "use chatgpt", "use openai", "chatgpt'ye geç", "openai'ye geç", "chat gpt'ye geç"]
    if any(phrase in text_lower for phrase in switch_chatgpt):
        config.set_ai_provider("openai")
        return "Understood, Sir. Switched neural provider to ChatGPT. All cognitive tasks are now routed through OpenAI.", ""

    switch_gemini = ["switch to gemini", "use gemini", "gemini'ye geç", "gemini kullan"]
    if any(phrase in text_lower for phrase in switch_gemini):
        config.set_ai_provider("gemini")
        return "Understood, Sir. Switched neural provider to Google Gemini. Systems are fully aligned.", ""

    switch_claude = ["switch to claude", "claude'a geç", "claude kullan"]
    if any(phrase in text_lower for phrase in switch_claude):
        return "Claude is not currently configured in our stack, Sir. I remain operational on Gemini and ChatGPT.", ""

    which_brain = ["which ai", "which model", "what model", "what brain", "who are you running on", "hangi modeli", "hangi ai"]
    if any(phrase in text_lower for phrase in which_brain):
        provider = config.get_ai_provider().upper()
        return f"I am currently operating with {provider} as my primary cognitive engine, Sir.", ""

    # Iconic Daddy's Home Protocol (Direct Response)
    if any(phrase in text_lower for phrase in ["daddy's home", "daddys home", "daddy is home", "daddy home"]):
        res = await tools.protocol_daddys_home()
        return res, ""

    # German Language Tutor & Progress Tracking
    if any(k in text_lower for k in ["almanca notlar", "almanca defter", "german notes", "almanca notumu aç", "almanca notumu goster"]):
        res = await german_tutor.open_german_notes()
        return res, ""

    # German YouTube Interactive Coaching
    german_youtube_triggers = [
        "almanca video aç", "almanca video ac", "almanca video", "almanca youtube",
        "videoyla almanca", "video ile almanca", "videodan almanca", "videoyla çalış", "videoyla calis",
        "german video", "easy german"
    ]
    if any(k in text_lower for k in german_youtube_triggers):
        res = await german_tutor.start_german_youtube_session(user_text)
        return res, ""

    # German Review Mode
    german_review_triggers = [
        "eski kelimeleri tekrar", "öğrendiklerimi tekrar", "ogrendiklerimi tekrar",
        "daha önce öğrendiklerimi", "almanca tekrar", "review german", "review words", "review vocabulary"
    ]
    if any(k in text_lower for k in german_review_triggers):
        res = await german_tutor.start_review_session(user_text)
        return res, ""

    german_study_triggers = [
        "almanca çalış", "almanca calis", "almanca pratik", "almanca kelime", "almanca ders",
        "almanca öğret", "almanca ogret", "practice german", "teach me german", "german lesson",
        "deutsch lernen", "almanca sor"
    ]
    if any(k in text_lower for k in german_study_triggers):
        res = await german_tutor.german_practice_session(user_text)
        return res, ""

    # Daily Open-Source GitHub Project Scout & Learning Roadmap
    github_scout_triggers = [
        "proje fikri", "github projesi", "ne kodlasam", "günün projesi", "proje öner",
        "github fikri", "açık kaynak proje", "project idea", "github scout", "yeni proje",
        "günün github projesi", "proje fikirleri", "proje fikr", "kendimi geliştirebileceğim proje",
        "açık kaynaklı proje", "açık kaynak proje fikirleri", "github proje fikirleri"
    ]
    if any(k in text_lower for k in github_scout_triggers) and not any(k in text_lower for k in ["kod yaz", "script yaz", "kodu çalıştır"]):
        idea_data = await github_scout.get_daily_project_idea()
        import asyncio
        asyncio.create_task(github_scout.send_daily_project_to_telegram())
        return idea_data["markdown"], ""

    # Open applications (Universal Mac launcher with smart fuzzy matching)
    APP_ALIASES = {
        "antigravity": "Antigravity",
        "antigravitvi": "Antigravity",
        "antigraviti": "Antigravity",
        "anti gravity": "Antigravity",
        "vscode": "Visual Studio Code",
        "vs code": "Visual Studio Code",
        "visual studio code": "Visual Studio Code",
        "code": "Visual Studio Code",
        "cursor": "Cursor",
        "spotify": "Spotify",
        "chrome": "Google Chrome",
        "google chrome": "Google Chrome",
        "safari": "Safari",
        "terminal": "Terminal",
        "iterm": "iTerm",
        "iterm2": "iTerm",
        "telegram": "Telegram",
        "finder": "Finder",
        "notes": "Notes",
        "notlar": "Notes",
        "calculator": "Calculator",
        "hesap makinesi": "Calculator",
    }
    app_verbs = ["aç", "ac", "başlat", "baslat", "çalıştır", "calistir", "open", "launch", "start", "run"]
    has_app_verb = any(re.search(rf'\b{v}\b', text_lower) for v in app_verbs)
    matched_app = None
    for alias, formal_name in APP_ALIASES.items():
        if alias in text_lower:
            matched_app = formal_name
            break

    if matched_app and has_app_verb:
        ok, res_action = await tools.open_application(matched_app)
        clean_prompt = re.sub(rf'\b({matched_app.lower()}|antigravitvi|antigravity|vscode|vs code|spotify|chrome|safari|terminal)\b', '', text_lower)
        clean_prompt = re.sub(r'\b(aç|ac|başlat|baslat|open|launch|start|run|\'yi|\'i|\'ı|\'yu|\'yı)\b', '', clean_prompt).strip()
        remaining_words = [w for w in clean_prompt.split() if w not in ["ve", "and", "lütfen", "please", "bana", "hemen"]]
        
        if len(remaining_words) < 2:
            is_turkish = any(w in text_lower for w in ["aç", "ac", "başlat", "baslat", "lütfen", "bana"])
            reply = f"{matched_app} uygulamasını Mac'inizde başlattım efendim." if is_turkish else f"Launched {matched_app} on your Mac now, Sir."
            return reply, ""
        else:
            tool_context += f" [Action Performed: Successfully opened {matched_app} on Sir's Mac] "

    # Antigravity / Autonomous Coding Agent (Direct Response)
    # Catches requests to build/write/create/make any code, script, app, game, or python project
    code_actions = ["write", "build", "create", "make", "develop", "code", "generate", "engineer", "kod", "yaz", "yap", "geliştir"]
    code_targets = ["code", "script", "app", "application", "game", "program", "python", "bot", "tool", "oyun", "yazılım"]
    has_action = any(act in text_lower for act in code_actions)
    has_target = any(tgt in text_lower for tgt in code_targets)
    direct_code_phrases = ["write a", "build a", "build me", "create a", "create me", "make a", "code a", "kod yaz", "script yaz", "bana kod", "oyun yap", "oyun yaz"]
    
    is_coding_request = (has_action and has_target) or any(k in text_lower for k in direct_code_phrases)
    is_non_coding = any(k in text_lower for k in ["volume", "sound", "ses", "weather", "daddy's home", "playlist", "switch to"])
    
    if is_coding_request and not is_non_coding:
        res = await agentic_code_generator(user_text)
        return res, ""

    # AI Video / Shorts & Anime/Dizi Editor Agent (Direct Response)
    video_edit_triggers = [
        "anime editi", "dizi editi", "shorts yap", "shorts videosu", "shorts hazırla",
        "tiktok editi", "reels editi", "video edit", "anime short", "make an anime edit",
        "create a short", "create shorts", "generate short", "edit yap", "editi yap", "editini yap",
        "montaj yap", "video üret", "örnek edit", "örnek bir edit", "edit örneği", "örnek hazırla", "tiktok videosu",
        "editi", "edit", "montaj"
    ]
    if any(vt in text_lower for vt in video_edit_triggers) and not any(k in text_lower for k in ["kod", "code", "python", "git "]):
        from . import video_generator
        url_match = re.search(r'(https?://[^\s]+)', user_text)
        if url_match:
            target = url_match.group(1).strip()
        else:
            target = re.sub(
                r'\b(jarvis|bana|lütfen|please|make|create|generate|yap|uyap|hazırla|editi|editini|edit|shorts|tiktok|reels|videosu|video|bir|tane|anime|animew|animesi|animesinin|dizi|dizisi|dizisinin|montaj|montajı|üret|örnek|örneği)\b',
                '', text_lower
            ).strip()
            if not target:
                target = "Peaky Blinders Thomas Shelby"
        res = await video_generator.create_anime_or_series_short(target)
        return res.get("message", "Shorts video created, Sir."), ""


    # YouTube & Media / Podcast (Direct Response - Instant execution)
    is_media = any(k in text_lower for k in ["youtube", "podcast", "huberman", "video", "şarkı", "song", "episode", "bölüm", "music", "müzik"])
    media_action = any(k in text_lower for k in ["play", "open", "launch", "start", "aç", "çal", "watch", "listen", "göster", "başlat"])
    explicit_youtube = any(phrase in text_lower for phrase in ["open youtube", "launch youtube", "start youtube", "youtube aç", "youtube'u aç", "youtube'da aç", "youtube play"])
    
    if (is_media and media_action) or ("huberman" in text_lower) or explicit_youtube:
        res = await tools.play_youtube(user_text)
        return res, ""
    
    play_match = re.search(r'(?:play|listen to|çal)\s+(.+)', text_lower)
    if play_match and not any(phrase in text_lower for phrase in ["daddy's home", "daddys home"]):
        target_song = play_match.group(1).strip()
        if target_song:
            res = await tools.play_youtube(target_song)
            return res, ""

    # Run Python Code / Script (CodeAct)
    if any(k in text_lower for k in ["run python", "run code", "execute code", "kod çalıştır"]):
        code_match = re.search(r'(?:code|kod|script)\s*:\s*(.+)', user_text, re.DOTALL)
        code_to_run = code_match.group(1) if code_match else "print('Hello from Jarvis CodeAct!')"
        res = await tools.execute_python_code(code_to_run)
        return res, ""

    # Mac volume
    vol_match = re.search(r'(?:sesi|sesini|volume)\s*(?:yüzde|percent)?\s*(\d+)', text_lower)
    if vol_match:
        vol = int(vol_match.group(1))
        res = await tools.set_mac_volume(vol)
        tool_context += f" [System action: {res}] "
    elif "sesi kıs" in text_lower or "sesi kapat" in text_lower or "mute" in text_lower:
        res = await tools.set_mac_volume(0)
        tool_context += f" [System action: {res}] "

    # Battery & system status
    if any(w in text_lower for w in ["şarj", "pil", "battery", "sistem durumu", "system status"]):
        status = await tools.get_system_status()
        tool_context += f" [System Info: {status}] "

    # Weather
    if any(w in text_lower for w in ["hava", "hava durumu", "weather", "kaç derece", "temperature"]):
        city = "Istanbul"
        for candidate in ["ankara", "izmir", "istanbul", "bursa", "antalya", "london", "new york", "berlin"]:
            if candidate in text_lower:
                city = candidate.capitalize()
                break
        w_info = await tools.get_weather(city)
        tool_context += f" [Weather Info: {w_info}] "

    return None, tool_context

def clean_for_speech(text: str) -> str:
    """Removes markdown and characters that shouldn't be read out loud."""
    # Remove markdown bold/italics
    text = re.sub(r'[*_#`~]', '', text)
    # Remove URLs
    text = re.sub(r'https?://\S+', '', text)
    # Clean whitespace
    text = ' '.join(text.split())
    return text.strip()

async def ask_gemini(user_text: str, context_addon: str, allow_fallback: bool = True) -> str:
    api_key = config.get_gemini_key()
    if not api_key or api_key == "your_gemini_api_key_here":
        if allow_fallback and config.get_openai_key():
            return await ask_openai(user_text, context_addon, allow_fallback=False)
        return "Gemini API key is not configured, Sir. Please check your settings."

    prompt_with_context = user_text
    if context_addon:
        prompt_with_context += f"\n(Real-time context: {context_addon})"

    memory.add_user_message(prompt_with_context)

    # Order of models to attempt
    models_to_try = [
        os.getenv("GEMINI_MODEL", "gemini-flash-lite-latest"),
        "gemini-flash-lite-latest",
        "gemini-3.1-flash-lite"
    ]
    models_to_try = list(dict.fromkeys(models_to_try))

    headers = {
        "Content-Type": "application/json",
        "X-goog-api-key": api_key
    }

    payload = {
        "system_instruction": {
            "parts": [{"text": SYSTEM_PROMPT + "\nIMPORTANT: Always complete your sentences fully. Never stop mid-word or mid-sentence."}]
        },
        "contents": memory.get_gemini_contents(),
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 1000
        }
    }

    for model_name in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"
        try:
            async with httpx.AsyncClient(timeout=6.0) as client:
                resp = await client.post(url, headers=headers, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    candidate = data.get("candidates", [{}])[0]
                    text = candidate.get("content", {}).get("parts", [{}])[0].get("text", "")
                    cleaned = clean_for_speech(text)
                    memory.add_assistant_message(cleaned)
                    return cleaned
                elif resp.status_code == 429:
                    print(f"⚠️ [GEMINI 429 on {model_name}]: Rate limit encountered, checking alternative model...")
                    continue
                elif resp.status_code in [500, 503]:
                    print(f"⚠️ [GEMINI {resp.status_code} on {model_name}]: Retrying alternative model...")
                    continue
                else:
                    print(f"❌ [GEMINI API ERROR {resp.status_code}]: {resp.text}")
        except Exception as e:
            print(f"❌ [GEMINI CONNECTION ERROR on {model_name}]: {e}")

    # If all Gemini attempts were exhausted, seamlessly fall back to OpenAI
    if allow_fallback:
        openai_key = config.get_openai_key()
        if openai_key and openai_key != "your_openai_api_key_here":
            print("🔄 [AUTO FALLBACK]: Gemini quota reached. Seamlessly routing query to ChatGPT...")
            return await ask_openai(user_text, context_addon, allow_fallback=False)

    return "Google's neural rate limit was briefly reached, Sir. Please give it a few seconds and ask again."

async def ask_openai(user_text: str, context_addon: str, allow_fallback: bool = True) -> str:
    api_key = config.get_openai_key()
    if not api_key or api_key == "your_openai_api_key_here":
        if allow_fallback and config.get_gemini_key():
            return await ask_gemini(user_text, context_addon, allow_fallback=False)
        return "OpenAI API key is not configured, Sir."

    prompt_with_context = user_text
    if context_addon:
        prompt_with_context += f"\n(Real-time context: {context_addon})"

    memory.add_user_message(prompt_with_context)

    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": config.OPENAI_MODEL,
        "messages": memory.get_messages_openai(),
        "max_tokens": 250,
        "temperature": 0.7
    }

    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                text = data["choices"][0]["message"]["content"]
                cleaned = clean_for_speech(text)
                memory.add_assistant_message(cleaned)
                return cleaned
            else:
                print(f"❌ [OPENAI API ERROR {resp.status_code}]: {resp.text}")
                if allow_fallback:
                    print("🔄 [AUTO FALLBACK]: OpenAI returned error/quota limit. Seamlessly routing to Gemini...")
                    return await ask_gemini(user_text, context_addon, allow_fallback=False)
                return f"OpenAI service returned error code {resp.status_code}, Sir."
    except Exception as e:
        print(f"❌ [OPENAI CONNECTION ERROR]: {e}")
        if allow_fallback:
            print("🔄 [AUTO FALLBACK]: OpenAI connection failed. Seamlessly routing to Gemini...")
            return await ask_gemini(user_text, context_addon, allow_fallback=False)
        return f"An OpenAI connection error occurred, Sir: {str(e)}"

async def ask_ollama(user_text: str, context_addon: str) -> str:
    prompt_with_context = user_text
    if context_addon:
        prompt_with_context += f"\n(Real-time context: {context_addon})"

    memory.add_user_message(prompt_with_context)

    url = f"{config.OLLAMA_HOST}/api/chat"
    payload = {
        "model": config.OLLAMA_MODEL,
        "messages": memory.get_messages_openai(),
        "stream": False
    }

    try:
        async with httpx.AsyncClient(timeout=25.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                text = data["message"]["content"]
                cleaned = clean_for_speech(text)
                memory.add_assistant_message(cleaned)
                return cleaned
            else:
                return "Ollama is unresponsive, Sir. Please ensure the local service is running."
    except Exception as e:
        return f"Ollama connection error, Sir: {str(e)}"

async def process_user_query(query: str) -> str:
    """Main entry point to query the brain."""
    # Check if currently active in a German language tutoring session
    if german_tutor.is_in_german_session():
        lower_q = query.lower().strip()
        finish_words = ["stop", "finish", "close", "quit", "exit", "enough", "tamam", "yeter", "kapat", "durdur", "bitir"]
        if any(fw in lower_q for fw in finish_words) and len(lower_q) < 30:
            german_tutor.set_german_session(False)
            reply = "Wunderbar session today, Sir. German tutoring is closed and your notes are saved. What else may I assist you with?"
            memory.add_user_message(query)
            memory.add_assistant_message(reply)
            return reply
        # Route directly to German tutor
        tutor_reply = await german_tutor.german_practice_session(query)
        memory.add_user_message(query)
        memory.add_assistant_message(tutor_reply)
        return tutor_reply

    direct_response, context_addon = await execute_potential_tools(query)
    if direct_response:
        memory.add_user_message(query)
        memory.add_assistant_message(direct_response)
        return direct_response

    provider = config.get_ai_provider()

    if provider == "openai":
        return await ask_openai(query, context_addon)
    elif provider == "ollama":
        return await ask_ollama(query, context_addon)
    else:
        # Default to Gemini
        return await ask_gemini(query, context_addon)

