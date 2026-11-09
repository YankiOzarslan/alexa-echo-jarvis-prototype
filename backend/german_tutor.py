import os
import re
import json
import datetime
import asyncio
from pathlib import Path
import httpx
from . import config

NOTES_PATH = Path(__file__).resolve().parent.parent / "german_learning_notes.md"
PROGRESS_PATH = Path(__file__).resolve().parent.parent / "german_progress.json"

_IN_GERMAN_SESSION = False
_GERMAN_HISTORY = []
_REVIEW_MODE = False
_SPEECH_RATE = "92%"
_LAST_TARGET_GERMAN = ""
_ATTEMPT_COUNT = 0

def is_in_german_session() -> bool:
    global _IN_GERMAN_SESSION
    return _IN_GERMAN_SESSION

def set_german_session(active: bool):
    global _IN_GERMAN_SESSION, _GERMAN_HISTORY, _REVIEW_MODE, _SPEECH_RATE, _ATTEMPT_COUNT
    _IN_GERMAN_SESSION = active
    if not active:
        _GERMAN_HISTORY.clear()
        _REVIEW_MODE = False
        _SPEECH_RATE = "92%"
        _ATTEMPT_COUNT = 0

def get_last_german_phrase() -> str:
    global _LAST_TARGET_GERMAN
    return _LAST_TARGET_GERMAN

def set_last_german_phrase(phrase: str):
    global _LAST_TARGET_GERMAN
    _LAST_TARGET_GERMAN = phrase

def is_review_mode() -> bool:
    global _REVIEW_MODE
    return _REVIEW_MODE

def set_review_mode(active: bool):
    global _REVIEW_MODE
    _REVIEW_MODE = active

def get_speech_rate() -> str:
    global _SPEECH_RATE
    return _SPEECH_RATE

def set_speech_rate(rate: str):
    global _SPEECH_RATE
    _SPEECH_RATE = rate

def load_progress() -> dict:
    """Loads persistent progress data."""
    if PROGRESS_PATH.exists():
        try:
            with open(PROGRESS_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading german_progress.json: {e}")
    return {
        "user_name": config.JARVIS_USER_NAME,
        "last_session_date": str(datetime.date.today()),
        "mode": "new_learning",
        "learned_words": {},
        "completed_scenarios": []
    }

def save_progress(data: dict):
    """Saves persistent progress data."""
    try:
        with open(PROGRESS_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving german_progress.json: {e}")

def get_mastered_words() -> list:
    prog = load_progress()
    return list(prog.get("learned_words", {}).keys())

def record_learned_word(topic: str, vocabulary: str, note: str):
    """Updates both JSON progress database and markdown notes."""
    clean_topic = re.sub(r'</?[^>]+>', '', topic).strip()
    clean_vocab = re.sub(r'</?[^>]+>', '', vocabulary).strip()
    clean_note = re.sub(r'</?[^>]+>', '', note).strip()

    # 1. Update JSON database
    prog = load_progress()
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    prog["last_session_date"] = today_str
    words_dict = prog.setdefault("learned_words", {})
    
    # Extract phrase and meaning e.g. "Guten Morgen (Good morning)"
    items = [v.strip() for v in clean_vocab.split(",") if v.strip()]
    for item in items:
        m = re.match(r'^(.*?)\s*\((.*?)\)$', item)
        if m:
            w = m.group(1).strip()
            mean = m.group(2).strip()
        else:
            w = item
            mean = clean_note
        if w:
            if w in words_dict:
                words_dict[w]["review_count"] = words_dict[w].get("review_count", 0) + 1
            else:
                words_dict[w] = {
                    "meaning": mean,
                    "topic": clean_topic,
                    "date": today_str,
                    "review_count": 1
                }
    save_progress(prog)

    # 2. Update Markdown Notebook
    if not NOTES_PATH.exists():
        return

    new_row = f"| {today_str} | {clean_topic} | {clean_vocab} | {clean_note} |\n"
    with open(NOTES_PATH, "r", encoding="utf-8") as f:
        doc = f.read()

    table_marker = "|-------|---------------|-------------------------------|-----------------|\n"
    if table_marker in doc:
        doc = doc.replace(table_marker, table_marker + new_row)
    else:
        doc += f"\n{new_row}"

    if items and "## 🧠 Kelime Haznesi" in doc:
        vocab_text = "\n".join([f"* **{v}**" for v in items]) + "\n"
        doc = doc.replace("## 🧠 Kelime Haznesi (Vocabulary Bank)\n", f"## 🧠 Kelime Haznesi (Vocabulary Bank)\n{vocab_text}")

    with open(NOTES_PATH, "w", encoding="utf-8") as f:
        f.write(doc)

def enhance_german_ssml(text: str, rate: str = None) -> str:
    """Enhances German SSML so Echo Dot uses Amazon Polly's Vicki voice with articulate rate."""
    current_rate = rate or get_speech_rate()
    def _wrap_vicki(match):
        inner = match.group(1).strip()
        # Clean any nested tags
        inner = re.sub(r'</?(?:voice|prosody|lang)[^>]*>', '', inner).strip()
        return f'<voice name="Vicki"><lang xml:lang="de-DE"><prosody rate="{current_rate}">{inner}</prosody></lang></voice>'

    # If voice is already present, ensure prosody
    text = re.sub(r'<voice[^>]*>\s*<lang[^>]*>(.*?)</lang>\s*</voice>', _wrap_vicki, text, flags=re.DOTALL)

    # Replace standalone <lang xml:lang="de-DE">
    text = re.sub(r'(?<!<voice name="Vicki">)<lang xml:lang="de-DE">(.*?)</lang>', _wrap_vicki, text, flags=re.DOTALL)

    # If current rate is slower (e.g. 70%), update any hardcoded 92% rate
    if current_rate != "92%":
        text = re.sub(r'rate="92%"', f'rate="{current_rate}"', text)
        # Slow down English speech too
        if not text.startswith("<prosody"):
            text = f'<prosody rate="80%">{text}</prosody>'
    return text

async def open_german_notes() -> str:
    """Opens the German learning notes in VS Code or default viewer."""
    if not NOTES_PATH.exists():
        return "Almanca not defteriniz henüz bulunamadı efendim."
    try:
        proc = await asyncio.create_subprocess_exec("code", str(NOTES_PATH))
        await proc.communicate()
        return "Almanca not defterinizi VS Code üzerinde açtım efendim."
    except Exception:
        await asyncio.create_subprocess_exec("open", str(NOTES_PATH))
        return "Almanca not defterinizi ekranda açtım efendim."

async def start_german_youtube_session(user_request: str) -> str:
    """Finds an authentic German daily conversation YouTube video, opens it on Mac, and teaches practical usage."""
    from . import tools
    req_lower = user_request.lower()
    
    if any(k in req_lower for k in ["spor", "gym", "fitness", "antrenman"]):
        query = "Easy German at the gym fitness German conversation"
        topic = "Gym & Fitness"
    elif any(k in req_lower for k in ["restoran", "yemek", "cafe", "kafe", "sipariş", "kahve"]):
        query = "Easy German ordering food cafe bakery"
        topic = "Restaurant & Cafe"
    elif any(k in req_lower for k in ["market", "alışveriş", "supermarket"]):
        query = "Easy German supermarket grocery shopping"
        topic = "Supermarket Shopping"
    elif any(k in req_lower for k in ["havaalanı", "seyahat", "travel", "otel", "hotel"]):
        query = "Easy German travel airport hotel"
        topic = "Travel & Hotel"
    else:
        query = "Easy German street interview daily routine"
        topic = "Everyday Street Conversation"

    # Launch video on Mac screen
    await tools.play_youtube(query)
    set_german_session(True)

    starter = f"[INTERNAL_PROMPT] Sir requested to practice German with a YouTube video. You just opened an authentic Easy German video about '{topic}' on Sir's Mac screen. Announce that the video is now playing on the Mac, and immediately teach the first high-yield phrase from this scenario using <voice name='Vicki'><lang xml:lang='de-DE'><prosody rate='92%'>PHRASE</prosody></lang></voice>."
    return await german_practice_session(starter)

async def start_review_session(user_text: str = "") -> str:
    """Pulls past learned vocabulary from progress file and quizzes Sir."""
    set_review_mode(True)
    set_german_session(True)
    prog = load_progress()
    words = prog.get("learned_words", {})
    if not words:
        return "You haven't recorded any vocabulary in your notebook yet, Sir. Let us start with a fresh daily conversation lesson!"

    word_items = list(words.items())
    sample_text = ", ".join([f"{w} ({info.get('meaning', '')})" for w, info in word_items[-6:]])

    prompt = f"[INTERNAL_PROMPT] Sir entered Review Mode to practice past learned vocabulary. Here are words Sir has previously learned: {sample_text}. Warmly quiz Sir on one of these past words: say the German word with <voice name='Vicki'><lang xml:lang='de-DE'><prosody rate='92%'>WORD</prosody></lang></voice> and ask Sir what it means, or ask Sir how to say the English meaning in German."
    return await german_practice_session(prompt)

async def german_practice_session(user_text: str) -> str:
    """Specialized German tutor that teaches, quizzes, and auto-records progress."""
    global _IN_GERMAN_SESSION, _GERMAN_HISTORY, _REVIEW_MODE

    lower_u = user_text.lower().strip()

    # 1. Check if user wants to finish session
    finish_words = ["stop", "finish", "close", "quit", "exit", "enough", "tamam yeter", "yeterli", "almanca bitti", "almancayı kapat", "dersi bitir"]
    if any(fw in lower_u for fw in finish_words) and len(lower_u) < 30:
        set_german_session(False)
        return "Wunderbar work today, Sir. German tutoring session is closed, and your vocabulary notes are saved. What else may I assist you with?"

    # Check user commands only if not an internal prompt
    if not user_text.startswith("[INTERNAL_PROMPT]"):
        # 2. Check if user requested Review Mode
        review_triggers = ["eski kelimeleri tekrar", "öğrendiklerimi tekrar", "ogrendiklerimi tekrar", "daha önce öğrendiklerimi", "tekrar edelim", "review words", "review mode", "geçmiş kelimeler"]
        if any(rt in lower_u for rt in review_triggers):
            return await start_review_session(user_text)

        # 3. Check if user requested to switch from Review back to New Learning
        new_triggers = ["yeni kelime", "yeni konu", "continue", "devam et", "sıradaki", "yeni ders", "new lesson", "new words"]
        if any(nt in lower_u for nt in new_triggers):
            set_review_mode(False)

        # 4. Check if user requested a YouTube video lesson
        if any(yt in lower_u for yt in ["video aç", "youtube", "videoyla", "video ile", "videodan"]) and "almanca" in lower_u:
            return await start_german_youtube_session(user_text)

        # 5. Check if user requested slower / faster speech
        slower_triggers = ["slower", "slow down", "speak slower", "more slowly", "daha yavaş", "yavaşlat", "yavaş anlat", "yavaş söyle", "yavaş", "slow", "slowly", "yavas"]
        faster_triggers = ["faster", "faster please", "daha hızlı", "hızlan", "normal speed", "normal hız", "normal"]
        if any(st in lower_u for st in slower_triggers):
            set_speech_rate("70%")
            if len(lower_u) < 30:
                user_text = "[INTERNAL_PROMPT] Sir requested: 'Explain and speak slower'. Please speak gently and slowly. Repeat the previous German phrase or concept extra slowly using <voice name='Vicki'><lang xml:lang='de-DE'><prosody rate='70%'>PHRASE</prosody></lang></voice>, break down each syllable clearly with short pauses, and guide Sir step-by-step."
        elif any(ft in lower_u for ft in faster_triggers):
            set_speech_rate("92%")

        # 6. Check if user asked to repeat the last sentence
        repeat_sentence_triggers = [
            "repeat the last sentence", "repeat last sentence", "repeat that sentence", "repeat that",
            "repeat the sentence", "say that again", "say it again", "can you repeat that", "can you repeat",
            "repeat please", "what was the sentence", "what was that", "what did you say",
            "son cümleyi tekrar et", "son cümleyi tekrar", "son cümleyi söyle", "bir daha söyle",
            "tekrar et", "cümleyi tekrar et", "tekrar söyler misin", "baştan al", "anlamadım tekrar et"
        ]
        if any(rst in lower_u for rst in repeat_sentence_triggers) and len(lower_u) < 45:
            target = get_last_german_phrase() or "Guten Tag, wie geht es dir?"
            rate = get_speech_rate()
            reply = (
                f"Certainly, Sir. The sentence was: "
                f"<voice name='Vicki'><lang xml:lang='de-DE'><prosody rate='{rate}'>{target}</prosody></lang></voice>. "
                f"Take your time and repeat after me."
            )
            return enhance_german_ssml(reply)

    set_german_session(True)

    mastered = get_mastered_words()
    mastered_sample = ", ".join(mastered[-15:]) if mastered else "None"

    if _REVIEW_MODE:
        mode_instruction = f"""CURRENT MODE: REVIEW MODE (Geri Dönüp Tekrar Etme).
Sir wants to review past learned words. Test Sir's memory on past vocabulary.
Recent past words: {mastered_sample}."""
    else:
        mode_instruction = f"""CURRENT MODE: NEW KNOWLEDGE (YENİ KONU / KELİMELER).
CRITICAL RULE: Sir has ALREADY learned these words: [{mastered_sample}].
STRICTLY DO NOT REPEAT THESE WORDS!
Teach Sir a brand NEW, practical everyday German phrase or dialogue from daily life (e.g. gym/fitness, cafe/restaurant, supermarket, travel, transportation, asking directions)."""

    rate = get_speech_rate()
    rate_guideline = f"""CRITICAL VOICE & PRONUNCIATION RULE:
Echo Dot uses an English voice by default. To trigger Amazon Polly's authentic native German neural voice 'Vicki' at speed rate '{rate}', you MUST wrap EVERY German word, phrase, greeting, or sentence inside:
<voice name="Vicki"><lang xml:lang="de-DE"><prosody rate="{rate}">GERMAN_PHRASE</prosody></lang></voice>
"""
    if rate == "70%":
        rate_guideline += """
PACE DIRECTIVE (SLOW EXPLANATION ACTIVE):
Sir explicitly requested you to speak and explain SLOWER ('yavaş anlat').
1. Keep your explanation calm, gentle, and slow.
2. Break the German phrase down syllable by syllable or word by word with pauses (e.g. 'Ist... die-ses... Ge-rät... frei?').
3. Explain each component clearly so Sir can easily absorb the pronunciation.
"""

    target_phrase = get_last_german_phrase()
    eval_guideline = ""
    if target_phrase and not user_text.startswith("[INTERNAL_PROMPT]"):
        eval_guideline = f"""
STRICT PRONUNCIATION & ACCURACY EVALUATION:
The active German target phrase is: '{target_phrase}'.
Sir's attempt/response: '{user_text}'.
- Critically evaluate Sir's pronunciation attempt or answer.
- If Sir mispronounced the phrase, skipped words, or made a clear mistake: DO NOT falsely say 'Ausgezeichnet' or declare it correct!
- Kindly point out the difference (e.g. 'Almost, Sir, but notice how the word ends...' or 'You said X, but the correct German is Y'), demonstrate the correct pronunciation with <voice name="Vicki"><lang xml:lang="de-DE"><prosody rate="75%">{target_phrase}</prosody></lang></voice>, and ask Sir to try repeating it again.
- Only confirm it as fully correct if Sir's pronunciation or translation was genuinely accurate.
"""

    system_prompt = f"""You are J.A.R.V.I.S. serving as Sir's elite personal German Language Coach.
Your goal is to teach Sir practical German step-by-step with 100% authentic native German pronunciation.

{rate_guideline}

{mode_instruction}

{eval_guideline}

CONVERSATIONAL RULES:
1. Speak concisely (1 to 2 sentences max) so Sir can easily listen and answer via voice on Echo Dot.
2. If Sir's pronunciation was evaluated and accurate, warmly praise the result and advance.
3. AT THE VERY END OF YOUR RESPONSE, always append the hidden tracking tag:
[LOG_GERMAN: Topic | german_phrase (English meaning) | Coach note]
"""

    _GERMAN_HISTORY.append({"role": "user", "parts": [{"text": user_text}]})
    if len(_GERMAN_HISTORY) > 10:
        _GERMAN_HISTORY = _GERMAN_HISTORY[-10:]

    raw = None

    # 1. Try Gemini
    api_key = config.get_gemini_key()
    if api_key and api_key != "your_gemini_api_key_here":
        model_name = os.getenv("GEMINI_MODEL", "gemini-flash-lite-latest")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"
        headers = {"Content-Type": "application/json", "X-goog-api-key": api_key}
        payload = {
            "system_instruction": {"parts": [{"text": system_prompt}]},
            "contents": _GERMAN_HISTORY,
            "generationConfig": {"temperature": 0.6, "maxOutputTokens": 400}
        }
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.post(url, headers=headers, json=payload)
                if resp.status_code == 200:
                    raw = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            print(f"German tutor Gemini error: {e}")

    # 2. Fallback to OpenAI if Gemini fails or empty
    if not raw:
        openai_key = config.get_openai_key()
        if openai_key and openai_key != "your_openai_api_key_here":
            try:
                url = f"{config.OPENAI_BASE_URL}/chat/completions"
                headers = {"Authorization": f"Bearer {openai_key}", "Content-Type": "application/json"}
                messages = [{"role": "system", "content": system_prompt}]
                for h in _GERMAN_HISTORY:
                    r = "user" if h["role"] == "user" else "assistant"
                    t = h["parts"][0]["text"]
                    messages.append({"role": r, "content": t})
                payload = {"model": config.OPENAI_MODEL, "messages": messages, "max_tokens": 300, "temperature": 0.6}
                async with httpx.AsyncClient(timeout=8.0) as client:
                    resp = await client.post(url, headers=headers, json=payload)
                    if resp.status_code == 200:
                        raw = resp.json()["choices"][0]["message"]["content"]
            except Exception as e:
                print(f"German tutor OpenAI error: {e}")

    if raw:
        match = re.search(r'\[LOG_GERMAN:\s*([^\|]+)\|([^\|]+)\|([^\]]+)\]', raw)
        if match:
            topic = match.group(1).strip()
            vocab = match.group(2).strip()
            note = match.group(3).strip()
            record_learned_word(topic, vocab, note)
            clean_reply = re.sub(r'\[LOG_GERMAN:[^\]]+\]', '', raw).strip()
        else:
            clean_reply = raw.strip()

        # Enhance SSML tags with Vicki voice and appropriate prosody
        enhanced_reply = enhance_german_ssml(clean_reply)

        # Extract German phrase to save as target for future evaluation
        match_phrase = re.search(r'<lang xml:lang="de-DE">(?:<prosody[^>]*>)?(.*?)(?:</prosody>)?</lang>', enhanced_reply)
        if match_phrase:
            clean_p = re.sub(r'</?[^>]+>', '', match_phrase.group(1)).strip()
            if clean_p and len(clean_p) > 1:
                set_last_german_phrase(clean_p)
        elif match:
            m_vocab = re.match(r'^(.*?)\s*\(', vocab)
            clean_v = m_vocab.group(1).strip() if m_vocab else vocab.strip()
            set_last_german_phrase(clean_v)

        _GERMAN_HISTORY.append({"role": "model", "parts": [{"text": enhanced_reply}]})
        return enhanced_reply

    fallback_rate = get_speech_rate()
    fallback_reply = f'Wunderbar, Sir. Let us practice gym conversation. Repeat after me: <voice name="Vicki"><lang xml:lang="de-DE"><prosody rate="{fallback_rate}">Ist dieses Gerät frei?</prosody></lang></voice>.'
    set_last_german_phrase("Ist dieses Gerät frei?")
    return enhance_german_ssml(fallback_reply)

async def handle_fallback_attempt() -> str:
    """Handles oral repetition when speech phonetics were unclear to Alexa without falsely praising."""
    global _ATTEMPT_COUNT
    target = get_last_german_phrase() or "Guten Tag, wie geht es dir?"
    
    if _ATTEMPT_COUNT == 0:
        _ATTEMPT_COUNT = 1
        reply = (
            f"That was a good first attempt, Sir, but let us polish the pronunciation. "
            f"Listen carefully to how each sound is shaped: <voice name='Vicki'><lang xml:lang='de-DE'><prosody rate='75%'>{target}</prosody></lang></voice>. "
            f"Now let us try repeating it together once more: <voice name='Vicki'><lang xml:lang='de-DE'><prosody rate='70%'>{target}</prosody></lang></voice>."
        )
        return enhance_german_ssml(reply)
    else:
        _ATTEMPT_COUNT = 0
        prompt = (
            f"[INTERNAL_PROMPT] Sir attempted to pronounce '{target}' a second time. "
            f"Acknowledge Sir's practice effort realistically, confirm the English meaning clearly, and advance to the next practical phrase."
        )
        return await german_practice_session(prompt)
