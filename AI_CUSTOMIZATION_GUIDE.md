# 🤖 AI-Powered Customization Guide for J.A.R.V.I.S.
> *How to adapt, extend, and rewrite this codebase using AI assistants (Gemini, Claude, Cursor, ChatGPT, Antigravity, Copilot)*

[![Türkçe Rehber](https://img.shields.io/badge/Rehber-T%C3%BCrk%C3%A7e_Versiyon-red.svg)](YAPAY_ZEKA_OZELLESTIRME_REHBERI.md)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 🎯 Purpose of This Guide

This codebase is intentionally architected to be **AI-agent friendly**:
- Clean separation of concerns (`brain.py`, `tools.py`, `server.py`, `config.py`).
- Deterministic regex and function calling dispatchers.
- Zero complex boilerplate frameworks or bloated middleware.

Whether you are using **Google Gemini**, **Anthropic Claude**, **Cursor IDE**, **ChatGPT**, or **Google Antigravity**, you can feed this repository to your AI assistant and instruct it to customize Jarvis for your exact hardware, OS, and personal workflow.

---

## 🗺️ Codebase Map for AI Models

When asking an AI model to edit code, you don't need to feed it all files at once. Give it only the relevant files to preserve context window and avoid hallucinations:

| If You Want To Modify... | Files to Provide to the AI | What's Inside |
| :--- | :--- | :--- |
| **Persona, Tone, Voice & Name** | [`backend/config.py`](backend/config.py)<br>[`backend/brain.py`](backend/brain.py) | System prompt, user name, personality, fallback heuristics. |
| **System Automations (Mac/Win/Linux)** | [`backend/tools.py`](backend/tools.py)<br>[`backend/brain.py`](backend/brain.py) | AppleScripts, OS commands, volume, app launcher, weather. |
| **Smart Home & IoT (Home Assistant)** | [`backend/tools.py`](backend/tools.py)<br>[`backend/config.py`](backend/config.py) | REST API callers, webhooks, smart light toggles. |
| **AI Brain & Providers (Claude, DeepSeek)** | [`backend/brain.py`](backend/brain.py)<br>[`backend/config.py`](backend/config.py) | Gemini, OpenAI, Ollama handlers and router functions. |
| **Telegram Remote Bot** | [`backend/telegram_bot.py`](backend/telegram_bot.py) | Voice note transcription, chat polling, auto media push. |
| **Alexa Voice Commands & Invocations** | [`alexa/interaction_model_en.json`](alexa/interaction_model_en.json)<br>[`backend/server.py`](backend/server.py) | Alexa skill slots, sample utterances, intent endpoints. |
| **TikTok/Shorts Video Generator** | [`backend/video_generator.py`](backend/video_generator.py) | FFmpeg pipeline, subtitles, aspect ratio, audio mixing. |

---

## 📋 Ready-to-Copy AI Prompts (Copy & Paste)

You can copy and paste the following prompt templates directly into **Gemini**, **Claude**, **ChatGPT**, or **Cursor Composer**.

---

### 🎨 Template 1: Change Persona, Wake Name & Voice Tone

```markdown
I have an open-source AI assistant called J.A.R.V.I.S. that connects Amazon Echo Dot to a Python backend.
Attached are `backend/config.py` and `backend/brain.py`.

Please modify them to:
1. Change Jarvis's persona from a formal British butler to: [INSERT YOUR DESIRED PERSONA, e.g., "a witty, sarcastic Cyberpunk AI named FRIDAY / a friendly study assistant"].
2. Change the default user address from "Sir" to "[YOUR NAME]".
3. Keep answers concise (< 3 sentences) because Amazon Echo speaks these responses aloud and long answers feel sluggish over voice.
4. Update the system prompt in `config.py` and ensure `brain.py` reflects this tone across both Gemini and OpenAI fallback handlers.
```

---

### 💻 Template 2: Adapt for Windows or Linux (Replacing macOS AppleScript)

```markdown
Currently, `backend/tools.py` uses macOS AppleScript (`osascript`) for volume control and launching applications (`open -a`).
I am running this project on [Windows 11 / Ubuntu Linux].

Attached is `backend/tools.py`.
Please update the following functions to work natively on my OS:
1. `set_volume(level)`: Use [pycaw or ctypes for Windows / amixer or pactl for Linux].
2. `get_battery()`: Use [psutil to read battery status cross-platform].
3. `open_app(app_name)`: Use native process launch (`os.startfile` or `subprocess.Popen`).
4. Ensure all changes handle errors gracefully without crashing the FastAPI server.
```

---

### 🏠 Template 3: Add Home Assistant / Smart Home Light Controls

```markdown
I want my Echo Dot Jarvis to control my Smart Home devices via Home Assistant REST API.
Attached are `backend/config.py`, `backend/tools.py`, and `backend/brain.py`.

Please:
1. In `config.py`, add environment variables:
   - `HASS_URL = os.getenv("HASS_URL", "http://homeassistant.local:8123")`
   - `HASS_TOKEN = os.getenv("HASS_TOKEN", "")`
2. In `tools.py`, create a function `toggle_light(entity_id, state="toggle")` that sends a POST request to Home Assistant's `/api/services/light/toggle` with Authorization Bearer header.
3. In `brain.py`, add tool-calling or pattern-matching so when the user says:
   - "Turn off the bedroom lights"
   - "Toggle desk lamp"
   Jarvis executes `toggle_light` and replies with a smooth voice confirmation.
```

---

### 🧠 Template 4: Add Anthropic Claude 3.5 Sonnet or DeepSeek V3

```markdown
I want to add [Anthropic Claude 3.5 Sonnet / DeepSeek V3] as a supported AI provider in J.A.R.V.I.S.
Attached are `backend/config.py` and `backend/brain.py`.

Please:
1. In `config.py`, add config parameters for the new provider API Key and Model Name.
2. In `brain.py`, implement an asynchronous handler function `ask_claude(prompt)` or `ask_deepseek(prompt)` using the standard SDK or httpx.
3. Integrate it into `ask_jarvis(prompt)` routing logic so I can set `AI_PROVIDER=claude` or `AI_PROVIDER=deepseek` in my `.env` file.
4. Keep the multi-model fallback intact (if the primary provider encounters a rate limit, fallback to Gemini Flash).
```

---

### 📱 Template 5: Add Spotify Web API / Music Playback

```markdown
I want Jarvis to control Spotify playback on my Mac/Echo using the Spotify Web API or spotipy.
Attached are `backend/tools.py` and `backend/brain.py`.

Please:
1. Write a tool function `play_spotify_track(query)` that searches for a track or playlist and triggers playback.
2. In `brain.py`, wire voice intents like "Jarvis, play Synthwave" or "Jarvis, pause music" to invoke this tool.
3. Keep voice replies short and acknowledge the command instantly.
```

---

### 🎙️ Template 6: Change Alexa Wake Word & Invocation Name

```markdown
Currently, the Alexa custom skill is invoked by saying "Alexa, open Jarvis".
Attached is `alexa/interaction_model_en.json`.

Please:
1. Change the skill invocation name from "jarvis" to "[YOUR CUSTOM NAME, e.g., 'friday' or 'computer' or 'my assistant']".
2. Add new sample utterances for commands I use frequently:
   - "[your custom voice commands]"
3. Ensure the JSON schema remains fully compatible with Amazon Alexa Developer Console V2.
```

---

## ⚠️ 4 Golden Rules for AI Coding Assistants

When letting an AI modify this codebase, instruct it to observe these constraints:

1. **Voice Latency Ceiling (< 3000ms):**
   Amazon Alexa will timeout with an error chime if the webhook response takes longer than ~8 seconds. Keep LLM token limits moderate (`max_tokens=250`), use fast models (`gemini-flash-lite-latest` or `gpt-4o-mini`), and avoid synchronous network calls.
2. **Non-Blocking Background Tasks:**
   If a task takes longer than 3 seconds (like rendering a 60-second TikTok video with FFmpeg or scraping GitHub), run it using `asyncio.create_task()` or background threads so Alexa gets an immediate voice response: *"I've started rendering your video in the background, Sir."*
3. **No Hardcoded Secrets:**
   All API keys, tokens, and webhooks must be loaded from `os.getenv()` in `backend/config.py`. Never let the AI write raw tokens into `.py` files.
4. **Resilient Fallbacks:**
   Voice assistants are used hands-free. If a third-party API fails, catch exceptions and return a witty spoken fallback rather than throwing a 500 internal server error.
