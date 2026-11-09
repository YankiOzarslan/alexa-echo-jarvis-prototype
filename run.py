import os
import sys
import shutil
from pathlib import Path

def setup_environment():
    root = Path(__file__).resolve().parent
    env_file = root / ".env"
    env_example = root / ".env.example"

    if not env_file.exists() and env_example.exists():
        shutil.copy(env_example, env_file)
        print("💡 [BİLGİ] .env dosyası oluşturuldu. Lütfen içine Gemini veya OpenAI API anahtarınızı ekleyin.")

def main():
    setup_environment()
    try:
        import uvicorn
        from backend.config import PORT
    except ImportError:
        print("❌ Gerekli kütüphaneler eksik! Lütfen terminalde şu komutu çalıştırın:")
        print("   pip install -r requirements.txt")
        sys.exit(1)

    print("=" * 60)
    print("🤖 J.A.R.V.I.S. ALEXA BACKEND BAŞLATILIYOR...")
    print(f"📡 Yerel Port: http://localhost:{PORT}")
    print(f"🔗 Alexa Webhook: http://localhost:{PORT}/alexa")
    print(f"🧪 Doğrudan Test Endpoint'i: http://localhost:{PORT}/test")
    print("=" * 60)

    uvicorn.run("backend.server:app", host="0.0.0.0", port=PORT, reload=True)

if __name__ == "__main__":
    main()
