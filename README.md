# 🚦 Trafikİz: Ankara Akıllı Şehir Dijital İkizi ve Karar Destek Sistemi

**Trafikİz**, Ankara D200 (Eskişehir Yolu) aksındaki kritik kavşakların trafik yoğunluğunu ve hava durumu verilerini eş zamanlı olarak işleyerek analiz eden Python tabanlı bir **Dijital İkiz (Digital Twin)** ve **Karar Destek Sistemi (KDS)** projesidir.

Geleneksel harita uygulamaları sadece *durum tespiti* yaparken, Trafikİz proaktif bir yaklaşımla çalışır. Gerçek zamanlı API'lerden çekilen verileri matematiksel bir yoğunluk endeksinden geçirir ve olası kilitlenmeleri otonom olarak tespit eder. Sistemi sıradan bir harita olmaktan çıkaran en büyük özellik; sisteme entegre edilen **Büyük Dil Modeli (Gemini AI)** sayesinde kriz anlarında kullanıcılara spesifik, anlık ve mantıksal alternatif rota tavsiyeleri üretebilmesidir.

## ✨ Öne Çıkan Özellikler

* 📍 **Kavşak Odaklı (Node-Based) Mimari:** İlçe sınırları gibi geniş ve belirsiz alanlar yerine; Ümitköy Köprüsü, Bilkent Şehir Hastanesi Kavşağı gibi trafiğin gerçek anlamda kilitlendiği spesifik düğüm noktaları izlenir.
* 🤖 **RAG Tabanlı Gemini AI Asistanı:** Sistemdeki canlı hız ve meteoroloji verileri arka planda Gemini yapay zekasına beslenir. Kullanıcı "Ambulansım var, Eskişehir yolu kilitli" dediğinde, sistem halüsinasyon görmeden sadece o anki canlı Ankara verisine dayanarak en hızlı rotayı çizer.
* 🕹️ **"What-If" Simülasyon Motoru:** Karar vericilerin (UKOME, 112 Acil), gerçek hayatta bir yolu kapatmadan veya yoğunluk aniden artmadan önce "Sincan'da yoğunluk %80 artarsa ve hava yağmurlu olursa ne olur?" sorusunu dijital ortamda test edebilmesini sağlar.
* ⚡ **Dinamik Uyarı Paneli:** Herhangi bir kavşakta anlık hız, serbest akış hızının belirlenen eşiğinin altına düştüğünde arayüz otonom olarak kırmızı alarm verir ve rota tavsiyesini ekrana basar.

## 🛠️ Kullanılan Teknolojiler

* **Dil:** Python 3
* **Arayüz (Frontend):** Streamlit
* **Mekansal Görselleştirme:** Folium, Streamlit-Folium
* **Veri Kaynakları:**
  * TomTom Traffic Flow API (Anlık ve Serbest Akış Hızı)
  * OpenWeatherMap API (Koordinat Bazlı Canlı Hava Durumu)
  * Google Gemini API (LLM Karar Destek Asistanı)

---

## 🚀 Kurulum ve Çalıştırma Adımları

Projeyi kendi bilgisayarınızda çalıştırmak için aşağıdaki adımları sırasıyla uygulayın.

### 1. Projeyi Klonlayın
git clone [https://github.com/kullaniciadiniz/trafikiz.git](https://github.com/myelifs/trafikiz.git)
cd trafikiz

### 2. Sanal Ortam (.venv) Oluşturun ve Aktif Edin
Projenin kütüphane çakışmalarını önlemek için izole bir ortam kurun:

Bash
# Windows için:
python -m venv .venv
.\.venv\Scripts\activate

# macOS / Linux için:
python3 -m venv .venv
source .venv/bin/activate

### 3. Gerekli Kütüphaneleri Yükleyin
Bash
pip install -r requirements.txt

### 4. ⚠️ Çevresel Değişkenleri (.env) Ayarlayın (ÇOK ÖNEMLİ)
Güvenlik prensipleri gereği API şifrelerini barındıran .env dosyası bu GitHub reposuna eklenmemiştir. Projeyi çalıştırabilmek için ana dizinde (app.py ile aynı yerde) kendiniz bir .env dosyası oluşturmalı ve içine kendi API anahtarlarınızı aşağıdaki formatta yazmalısınız:

Kod snippet'i
TOMTOM_API_KEY="sizin_tomtom_anahtariniz_buraya"
OPENWEATHER_API_KEY="sizin_openweather_anahtariniz_buraya"
GEMINI_API_KEY="sizin_gemini_anahtariniz_buraya"

### 5. Uygulamayı Başlatın
Tüm adımları tamamladıktan sonra yönetim panelini tarayıcınızda açmak için:

Bash
# streamlit run app.py

## 📊 Proje Yönetimi ve Ürün Yol Haritası (Product Roadmap)

Trafikİz, salt bir kodlama pratiği olarak değil; uçtan uca tasarlanmış, Çevik (Agile) prensiplerle yönetilen bir ürün (SaaS) vizyonuyla geliştirilmektedir. Proje yöneticisi şapkasıyla yürütülen ürün yaşam döngüsü şu şekildedir:

* **MVP (Minimum Çalışır Ürün) Fazı - Mevcut Durum:** * Karar vericiler (UKOME, Emniyet, 112) için karmaşık grafiklerden arındırılmış, aksiyon odaklı minimal UI/UX tasarımı.
  * API entegrasyonlarının ve RAG tabanlı Gemini Karar Destek Asistanı'nın canlıya alınması.
* **Paydaş ve İhtiyaç Analizi:** Sadece "harita göstermek" yerine, kriz anındaki kullanıcının (örn: Ambulans şoförü) "Saniyeler içinde nereye sapmalıyım?" problemine doğrudan çözüm üreten KDS mimarisinin kurgulanması.
* **Gelecek Fazlar (Product Backlog):**
  * Geçmiş verilerin loglanması için Zaman Serisi Veritabanı entegrasyonu.
  * Otonom rota tavsiyelerinin sağladığı $CO_2$ emisyonu engelleme istatistiklerinin (Sürdürülebilirlik/Yeşil Teknoloji) eklenmesi.
  * Kesintisiz iletişim için Supabase altyapısı ile asenkron veri iletişimi.

---

## 👩‍💻 Proje Yöneticisi & Baş Geliştirici (Tech Lead)

**Miyase Elif Aksoy** *Bilecik Şeyh Edebali Üniversitesi - İstatistik ve Bilgisayar Bilimleri Bölümü*
