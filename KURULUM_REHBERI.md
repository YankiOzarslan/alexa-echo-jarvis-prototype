# 🚀 Echo Dot ile Yapay Zeka Jarvis Kurulum Rehberi

[![English Setup Guide](https://img.shields.io/badge/Guide-English_Version-blue.svg)](SETUP_GUIDE.md)
[![Yapay Zeka ile Özelleştirme](https://img.shields.io/badge/Rehber-Yapay_Zeka_%C3%96zelle%C5%9Ftirme-green.svg)](YAPAY_ZEKA_OZELLESTIRME_REHBERI.md)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Bu rehber, elinizdeki **Amazon Echo Dot (2. Nesil)** cihazını **sıfır maliyetle** (Amazon'un paralı abonelik tuzaklarına bulaşmadan) gerçek bir yapay zeka (LLM) destekli **J.A.R.V.I.S.** asistanına nasıl dönüştüreceğinizi adım adım açıklar.

---

## 💡 Neden Amazon'a Para Ödemiyoruz?

Amazon Echo cihazları normalde sürekli *"Amazon Music abonesi olun"*, *"Audible satın alın"* gibi yönlendirmeler yapar.
Ancak Amazon, geliştiricilerin kendi özel sesli uygulamalarını yapabilmesi için **Alexa Developer Console (Geliştirici Konsolu)** sunar ve bu tamamen **ÜCRETSİZDİR**.

Biz burada cihazı mağaza için değil, **kendimize özel geliştirici modunda (Development Mode)** çalıştıracağız:
1. Siz *"Alexa, open Jarvis"* dediğiniz an Amazon'un tüm standart reklam ve paralı yönlendirmeleri devreden çıkar.
2. Echo Dot sadece hassas mikrofon ve hoparlör görevi görür; söylediğinizi metne döküp Mac'inizde çalışan Python servisine yollar.
3. Yanıtı Mac'inizdeki yapay zeka beyni (Google Gemini veya OpenAI veya yerel model) üretir ve Echo Dot bunu seslendirir.

---

## 🛠️ ADIM 1: Mac Üzerinde Jarvis Backend Kurulumu

### 1.1. Bağımlılıkları Yükleyin
Terminali açın ve proje klasöründe şu komutu çalıştırın:
```bash
pip install -r requirements.txt
```

### 1.2. Yapay Zeka API Anahtarını Ekleyin
Proje kök dizininde `.env.example` dosyasının bir kopyasını `.env` olarak oluşturun:
```bash
cp .env.example .env
```
Ardından `.env` dosyasını açın:
- **Google Gemini (Tavsiye Edilen - Ücretsiz & Hızlı):**
  - [Google AI Studio](https://aistudio.google.com/) adresine girin, ücretsiz bir API Key alın.
  - `.env` içine yapıştırın:
    ```env
    AI_PROVIDER=gemini
    GEMINI_API_KEY=your_gemini_api_key_here
    GEMINI_MODEL=gemini-2.5-flash
    ```
- *(Alternatif)* OpenAI kullanmak isterseniz `AI_PROVIDER=openai` yapıp `OPENAI_API_KEY` girin.

### 1.3. Jarvis'i Başlatın
```bash
python3 run.py
```
Terminalde Jarvis'in `http://localhost:8000` portunda çalıştığını göreceksiniz.

---

## 🌐 ADIM 2: Dış Dünyaya Açma (Ücretsiz HTTPS Tüneli)

Amazon sunucularının Mac'inizdeki Jarvis'e ulaşabilmesi için geçerli bir HTTPS bağlantısı gerekir. Bunun en kolay ve ücretsiz yolu **Cloudflare Tunnel** kullanmaktır.

1. Cloudflare tünel aracını yükleyin:
   ```bash
   brew install cloudflared
   ```
2. Yeni bir terminal penceresinde tüneli başlatın:
   ```bash
   cloudflared tunnel --url http://localhost:8000
   ```
3. Terminalde size verilen `https://xxxx-xxxx.trycloudflare.com` şeklindeki URL'yi kopyalayın. *(Bu sizin canlı webhook adresinizdir).*

---

## ☁️ ADIM 3: Amazon Developer Console Ayarları (5 Dakika)

1. [developer.amazon.com/alexa/console/ask](https://developer.amazon.com/alexa/console/ask) adresine gidin. Echo Dot'unuzun kayıtlı olduğu Amazon hesabıyla giriş yapın.
2. Sağ üstteki **"Create Skill"** butonuna tıklayın.
3. Bilgileri şu şekilde doldurun:
   - **Skill name:** `Jarvis`
   - **Primary locale:** `English (US)` *(Echo Dot 2 modelleri US/UK profilinde en yüksek algılama başarısına sahiptir; Türkçe konuşsanız bile backend yapay zekamız Türkçe yanıt verecektir!)*
   - **Experience:** `Other` -> `Custom`
   - **Hosting service:** `Provision your own` *(Sayfanın en altındaki bu seçeneği seçin)*
   - Sağ üstten **"Next"** butonuna tıklayın.
   - Template seçimi sorarsa **"Start from Scratch"** seçin ve **"Create Skill"** deyin.

### 3.1. Etkileşim Modelini Yükleyin:
1. Sol menüden **Interaction Model** -> **JSON Editor** bölümüne tıklayın.
2. Bu projedeki [alexa/interaction_model_en.json](alexa/interaction_model_en.json) dosyasının tüm içeriğini kopyalayıp kutunun içine yapıştırın.
3. Yukarıdaki **"Save Model"** ve ardından **"Build Model"** butonuna basın (Modelin derlenmesi 1-2 dakika sürer).

### 3.2. Webhook Adresinizi Bağlayın (Endpoint):
1. Sol menüden **Endpoint** sekmesine tıklayın.
2. **HTTPS** seçeneğini işaretleyin.
3. **Default Region** kutusuna tünel adresinizi `/alexa` ekiyle birlikte yapıştırın:
   `https://xxxx-xxxx.trycloudflare.com/alexa`
4. Açılan dropdown menüden şu SSL seçeneğini seçin:
   - *"My development endpoint is a sub-domain of a domain that has a wildcard certificate from a certificate authority"*
5. Sayfanın en üstündeki **"Save Endpoints"** butonuna tıklayın.

---

## 🔊 ADIM 4: Echo Dot 2 Üzerinde Canlı Kullanım

1. Amazon Developer Console'da en üstteki **Test** sekmesine tıklayın.
2. Sol üstteki **"Skill testing is enabled in:"** ayarını `Off` durumundan **`Development`** durumuna getirin.
3. **İşte bu kadar!** Echo Dot 2 cihazınız aynı Amazon hesabına bağlı olduğu için anında hazır hale gelir.

### Nasıl Kullanacaksınız?
Echo Dot 2'nize seslenin:
> **Siz:** *"Alexa, open Jarvis"*  
> **Echo Dot (Jarvis):** *"Jarvis devrede efendim. Sizi dinliyorum, emriniz nedir?"*  
> **Siz:** *"Kuantum bilgisayarları bana 2 cümleyle anlatır mısın?"*  
> **Echo Dot (Jarvis):** *(Yapay zekanın yanıtını seslendirir ve oturumu açık tutar)*  
> **Siz:** *"Mac'in sesini yüzde yetmiş yap"*  
> **Echo Dot (Jarvis):** *"Mac system volume set to 70% efendim."*  
> **Siz:** *"Bugün hava kaç derece?"*  
> **Echo Dot (Jarvis):** *"İstanbul'da şu an sıcaklık 18 derece efendim."*  
> **Siz:** *"Teşekkürler, kapatabilirsin"*  
> **Echo Dot (Jarvis):** *"Görüşmek üzere efendim. Sistemler bekleme moduna alınıyor."*

---

## 🎯 Gelişmiş Özellikler
- **Sürekli Diyalog (Multi-turn Conversation):** Her cümleden sonra tekrar "Alexa" demenize gerek kalmaz; Jarvis cevabı verdikten sonra sizi dinlemeye devam eder.
- **Mac Sistem Entegrasyonu:** Ses seviyesini kontrol edebilir, uygulamaları açabilir ve şarj durumunu sorgulayabilirsiniz.
- **Canlı Terminal İzleme:** Mac terminalinizde kullanıcının söylediği metinleri ve Jarvis'in düşünme sürecini canlı olarak izleyebilirsiniz.
