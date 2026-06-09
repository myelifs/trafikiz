"""
=============================================================================
  ANKARA AKILLI ŞEHİR TRAFİK HARİTASI (MVP) — KAVŞAK BAZLI
  -----------------------------------------------------------
  Ankara D200 (Eskişehir Yolu) hattındaki kritik kavşak ve bulvarların
  canlı trafik, kaza ve hava durumu verilerini API'lerden çekip,
  folium ile interaktif bir HTML haritasına basar.

  Düğüm Noktaları (Batı → Doğu):
      1. Polatlı D200 Sanayi Kavşağı
      2. Sincan OSB Kavşağı
      3. Eryaman Optimum Kavşağı
      4. Ümitköy Köprüsü
      5. Bilkent Şehir Hastanesi Kavşağı
      6. Anadolu Bulvarı Kesişimi

  Kullanım:
      1)  .env dosyasına TOMTOM_API_KEY ve OPENWEATHER_API_KEY yazın.
      2)  pip install -r requirements.txt
      3)  python main.py
      4)  Oluşan ankara_trafik_haritasi.html dosyasını tarayıcıda açın.
=============================================================================
"""

import os
import sys
import io
from datetime import datetime

# ---------------------------------------------------------------------------
# Windows Türkçe terminal (cp1254) emoji karakterlerini desteklemez.
# stdout'u UTF-8'e ayarlayarak UnicodeEncodeError hatasını önlüyoruz.
# ---------------------------------------------------------------------------
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import requests
import folium
from dotenv import load_dotenv

# ============================================================================
# ADIM 1 — KURULUM VE VERİ YAPISI
# ============================================================================

# .env dosyasındaki değişkenleri ortam değişkeni olarak yükle
load_dotenv()

# API anahtarlarını oku
TOMTOM_API_KEY = os.getenv("TOMTOM_API_KEY")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")


def api_anahtarlarini_kontrol_et():
    """
    .env dosyasındaki API anahtarlarının gerçekten doldurulup
    doldurulmadığını kontrol eder. Eksikse programı durdurur.
    """
    eksik = []
    if not TOMTOM_API_KEY or "buraya" in TOMTOM_API_KEY:
        eksik.append("TOMTOM_API_KEY")
    if not OPENWEATHER_API_KEY or "buraya" in OPENWEATHER_API_KEY:
        eksik.append("OPENWEATHER_API_KEY")

    if eksik:
        print("=" * 55)
        print("  HATA: Aşağıdaki API anahtarları eksik veya geçersiz:")
        for k in eksik:
            print(f"    ✗  {k}")
        print("\n  Lütfen .env dosyanızı açıp anahtarları yazın.")
        print("  Şablon dosya: .env.example")
        print("=" * 55)
        sys.exit(1)

    print("[✓] API anahtarları başarıyla yüklendi.")


# ---------------------------------------------------------------------------
# KRİTİK KAVŞAK VE BULVAR DÜĞÜMLERİ (Node-Based)
# ---------------------------------------------------------------------------
# Ankara D200 (Eskişehir Yolu) hattı üzerindeki 6 kritik düğüm noktası.
# Koordinatlar gerçek kavşak konumlarına göre belirlenmiştir.
# Sıralama: Batıdan doğuya doğru.
# ---------------------------------------------------------------------------
KAVSAKLAR = [
    {
        "ad":  "Polatlı D200 Sanayi Kavşağı",
        "lat": 39.5846,
        "lon": 32.1362,
        # D200'ün Polatlı Organize Sanayi Bölgesi ile kesiştiği kavşak
    },
    {
        "ad":  "Sincan OSB Kavşağı",
        "lat": 39.9497,
        "lon": 32.5534,
        # D200'ün Sincan Organize Sanayi Bölgesi girişiyle buluştuğu nokta
    },
    {
        "ad":  "Eryaman Optimum Kavşağı",
        "lat": 39.9473,
        "lon": 32.6312,
        # Eskişehir Yolu üzerinde Optimum AVM karşısındaki ana kavşak
    },
    {
        "ad":  "Ümitköy Köprüsü",
        "lat": 39.9086,
        "lon": 32.7384,
        # Eskişehir Yolu - Ümitköy üst geçidi / köprü kavşağı
    },
    {
        "ad":  "Bilkent Şehir Hastanesi Kavşağı",
        "lat": 39.8672,
        "lon": 32.7488,
        # Eskişehir Yolu'ndan Bilkent Şehir Hastanesi'ne ayrılan kavşak
    },
    {
        "ad":  "Anadolu Bulvarı Kesişimi",
        "lat": 39.9213,
        "lon": 32.8105,
        # Eskişehir Yolu ile Anadolu Bulvarı'nın kesiştiği büyük kavşak
    },
]

# ---------------------------------------------------------------------------
# İLÇE MERKEZLERİ (Sabit Etiket Katmanı)
# ---------------------------------------------------------------------------
# Haritada coğrafi okunabilirlik için ilçe isimlerini DivIcon ile
# metin olarak göstereceğiz. Bu marker'lar tıklanamaz, sadece isim yazar.
# ---------------------------------------------------------------------------
ILCE_MERKEZLERI = {
    "Polatlı":   {"lat": 39.5840, "lon": 32.1477},
    "Sincan":    {"lat": 39.9680, "lon": 32.5860},
    "Etimesgut": {"lat": 39.9450, "lon": 32.6580},
    "Çankaya":   {"lat": 39.9180, "lon": 32.8540},
    "Elmadağ":   {"lat": 39.9210, "lon": 33.2310},
}

# ---------------------------------------------------------------------------
# KAVŞAK → İLÇE EŞLEMESİ
# ---------------------------------------------------------------------------
# Her kavşak düğümünün hangi ilçeye bağlı olduğunu belirler.
# Popup ve tooltip'te "İlçe — Kavşak Adı" formatında gösterilir.
# ---------------------------------------------------------------------------
KAVSAK_ILCE_ESLEME = {
    "Polatlı D200 Sanayi Kavşağı":      "Polatlı",
    "Sincan OSB Kavşağı":               "Sincan",
    "Eryaman Optimum Kavşağı":          "Etimesgut",
    "Ümitköy Köprüsü":                  "Çankaya",
    "Bilkent Şehir Hastanesi Kavşağı":  "Çankaya",
    "Anadolu Bulvarı Kesişimi":         "Çankaya",
}

# ---------------------------------------------------------------------------
# ALTERNATİF ROTA SÖZLÜĞÜ
# ---------------------------------------------------------------------------
# Her kavşak için trafik sıkışıksa önerilen alternatif güzergâhlar.
# Anahtar: kavşak adı → Değer: alternatif rota tavsiyesi
# ---------------------------------------------------------------------------
ALTERNATIF_ROTALAR = {
    "Polatlı D200 Sanayi Kavşağı": (
        "🔄 Polatlı D200 Sanayi Kavşağı kilitliyse;\n"
        "• Polatlı-Temelli bağlantı yolundan geçerek Ankara Çevre Yolu'na (O-4) bağlanın.\n"
        "• Alternatif: Sakarya Mahallesi ara sokaklarını kullanarak D200'e geri dönün."
    ),
    "Sincan OSB Kavşağı": (
        "🔄 Sincan OSB Kavşağı kilitliyse;\n"
        "• Fatih Bulvarı üzerinden Sincan merkezine geçip, Tandoğan Caddesi ile "
        "Eryaman yönüne devam edin.\n"
        "• Alternatif: OSB iç yollarını kullanarak Ankara Bulvarı'na sapın."
    ),
    "Eryaman Optimum Kavşağı": (
        "🔄 Eryaman Optimum Kavşağı kilitliyse;\n"
        "• 1. Cadde (Eryaman Bulvarı) üzerinden güneye inip, "
        "Dumlupınar Bulvarı'na bağlanın.\n"
        "• Alternatif: Etimesgut Bulvarı'ndan devam ederek "
        "İstanbul Yolu servis yoluna geçin."
    ),
    "Ümitköy Köprüsü": (
        "🔄 Ümitköy Köprüsü kilitliyse;\n"
        "• Sabancı Bulvarı'na saparak Konutkent üzerinden Çayyolu'na inin.\n"
        "• Alternatif: 2629. Sokak → Yaşam Caddesi güzergâhını kullanarak "
        "Eskişehir Yolu'na paralel ilerleyin."
    ),
    "Bilkent Şehir Hastanesi Kavşağı": (
        "🔄 Bilkent Şehir Hastanesi Kavşağı kilitliyse;\n"
        "• Bilkent Üniversitesi kampüs içi yolundan geçerek "
        "Beytepe-ODTÜ bağlantısıyla Konya Yolu'na bağlanın.\n"
        "• Alternatif: İhsan Doğramacı Bulvarı ile güneye inip, "
        "1600. Cadde üzerinden devam edin."
    ),
    "Anadolu Bulvarı Kesişimi": (
        "🔄 Anadolu Bulvarı Kesişimi yoğunsa;\n"
        "• Konya Yolu'na bağlanarak Kızılay yönüne devam edin.\n"
        "• Alternatif: Mevlana Bulvarı üzerinden Söğütözü-Kızılay hattını kullanın.\n"
        "• Dönüş seçeneği: Dumlupınar Bulvarı → ODTÜ Yolu ile kampüs çevresinden dolanın."
    ),
}

# Tüm D200 hattını kapsayan bounding box (güneybatı → kuzeydoğu)
# Format: "minLon,minLat,maxLon,maxLat"
ANKARA_BBOX = "32.00,39.50,33.00,40.10"


# ============================================================================
# ADIM 2 — API VERİ ÇEKME FONKSİYONLARI (SENKRON)
# ============================================================================

def get_weather(lat: float, lon: float) -> dict:
    """
    OpenWeatherMap Current Weather API'den hava durumu verisini çeker.

    Parametreler:
        lat  : Enlem (örn. 39.9086)
        lon  : Boylam (örn. 32.7384)

    Döndürür:
        {
            "durum"    : str   – Hava durumu açıklaması (örn. "hafif yağmur")
            "sicaklik" : float – Sıcaklık (°C)
            "ikon_url" : str   – Hava durumu ikon görseli URL'si
        }
        Hata durumunda varsayılan değerlerle sözlük döner (program çökmez).
    """
    url = (
        f"https://api.openweathermap.org/data/2.5/weather"
        f"?lat={lat}&lon={lon}"
        f"&appid={OPENWEATHER_API_KEY}"
        f"&units=metric"   # Celsius cinsinden sıcaklık
        f"&lang=tr"        # Türkçe açıklamalar
    )

    try:
        yanit = requests.get(url, timeout=10)
        yanit.raise_for_status()
        veri = yanit.json()

        # JSON yapısından ihtiyacımız olan alanları çıkar
        hava_blogu = veri.get("weather", [{}])[0]
        ana_blok   = veri.get("main", {})
        ikon_kodu  = hava_blogu.get("icon", "01d")

        return {
            "durum":    hava_blogu.get("description", "bilinmiyor"),
            "sicaklik": ana_blok.get("temp", 0.0),
            "ikon_url": f"https://openweathermap.org/img/wn/{ikon_kodu}@2x.png",
        }

    except requests.RequestException as hata:
        # API hatası olursa ekrana uyarı bas, ama programı durdurma
        print(f"    [UYARI] Hava durumu alınamadı: {hata}")
        return {"durum": "veri yok", "sicaklik": 0.0, "ikon_url": ""}


def get_traffic_flow(lat: float, lon: float) -> dict:
    """
    TomTom Traffic Flow Segment Data API'den trafik akış verisini çeker.

    Parametreler:
        lat  : Enlem
        lon  : Boylam

    Döndürür:
        {
            "currentSpeed"  : int – Mevcut ortalama hız (km/h)
            "freeFlowSpeed" : int – Serbest akış hızı (trafiksiz hız, km/h)
        }
        Hata durumunda her iki değer de 0 döner.
    """
    url = (
        f"https://api.tomtom.com/traffic/services/4/flowSegmentData"
        f"/absolute/10/json"
        f"?point={lat},{lon}"
        f"&key={TOMTOM_API_KEY}"
    )

    try:
        yanit = requests.get(url, timeout=10)
        yanit.raise_for_status()
        veri = yanit.json()

        # flowSegmentData bloğundan hız bilgilerini al
        segment = veri.get("flowSegmentData", {})

        return {
            "currentSpeed":  segment.get("currentSpeed", 0),
            "freeFlowSpeed": segment.get("freeFlowSpeed", 0),
        }

    except requests.RequestException as hata:
        print(f"    [UYARI] Trafik akış verisi alınamadı: {hata}")
        return {"currentSpeed": 0, "freeFlowSpeed": 0}


def get_incidents(bbox: str) -> list:
    """
    TomTom Traffic Incident Details API'den belirtilen bounding box
    içindeki tüm trafik olaylarını (kaza, yol çalışması vb.) çeker.

    Parametreler:
        bbox : "minLon,minLat,maxLon,maxLat" formatında alan tanımı

    Döndürür:
        [
            {
                "lat"      : float – Olayın enlemi
                "lon"      : float – Olayın boylamı
                "aciklama" : str   – Olayın Türkçe açıklaması
            },
            ...
        ]
        Hata durumunda boş liste döner.
    """
    url = (
        f"https://api.tomtom.com/traffic/services/5/incidentDetails"
        f"?bbox={bbox}"
        f"&fields={{incidents{{type,geometry{{type,coordinates}},"
        f"properties{{iconCategory,events{{description}}}}}}}}"
        f"&language=tr-TR"
        f"&categoryFilter=0,1,2,3,4,5,6,7,8,9,10,11,14"
        f"&key={TOMTOM_API_KEY}"
    )

    try:
        yanit = requests.get(url, timeout=15)
        yanit.raise_for_status()
        veri = yanit.json()

        olaylar = veri.get("incidents", [])
        sonuc_listesi = []

        for olay in olaylar:
            geo   = olay.get("geometry", {})
            props = olay.get("properties", {})

            # Koordinatları geometri tipine göre çöz
            coords = geo.get("coordinates", [])
            geo_tip = geo.get("type", "")

            if geo_tip == "Point" and len(coords) >= 2:
                # Point: [lon, lat]
                olay_lon, olay_lat = coords[0], coords[1]
            elif geo_tip == "LineString" and coords:
                # LineString: ilk noktayı al [[lon, lat], ...]
                olay_lon, olay_lat = coords[0][0], coords[0][1]
            else:
                # Koordinat çözülemezse bu olayı atla
                continue

            # Olay açıklamalarını birleştir
            aciklamalar = [
                e.get("description", "Bilinmeyen olay")
                for e in props.get("events", [])
            ]
            aciklama_metni = "; ".join(aciklamalar) if aciklamalar else "Trafik olayı"

            sonuc_listesi.append({
                "lat":      olay_lat,
                "lon":      olay_lon,
                "aciklama": aciklama_metni,
            })

        return sonuc_listesi

    except requests.RequestException as hata:
        print(f"    [UYARI] Kaza/olay verisi alınamadı: {hata}")
        return []


# ============================================================================
# ADIM 3 — VERİ İŞLEME VE KARAR ALGORİTMASI
# ============================================================================

def verileri_topla_ve_analiz_et() -> list:
    """
    Her kavşak düğümü için API'lerden veri çeker ve karar algoritmasını uygular.

    Karar Algoritması:
        • currentSpeed < freeFlowSpeed × 0.80  →  status = "Sıkışık"
          (Mevcut hız, serbest akış hızının %80'inden düşükse sıkışık)
        • Aksi halde                            →  status = "Akıcı"

    Sıkışık olan kavşaklar için ALTERNATIF_ROTALAR sözlüğünden
    alternatif güzergâh tavsiyesi eklenir.

    Döndürür:
        Her kavşak düğümü için zenginleştirilmiş sözlük listesi.
    """
    print("\n" + "=" * 65)
    print("   ANKARA D200 KRİTİK KAVŞAK TRAFİK ANALİZİ — VERİ TOPLAMA")
    print("=" * 65)
    print(f"   Tarih/Saat    : {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
    print(f"   Düğüm Sayısı : {len(KAVSAKLAR)}")
    print("-" * 65)

    # ------------------------------------------------------------------
    # 1) Tüm D200 hattındaki kazaları/olayları TEK SEFERDE çek
    # ------------------------------------------------------------------
    print("\n📡 D200 hattı için kaza/olay verileri çekiliyor...")
    tum_kazalar = get_incidents(ANKARA_BBOX)
    print(f"   → Toplam {len(tum_kazalar)} olay bulundu.")

    # ------------------------------------------------------------------
    # 2) Her kavşak için hava durumu + trafik akışını çek, karar ver
    # ------------------------------------------------------------------
    kavsaklar_sonuc = []

    for kavsak in KAVSAKLAR:
        ad  = kavsak["ad"]
        lat = kavsak["lat"]
        lon = kavsak["lon"]

        print(f"\n📍 {ad}")
        print(f"   Koordinat: ({lat}, {lon})")

        # --- Hava durumu ---
        hava = get_weather(lat, lon)
        print(f"   🌤️  Hava  : {hava['sicaklik']:.1f}°C, {hava['durum']}")

        # --- Trafik akışı ---
        trafik = get_traffic_flow(lat, lon)
        mevcut_hiz  = trafik["currentSpeed"]
        serbest_hiz = trafik["freeFlowSpeed"]
        print(f"   🚗 Trafik : {mevcut_hiz} km/h (serbest: {serbest_hiz} km/h)")

        # --- KARAR ALGORİTMASI ---
        # Mevcut hız, serbest akış hızının %80'inden düşükse → Sıkışık
        if serbest_hiz > 0 and mevcut_hiz < serbest_hiz * 0.80:
            durum = "Sıkışık"
        else:
            durum = "Akıcı"

        # Yüzdesel yoğunluk oranını hesapla
        if serbest_hiz > 0:
            yogunluk_yuzdesi = round((1 - mevcut_hiz / serbest_hiz) * 100, 1)
        else:
            yogunluk_yuzdesi = 0.0

        print(f"   🚦 Durum  : {durum}  (yoğunluk: %{yogunluk_yuzdesi})")

        # --- Alternatif rota tavsiyesi ---
        # Sıkışıksa sözlükten al, akıcıysa boş bırak
        if durum == "Sıkışık":
            alternatif = ALTERNATIF_ROTALAR.get(ad, "Alternatif rota bilgisi yok.")
            print(f"   🔄 Alternatif rota önerildi.")
        else:
            alternatif = ""

        # --- Kavşağa yakın kazaları filtrele ---
        # Kavşak noktasına ~3 km yarıçap içindeki olayları seç
        # (~0.03° ≈ 3 km — kavşak bazlı olduğu için daha dar yarıçap)
        yakin_kazalar = []
        for kaza in tum_kazalar:
            if (abs(kaza["lat"] - lat) < 0.03 and
                abs(kaza["lon"] - lon) < 0.03):
                yakin_kazalar.append(kaza)

        print(f"   ⚠️  Yakın olay: {len(yakin_kazalar)} adet")

        # Sonuç sözlüğünü oluştur
        kavsaklar_sonuc.append({
            "ad":                ad,
            "lat":               lat,
            "lon":               lon,
            "hava_durum":        hava["durum"],
            "sicaklik":          hava["sicaklik"],
            "hava_ikon_url":     hava["ikon_url"],
            "mevcut_hiz":        mevcut_hiz,
            "serbest_hiz":       serbest_hiz,
            "yogunluk_yuzdesi":  yogunluk_yuzdesi,
            "durum":             durum,            # "Sıkışık" veya "Akıcı"
            "alternatif_rota":   alternatif,       # Sıkışıksa dolulur
            "yakin_kazalar":     yakin_kazalar,
        })

    print("\n" + "-" * 65)
    print(f"[✓] {len(kavsaklar_sonuc)} kavşak düğümü için veri toplama tamamlandı.\n")
    return kavsaklar_sonuc


# ============================================================================
# ADIM 4 — FOLİUM İLE HARİTA ÜRETİMİ
# ============================================================================

def harita_olustur(kavsaklar_sonuc: list) -> folium.Map:
    """
    Toplanan ve analiz edilen verileri kullanarak interaktif folium
    haritasını oluşturur. Marker'lar kavşak noktalarının tam üzerine
    yerleştirilir.
    """
    print("🗺️  Harita oluşturuluyor...\n")

    # ------------------------------------------------------------------
    # Harita oluştur — Merkez: Ümitköy Köprüsü civarı (D200 orta nokta)
    # ------------------------------------------------------------------
    harita = folium.Map(
        location=[39.91, 32.68],       # D200 hattının ortası
        zoom_start=10,                 # Tüm kavşaklar görünsün
        tiles="CartoDB dark_matter",   # Koyu tema
    )

    # ------------------------------------------------------------------
    # KATMAN 1: Sabit İlçe İsimleri (DivIcon ile metin etiketleri)
    # ------------------------------------------------------------------
    # İlçe isimlerini haritanın üzerine şık fontla yerleştir.
    # Bunlar tıklanamaz, sadece coğrafi referans sağlar.
    # ------------------------------------------------------------------
    ilce_katmani = folium.FeatureGroup(name="📌 İlçe İsimleri")

    for ilce_adi, koordinat in ILCE_MERKEZLERI.items():
        # DivIcon: standart iğne yerine sadece metin gösterir
        ilce_etiketi = folium.DivIcon(
            html=f"""
            <div style="
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 14px;
                font-weight: bold;
                color: #ecf0f1;
                text-shadow: 0 0 6px rgba(0,0,0,0.9), 0 0 12px rgba(0,0,0,0.6);
                white-space: nowrap;
                letter-spacing: 1px;
            ">{ilce_adi}</div>
            """,
            icon_size=(120, 20),
            icon_anchor=(60, 10),  # Metni koordinatın tam ortasına hizala
        )

        folium.Marker(
            location=[koordinat["lat"], koordinat["lon"]],
            icon=ilce_etiketi,
            # DivIcon marker'lar tıklanamaz, sadece görsel etiket
        ).add_to(ilce_katmani)

    ilce_katmani.add_to(harita)
    print("   📌 İlçe isim etiketleri eklendi.")

    # ------------------------------------------------------------------
    # KATMAN 2: Canlı Kavşak İğneleri (renkli marker'lar)
    # ------------------------------------------------------------------
    kavsak_katmani = folium.FeatureGroup(name="🚦 Kavşak Durumları")

    for kavsak in kavsaklar_sonuc:
        # Kavşağın bağlı olduğu ilçeyi bul
        bagli_ilce = KAVSAK_ILCE_ESLEME.get(kavsak["ad"], "")

        # --- Marker rengi: Sıkışık → kırmızı, Akıcı → yeşil ---
        if kavsak["durum"] == "Sıkışık":
            marker_rengi = "red"
            durum_emoji  = "🔴"
            durum_renk   = "#e74c3c"
        else:
            marker_rengi = "green"
            durum_emoji  = "🟢"
            durum_renk   = "#2ecc71"

        # --- Yakın kazaların listesini HTML olarak hazırla ---
        if kavsak["yakin_kazalar"]:
            kaza_satirlari = ""
            for kaza in kavsak["yakin_kazalar"][:5]:
                kaza_satirlari += f"<li>{kaza['aciklama']}</li>"
            kaza_html = f"""
            <div style="margin-top:8px;padding-top:6px;border-top:1px solid #555;">
                <b>⚠️ Yakın Olaylar ({len(kavsak['yakin_kazalar'])} adet):</b>
                <ol style="margin:4px 0;padding-left:18px;font-size:12px;">
                    {kaza_satirlari}
                </ol>
            </div>
            """
        else:
            kaza_html = """
            <div style="margin-top:8px;padding-top:6px;border-top:1px solid #555;">
                <span style="color:#999;">✅ Yakında bilinen olay yok.</span>
            </div>
            """

        # --- Alternatif rota HTML bloğu ---
        if kavsak["alternatif_rota"]:
            # Satır sonlarını <br> ile değiştir, • işaretlerini koru
            rota_metin = kavsak["alternatif_rota"].replace("\n", "<br>")
            alternatif_html = f"""
            <div style="margin-top:8px;padding:8px;background:#1a252f;
                        border-left:3px solid #f39c12;border-radius:4px;
                        font-size:12px;line-height:1.5;">
                {rota_metin}
            </div>
            """
        else:
            alternatif_html = ""

        # --- Popup HTML içeriği ---
        popup_icerik = f"""
        <div style="
            font-family: 'Segoe UI', Arial, sans-serif;
            min-width: 280px;
            max-width: 340px;
            color: #ecf0f1;
            background: #2c3e50;
            padding: 14px;
            border-radius: 8px;
        ">
            <!-- İlçe ve Kavşak Adı -->
            <p style="margin:0 0 4px;font-size:11px;color:#95a5a6;
                       text-transform:uppercase;letter-spacing:1px;">
                📌 {bagli_ilce}
            </p>
            <h3 style="margin:0 0 10px; color:{durum_renk}; font-size:15px;">
                {durum_emoji} {kavsak['ad']}
            </h3>

            <!-- Hava Durumu -->
            <div style="display:flex; align-items:center; margin-bottom:8px;">
                <img src="{kavsak['hava_ikon_url']}" width="40"
                     style="margin-right:8px;" alt="hava">
                <div>
                    <b>Hava Durumu:</b> {kavsak['hava_durum'].capitalize()}<br>
                    <b>Sıcaklık:</b> {kavsak['sicaklik']:.1f} °C
                </div>
            </div>

            <!-- Trafik Bilgisi Tablosu -->
            <table style="width:100%; font-size:13px; border-collapse:collapse;">
                <tr>
                    <td style="padding:3px 0;">🚗 <b>Mevcut Hız:</b></td>
                    <td style="padding:3px 0;">{kavsak['mevcut_hiz']} km/h</td>
                </tr>
                <tr>
                    <td style="padding:3px 0;">🛣️ <b>Serbest Akış Hızı:</b></td>
                    <td style="padding:3px 0;">{kavsak['serbest_hiz']} km/h</td>
                </tr>
                <tr>
                    <td style="padding:3px 0;">📊 <b>Yoğunluk:</b></td>
                    <td style="padding:3px 0;">%{kavsak['yogunluk_yuzdesi']}</td>
                </tr>
                <tr>
                    <td style="padding:3px 0;"><b>🚦 Durum:</b></td>
                    <td style="padding:3px 0;font-weight:bold;color:{durum_renk};">
                        {kavsak['durum']}
                    </td>
                </tr>
            </table>

            <!-- Yakın Kazalar -->
            {kaza_html}

            <!-- Alternatif Rota Tavsiyesi (sadece sıkışıksa görünür) -->
            {alternatif_html}

            <!-- Zaman damgası -->
            <p style="margin:8px 0 0;font-size:11px;color:#7f8c8d;text-align:right;">
                Güncelleme: {datetime.now().strftime('%H:%M:%S')}
            </p>
        </div>
        """

        # --- Marker'ı kavşağın tam koordinatına yerleştir ---
        folium.Marker(
            location=[kavsak["lat"], kavsak["lon"]],
            popup=folium.Popup(popup_icerik, max_width=360),
            tooltip=(
                f"{durum_emoji} {bagli_ilce} — {kavsak['ad']} — "
                f"{kavsak['durum']} ({kavsak['mevcut_hiz']} km/h)"
            ),
            icon=folium.Icon(
                color=marker_rengi,
                icon="info-sign",
                prefix="glyphicon",
            ),
        ).add_to(kavsak_katmani)

        print(f"   {durum_emoji} [{bagli_ilce}] {kavsak['ad']}")
        print(f"      {kavsak['durum']:8s} | "
              f"{kavsak['mevcut_hiz']:3d}/{kavsak['serbest_hiz']:3d} km/h | "
              f"{kavsak['sicaklik']:.0f}°C {kavsak['hava_durum']}")

    kavsak_katmani.add_to(harita)

    # ------------------------------------------------------------------
    # D200 hattı çizgisi (kavşakları birbirine bağlayan kesikli çizgi)
    # ------------------------------------------------------------------
    hat_koordinatlari = [[k["lat"], k["lon"]] for k in kavsaklar_sonuc]
    folium.PolyLine(
        hat_koordinatlari,
        color="#3498db",
        weight=3,
        opacity=0.6,
        dash_array="10",
        tooltip="D200 Eskişehir Yolu Hattı (Polatlı → Anadolu Blv.)",
    ).add_to(harita)

    # ------------------------------------------------------------------
    # Başlık kutusu (sol üst köşe)
    # ------------------------------------------------------------------
    baslik_html = f"""
    <div style="
        position: fixed;
        top: 12px; left: 60px;
        z-index: 9999;
        background: rgba(44,62,80,0.93);
        padding: 12px 22px;
        border-radius: 10px;
        border-left: 4px solid #3498db;
        font-family: 'Segoe UI', Arial, sans-serif;
        color: #ecf0f1;
        box-shadow: 0 4px 20px rgba(0,0,0,0.4);
    ">
        <h3 style="margin:0; color:#3498db; font-size:16px;">
            🏙️ Ankara D200 Kritik Kavşak Trafik Haritası
        </h3>
        <p style="margin:4px 0 0; font-size:12px; color:#bdc3c7;">
            Son güncelleme: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}
            &nbsp;·&nbsp; Eskişehir Yolu Hattı &nbsp;·&nbsp;
            {len(kavsaklar_sonuc)} Düğüm Noktası
        </p>
    </div>
    """
    harita.get_root().html.add_child(folium.Element(baslik_html))

    # ------------------------------------------------------------------
    # Lejant kutusu (sağ alt köşe)
    # ------------------------------------------------------------------
    lejant_html = """
    <div style="
        position: fixed;
        bottom: 30px; right: 20px;
        z-index: 9999;
        background: rgba(44,62,80,0.93);
        padding: 12px 18px;
        border-radius: 10px;
        border: 1px solid #7f8c8d;
        font-family: 'Segoe UI', Arial, sans-serif;
        color: #ecf0f1;
        font-size: 13px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.4);
    ">
        <b>Kavşak Durumu</b><br>
        <span style="color:#2ecc71;">● Yeşil Marker</span> → Akıcı<br>
        <span style="color:#e74c3c;">● Kırmızı Marker</span> → Sıkışık<br>
        <span style="color:#3498db;">- - - Kesikli Çizgi</span> → D200 Hattı<br>
        <span style="font-size:11px;color:#95a5a6;">
            Kriter: Hız &lt; Serbest Akış × %80<br>
            Sıkışık kavşaklarda alternatif rota önerilir
        </span>
    </div>
    """
    harita.get_root().html.add_child(folium.Element(lejant_html))

    return harita


# ============================================================================
# ANA FONKSİYON
# ============================================================================

def main():
    """
    Programın giriş noktası.
    Sırasıyla: anahtar kontrolü → veri toplama → harita üretimi → HTML kayıt.
    """
    print("\n" + "=" * 65)
    print("  🏙️  ANKARA D200 KRİTİK KAVŞAK TRAFİK HARİTASI (MVP)")
    print("=" * 65 + "\n")

    # 1) API anahtarlarını doğrula
    api_anahtarlarini_kontrol_et()

    # 2) Tüm kavşaklar için veri topla ve karar algoritmasını uygula
    kavsaklar_sonuc = verileri_topla_ve_analiz_et()

    # 3) Folium haritasını oluştur
    harita = harita_olustur(kavsaklar_sonuc)

    # 4) HTML dosyasına kaydet
    dosya_adi = "ankara_trafik_haritasi.html"
    harita.save(dosya_adi)

    print(f"\n{'=' * 65}")
    print(f"  ✅ Harita başarıyla oluşturuldu!")
    print(f"  📄 Dosya: {os.path.abspath(dosya_adi)}")
    print(f"  🌐 Tarayıcınızda açmak için dosyaya çift tıklayın.")
    print(f"{'=' * 65}\n")


# --- Script doğrudan çalıştırıldığında main() başlat ---
if __name__ == "__main__":
    main()
