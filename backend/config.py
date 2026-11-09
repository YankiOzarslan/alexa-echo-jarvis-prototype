import os
import re
from pathlib import Path
from dotenv import load_dotenv

# Load .env if present
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

def get_gemini_key() -> str:
    load_dotenv(dotenv_path=env_path, override=True)
    return os.getenv("GEMINI_API_KEY", "").strip()

def get_openai_key() -> str:
    load_dotenv(dotenv_path=env_path, override=True)
    return os.getenv("OPENAI_API_KEY", "").strip()

def get_telegram_token() -> str:
    load_dotenv(dotenv_path=env_path, override=True)
    return os.getenv("TELEGRAM_BOT_TOKEN", "").strip()

def get_telegram_chat_id() -> str:
    load_dotenv(dotenv_path=env_path, override=True)
    return os.getenv("TELEGRAM_ALLOWED_CHAT_ID", "").strip()

def save_telegram_chat_id(chat_id: str):
    cid = str(chat_id).strip()
    os.environ["TELEGRAM_ALLOWED_CHAT_ID"] = cid
    if env_path.exists():
        try:
            content = env_path.read_text(encoding="utf-8")
            if "TELEGRAM_ALLOWED_CHAT_ID=" in content:
                content = re.sub(r'TELEGRAM_ALLOWED_CHAT_ID=.*', f'TELEGRAM_ALLOWED_CHAT_ID={cid}', content)
            else:
                content += f"\nTELEGRAM_ALLOWED_CHAT_ID={cid}\n"
            env_path.write_text(content, encoding="utf-8")
        except Exception as e:
            pass

_CURRENT_PROVIDER = None

def get_ai_provider() -> str:
    global _CURRENT_PROVIDER
    if _CURRENT_PROVIDER:
        return _CURRENT_PROVIDER
    load_dotenv(dotenv_path=env_path, override=True)
    _CURRENT_PROVIDER = os.getenv("AI_PROVIDER", "gemini").lower()
    return _CURRENT_PROVIDER

def set_ai_provider(provider: str):
    global _CURRENT_PROVIDER
    _CURRENT_PROVIDER = provider.lower()
    os.environ["AI_PROVIDER"] = _CURRENT_PROVIDER

AI_PROVIDER = get_ai_provider()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-lite-latest")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3:latest")

JARVIS_USER_NAME = os.getenv("JARVIS_USER_NAME", "Sir")
JARVIS_LANGUAGE = os.getenv("JARVIS_LANGUAGE", "en")
PORT = int(os.getenv("PORT", "8000"))
