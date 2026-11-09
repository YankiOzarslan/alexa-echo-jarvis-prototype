# 🤖 J.A.R.V.I.S. İçin Yapay Zeka ile Özelleştirme Rehberi
> *Bu projeyi Gemini, Claude, Cursor, ChatGPT, Antigravity veya Copilot gibi yapay zekalara vererek kendinize göre nasıl yeniden yazdırabilirsiniz?*

[![English Guide](https://img.shields.io/badge/Guide-English_Version-blue.svg)](AI_CUSTOMIZATION_GUIDE.md)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 🎯 Bu Rehberin Amacı

Bu projenin kod mimarisi, **yapay zeka ajanlarının (AI Agents) kolayca okuyup geliştirebileceği modüler bir yapıda** tasarlanmıştır:
- Görevler net şekilde ayrılmıştır (`brain.py`, `tools.py`, `server.py`, `config.py`).
- Karmaşık, anlaşılması zor kütüphane bağımlılıkları yoktur.
- Fonksiyonlar doğrudan Python'ın doğal yapısıyla çalışır.

İster **Google Gemini**, **Anthropic Claude**, **Cursor IDE**, **ChatGPT** ister **Google Antigravity** kullanın; bu repoyu yapay zekaya verip birkaç cümleyle projenin adını, ses tonunu, işletim sistemini veya akıllı ev sisteminizi Jarvis'e bağlatabilirsiniz.

---

## 🗺️ Yapay Zeka İçin Kod Haritası

Bir yapay zekaya (LLM) değişiklik yaptırırken bütün kodları aynı anda vermenize gerek yoktur. Context (bağlam) sınırını aşmamak ve modelin hata yapmasını önlemek için sadece ilgili dosyaları modele yüklemeniz yeterlidir:

| Neyi Değiştirmek İstiyorsunuz? | Yapay Zekaya Vereceğiniz Dosyalar | Bu Dosyaların İçinde Ne Var? |
| :--- | :--- | :--- |
| **Kişilik, Ses Tonu, Hitap & İsim** | [`backend/config.py`](backend/config.py)<br>[`backend/brain.py`](backend/brain.py) | Sistem promptu, hitap şekli ("Sir"), asistanın karakteri ve yedek mekanizmaları. |
| **Sistem Komutları (Mac / Windows / Linux)** | [`backend/tools.py`](backend/tools.py)<br>[`backend/brain.py`](backend/brain.py) | Ses açıp/kısma, pil durumu, hava durumu, uygulama açıcı. |
| **Akıllı Ev & Işıklar (Home Assistant / Philips Hue)** | [`backend/tools.py`](backend/tools.py)<br>[`backend/config.py`](backend/config.py) | REST API istekleri, webhooklar, akıllı lamba açma/kapama fonksiyonları. |
| **Yapay Zeka Modelleri (Claude, DeepSeek vb.)** | [`backend/brain.py`](backend/brain.py)<br>[`backend/config.py`](backend/config.py) | Gemini, OpenAI, Ollama API çağrıları ve yönlendirme mantığı. |
| **Telegram Uzaktan Erişim Botu** | [`backend/telegram_bot.py`](backend/telegram_bot.py) | Sesli mesaj transkripsiyonu, sohbet dinleme, üretilen videoları telefona atma. |
| **Alexa Sesli Komutları & Çağırma İsmi** | [`alexa/interaction_model_en.json`](alexa/interaction_model_en.json)<br>[`backend/server.py`](backend/server.py) | Alexa skill komutları, örnek cümleler ve intent uç noktaları. |
| **TikTok/Shorts Video Üretici** | [`backend/video_generator.py`](backend/video_generator.py) | FFmpeg video işleme, alt yazı motoru, ses miksajı ve 9:16 sinematik katman. |

---

## 📋 Kopyala-Yapıştır Yapay Zeka Promptları (Hazır Şablonlar)

Aşağıdaki komut şablonlarını doğrudan **Gemini**, **Claude**, **ChatGPT** veya **Cursor Composer**'a yapıştırarak kodunuzu saniyeler içinde özelleştirebilirsiniz:

---

### 🎨 Şablon 1: Asistanın İsmini, Kişiliğini ve Hitap Tarzını Değiştirme

```markdown
Elimde Amazon Echo Dot'u bir Python backend'e bağlayan açık kaynaklı bir J.A.R.V.I.S. projesi var.
Ekte `backend/config.py` ve `backend/brain.py` dosyaları bulunuyor.

Lütfen bu dosyaları şu şekilde güncelle:
1. Jarvis'in resmi İngiliz uşağı tarzını değiştir: [İSTEDİĞİNİZ KİŞİLİK, örn: "Esprili, sarkastik bir Siberpunk yapay zekası olan FRIDAY yap" veya "Daha samimi ve Türkçe konuşan bir ders çalışma asistanı yap"].
2. Bana "Sir" diye hitap etmesi yerine "[KENDİ İSMİNİZ VEYA HİTAP TARZINIZ]" olarak hitap etsin.
3. Yanıtları kısa tutsun (en fazla 2-3 cümle), çünkü Amazon Echo bu yanıtları sesli olarak okuyor ve uzun metinler sesli asistanda hantal hissettiriyor.
4. `config.py` içindeki sistem promptunu ve `brain.py` içindeki yönlendiricileri bu yeni karaktere uygun hale getir.
```

---

### 💻 Şablon 2: Windows veya Linux'a Uyarlama (macOS AppleScript Yerine)

```markdown
Şu anda `backend/tools.py` dosyası ses seviyesini ayarlamak ve uygulamaları açmak için macOS AppleScript (`osascript`) kullanıyor.
Ben bu projeyi [Windows 11 / Ubuntu Linux] üzerinde çalıştırıyorum.

Ekte `backend/tools.py` dosyası var.
Lütfen aşağıdaki fonksiyonları benim işletim sistemimde yerel çalışacak şekilde yeniden yaz:
1. `set_volume(level)`: [Windows için pycaw veya ctypes / Linux için amixer veya pactl] kullan.
2. `get_battery()`: İşletim sisteminden bağımsız olarak pil durumunu okumak için [psutil] kullan.
3. `open_app(app_name)`: İşletim sisteminde doğrudan uygulama açmak için native komut kullan (`os.startfile` veya `subprocess.Popen`).
4. Hata durumlarında FastAPI sunucusunun çökmemesi için try-except bloklarını koru.
```

---

### 🏠 Şablon 3: Akıllı Ev Işıklarını ve Cihazları Bağlama (Home Assistant)

```markdown
Echo Dot Jarvis'imin evimdeki akıllı lambaları Home Assistant REST API üzerinden kontrol etmesini istiyorum.
Ekte `backend/config.py`, `backend/tools.py` ve `backend/brain.py` dosyaları var.

Lütfen:
1. `config.py` içine şu ortam değişkenlerini ekle:
   - `HASS_URL = os.getenv("HASS_URL", "http://homeassistant.local:8123")`
   - `HASS_TOKEN = os.getenv("HASS_TOKEN", "")`
2. `tools.py` içine `toggle_light(entity_id, state="toggle")` fonksiyonu yaz. Home Assistant'ın `/api/services/light/toggle` servisine Bearer token ile POST isteği atsın.
3. `brain.py` içine kullanıcı "odanın ışıklarını kapat", "masanın lambasını aç" dediğinde bu fonksiyonu tetikleyecek ve ardından şık bir sesli teyit dönecek mantığı entegre et.
```

---

### 🧠 Şablon 4: Yeni Bir LLM Modeli Ekleme (DeepSeek V3 veya Claude 3.5 Sonnet)

```markdown
J.A.R.V.I.S.'e yeni bir yapay zeka sağlayıcısı olarak [DeepSeek V3 / Anthropic Claude 3.5 Sonnet] eklemek istiyorum.
Ekte `backend/config.py` ve `backend/brain.py` dosyaları var.

Lütfen:
1. `config.py` içine yeni modelin API Key ve Model Adı değişkenlerini ekle.
2. `brain.py` içine standart Python SDK veya httpx kullanarak asenkron çalışan `ask_deepseek(prompt)` fonksiyonunu yaz.
3. Bunu `ask_jarvis(prompt)` yönlendiricisine ekle; böylece `.env` dosyama `AI_PROVIDER=deepseek` yazdığımda doğrudan bu model çalışsın.
4. Kota aşımı veya hata durumunda Gemini Flash'a otomatik geçiş yapan fallback yapısını koru.
```

---

### 🎙️ Şablon 5: Alexa Uyandırma İsmini Değiştirme (Jarvis Yerine Başka İsim)

```markdown
Şu an Echo Dot'a "Alexa, open Jarvis" denildiğinde skill açılıyor.
Ekte `alexa/interaction_model_en.json` dosyası var.

Lütfen:
1. Çağırma adını (invocation name) "jarvis" yerine "[İSTEDİĞİNİZ İSİM, örn: 'friday', 'bilgisayar' veya 'asistanım']" yap.
2. En sık kullandığım şu komutlar için yeni örnek cümleler (sample utterances) ekle:
   - "[eklemek istediğiniz sesli komutlar]"
3. JSON yapısının Amazon Alexa Developer Console ile tam uyumlu kalmasını sağla.
```

---

## ⚠️ Yapay Zekaya Kod Yazdırırken 4 Altın Kural

Yapay zekanın bu projede kod üretirken hata yapmaması için şu 4 kuralı mutlaka hatırlatın:

1. **Sesli Yanıt Hız Sınırı (< 3 saniye):**
   Amazon Alexa webhook cevabı ~8 saniyeden uzun sürerse zaman aşımı (timeout) hatası verir. Bu yüzden yapay zeka modelinin yanıtını kısa (`max_tokens=250`) ve hızlı tutun; senkron bloklayıcı işlemler yapmayın.
2. **Arka Plan Görevleri (Non-blocking Tasks):**
   Eğer yapılacak işlem 3 saniyeden uzun sürecekse (örn: 60 saniyelik TikTok videosu renderlamak veya web kazımak), işlemi `asyncio.create_task()` ile arka plana atın ve Alexa'ya hemen *"İşlemi arka planda başlattım efendim"* yanıtı dönün.
3. **Gizli Bilgileri Koda Asla Yazmayın:**
   Tüm API anahtarları, şifreler ve tokenlar `backend/config.py` üzerinden `os.getenv` ile okunmalıdır. Yapay zekanın Python dosyalarına doğrudan şifre yazmasına izin vermeyin.
4. **Hata Yakalama (Try-Except / Fallbacks):**
   Sesli asistan el kullanmadan yönetildiği için 500 sunucu hatası vermemelidir. Bir API çökerse zarif bir sesli yanıtla durum kullanıcıya bildirilmeli veya yedek modele geçilmelidir.
