# 🚀 Echo Dot & AI Jarvis Setup Guide (Zero-Cost / Subscription-Free)

[![Türkçe Kurulum Rehberi](https://img.shields.io/badge/Rehber-T%C3%BCrk%C3%A7e_Versiyon-red.svg)](KURULUM_REHBERI.md)
[![AI Customization Guide](https://img.shields.io/badge/Guide-AI_Customization-blue.svg)](AI_CUSTOMIZATION_GUIDE.md)

This step-by-step guide explains how to turn any **Amazon Echo Dot (Gen 2, 3, 4, or 5)** into a real, LLM-powered **J.A.R.V.I.S.** assistant at **zero cost** (without paying for Amazon Music, Audible, or subscription traps).

---

## 💡 Why Zero Cost?

Amazon Echo devices typically prompt users to subscribe to Amazon Music or buy Audible books. However, Amazon provides the **Alexa Developer Console** completely **FREE** so developers can build custom skills.

By running the Echo Dot in **Development Mode**:
1. When you say *"Alexa, open Jarvis"*, all standard Amazon advertising and commercial prompts are bypassed.
2. The Echo Dot acts purely as a high-sensitivity microphone array and speaker; it transcribes your speech and forwards it to your local Python backend.
3. Your local or cloud AI brain (Google Gemini, OpenAI, or local Ollama) processes the query, performs actions on your computer, and Echo Dot speaks the answer aloud.

---

## 🛠️ STEP 1: Backend Setup on Your Computer

### 1.1. Install Dependencies
Open your terminal in the project directory and install the requirements:
```bash
pip install -r requirements.txt
```

### 1.2. Configure Environment Variables
Copy the `.env.example` file to `.env`:
```bash
cp .env.example .env
```

Open `.env` in any text editor:
- **Google Gemini (Recommended — Ultra Fast & Free Tier):**
  - Go to [Google AI Studio](https://aistudio.google.com/) and grab a free API key.
  - Set in `.env`:
    ```env
    AI_PROVIDER=gemini
    GEMINI_API_KEY=your_gemini_api_key_here
    GEMINI_MODEL=gemini-2.5-flash
    ```
- *(Alternative)* For OpenAI, set `AI_PROVIDER=openai` and provide `OPENAI_API_KEY`.
- *(Alternative)* For 100% offline local AI, set `AI_PROVIDER=ollama`.

### 1.3. Start the Jarvis Backend
```bash
python3 run.py
```
You should see Jarvis running on `http://localhost:8000`.

---

## 🌐 STEP 2: Expose Your Backend to Alexa (Public HTTPS Tunnel)

Amazon Alexa requires a secure HTTPS endpoint to communicate with your local machine.

### Option A: Cloudflare Tunnel (Free & No Account Needed)
If you have `cloudflared` installed:
```bash
cloudflared tunnel --url http://localhost:8000
```
Copy the generated `https://*.trycloudflare.com` URL.

### Option B: ngrok (Free & Stable)
1. Sign up for a free account at [ngrok.com](https://ngrok.com).
2. Start the tunnel:
   ```bash
   ngrok http 8000
   ```
3. Copy the generated `https://*.ngrok-free.app` forwarding address.

---

## 🎙️ STEP 3: Create the Alexa Custom Skill (5 Minutes)

1. Go to the [Amazon Alexa Developer Console](https://developer.amazon.com/alexa/console/ask) and log in with the **same Amazon account** that is registered on your Echo Dot.
2. Click **Create Skill**:
   - **Skill Name:** `Jarvis`
   - **Primary Locale:** `English (US)`
   - **Model:** `Custom`
   - **Hosting:** `Provision your own`
   - Click **Create Skill**.
3. In the left sidebar, click **Interaction Model** $\rightarrow$ **JSON Editor**.
4. Open [`alexa/interaction_model_en.json`](alexa/interaction_model_en.json) from this repository, copy its entire contents, paste it into the JSON Editor, and click **Save Model** then **Build Model** (takes ~30 seconds).
5. In the left sidebar, click **Endpoint**:
   - Select **HTTPS**.
   - Under **Default Region**, paste your tunnel URL with `/alexa` appended:
     ```
     https://your-tunnel-url.ngrok-free.app/alexa
     ```
   - In the SSL dropdown, choose:
     `My development endpoint is a sub-domain of a domain that has a wildcard certificate from a certificate authority`.
   - Click **Save Endpoints**.

---

## 🗣️ STEP 4: Test with Your Echo Dot

1. Make sure your computer is running `python3 run.py` and your tunnel is active.
2. Stand in front of your Echo Dot and say:
   > *"Alexa, open Jarvis"*
3. Echo Dot will chime and reply:
   > *"Jarvis online, Sir. How may I assist you?"*
4. You can now talk naturally:
   - *"Set volume to 50 percent"*
   - *"What's the weather like?"*
   - *"Open Spotify"*
   - *"Tell me a tech joke"*
