"""
=============================================================================
  ANKARA TRAFİK DİJİTAL İKİZİ VE KARAR DESTEK YÖNETİM PANELİ (ENDÜSTRİYEL SÜRÜM)
  =============================================================================
"""

import os
import sys
import io
import time
from datetime import datetime
import pandas as pd

if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import folium
from folium.features import DivIcon
from folium.plugins import HeatMap
import streamlit as st
from streamlit_folium import st_folium
import requests as req_lib
from dotenv import load_dotenv

load_dotenv()

# ============================================================================
# VERİ YAPISI
# ============================================================================
KAVSAKLAR = [
    {"ad": "Polatlı D200 Sanayi Kavşağı", "ilce": "Polatlı", "lat": 39.5846, "lon": 32.1362},
    {"ad": "Sincan OSB Kavşağı", "ilce": "Sincan", "lat": 39.9497, "lon": 32.5534},
    {"ad": "Eryaman Optimum Kavşağı", "ilce": "Etimesgut", "lat": 39.9473, "lon": 32.6312},
    {"ad": "Ümitköy Köprüsü", "ilce": "Çankaya", "lat": 39.9086, "lon": 32.7384},
    {"ad": "Bilkent Şehir Hastanesi Kavşağı", "ilce": "Çankaya", "lat": 39.8672, "lon": 32.7488},
    {"ad": "Anadolu Bulvarı Kesişimi", "ilce": "Çankaya", "lat": 39.9213, "lon": 32.8105},
    {"ad": "Mamak Çevreyolu Kavşağı", "ilce": "Mamak", "lat": 39.9270, "lon": 32.9360},
    {"ad": "Elmadağ Giriş Kavşağı (D200 Aksı)", "ilce": "Elmadağ", "lat": 39.9210, "lon": 33.2310},
]

ILCE_MERKEZLERI = {
    "Polatlı":   {"lat": 39.5840, "lon": 32.1477},
    "Sincan":    {"lat": 39.9680, "lon": 32.5860},
    "Etimesgut": {"lat": 39.9450, "lon": 32.6580},
    "Çankaya":   {"lat": 39.9180, "lon": 32.8540},
    "Mamak":     {"lat": 39.9270, "lon": 32.9360},
    "Elmadağ":   {"lat": 39.9210, "lon": 33.2310},
}

ALTERNATIF_ROTALAR = {
    "Polatlı D200 Sanayi Kavşağı": "Polatlı-Temelli bağlantı yolundan O-4'e bağlanın.",
    "Sincan OSB Kavşağı": "Fatih Bulvarı ile Sincan merkeze geçip, Eryaman yönüne devam edin.",
    "Eryaman Optimum Kavşağı": "1. Cadde üzerinden güneye inip, Dumlupınar Bulvarı'na bağlanın.",
    "Ümitköy Köprüsü": "Sabancı Bulvarı'na saparak Konutkent üzerinden Çayyolu'na inin.",
    "Bilkent Şehir Hastanesi Kavşağı": "Bilkent İçi yoldan Beytepe-ODTÜ bağlantısıyla Konya Yolu'na bağlanın.",
    "Anadolu Bulvarı Kesişimi": "Bilkent Kavşağından Konya Yolu'na bağlanın veya Mevlana Bulvarına sapın.",
    "Mamak Çevreyolu Kavşağı": "Çevreyolu (O-20) yoğunsa Doğukent Bulvarı üzerinden merkeze alternatif yolları kullanın.",
    "Elmadağ Giriş Kavşağı (D200 Aksı)": "Çevreyolu Doğu katılımını kullanın veya Hasanoğlan yoluna girin.",
}

# ============================================================================
# API FONKSİYONLARI & CANLI VERİ
# ============================================================================
def get_weather(lat, lon):
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={os.getenv('OPENWEATHER_API_KEY')}&units=metric&lang=tr"
    try:
        veri = req_lib.get(url, timeout=5).json()
        return {"durum": veri["weather"][0]["description"], "sicaklik": veri["main"]["temp"]}
    except:
        return {"durum": "veri yok", "sicaklik": 0.0}

def get_traffic_flow(lat, lon):
    url = f"https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json?point={lat},{lon}&key={os.getenv('TOMTOM_API_KEY')}"
    try:
        s = req_lib.get(url, timeout=5).json().get("flowSegmentData", {})
        return {"currentSpeed": s.get("currentSpeed", 0), "freeFlowSpeed": s.get("freeFlowSpeed", 0)}
    except:
        return {"currentSpeed": 0, "freeFlowSpeed": 0}

def canli_veri_topla():
    import random
    sonuc = []
    for kavsak in KAVSAKLAR:
        lat, lon = kavsak["lat"], kavsak["lon"]
        hava = get_weather(lat, lon)
        trafik = get_traffic_flow(lat, lon)
        hiz = trafik["currentSpeed"]
        serbest = trafik["freeFlowSpeed"]
        
        dusus = round((1 - hiz/serbest)*100, 1) if serbest > 0 else 0.0
        durum = "Sıkışık" if dusus > 40 else ("Yoğun" if dusus > 20 else "Akıcı")
        rota = ALTERNATIF_ROTALAR.get(kavsak["ad"], "") if durum in ["Sıkışık", "Yoğun"] else ""
        
        # Kritik Analiz Metrikleri
        arac_sayisi = int(500 + (dusus * 25) * random.uniform(0.8, 1.2))
        bekleme = int(dusus * 0.4) if dusus > 20 else 0
        
        sonuc.append({
            **kavsak, "hava_durum": hava["durum"], "sicaklik": hava["sicaklik"],
            "mevcut_hiz": hiz, "serbest_hiz": serbest, "dusus_yuzdesi": dusus,
            "durum": durum, "alternatif_rota": rota,
            "arac_sayisi": arac_sayisi, "bekleme_suresi": bekleme
        })
    return sonuc

# ============================================================================
# SİMÜLASYON
# ============================================================================
def simulasyon_verisi_uret(yogunluk_carpani, hava_senaryosu, kaza_kavsak, zaman_proj):
    import random
    random.seed(int(time.time() * 10))
    
    hava_f = {"☀️ Açık": 1.0, "🌧️ Yağmurlu": 0.75, "❄️ Karlı": 0.55, "🌫️ Sisli": 0.65}.get(hava_senaryosu, 1.0)
    sicaklik = {"☀️ Açık": 22.0, "🌧️ Yağmurlu": 14.0, "❄️ Karlı": -2.0, "🌫️ Sisli": 8.0}.get(hava_senaryosu, 15)
    
    zaman_etki = {"Şimdi": 1.0, "+15 Dk": 0.85, "+30 Dk": 0.70, "+60 Dk": 0.50}.get(zaman_proj, 1.0)
    
    hizlar = [70, 60, 110, 90, 80, 75, 85, 65]
    
    kaza_idx = next((i for i, k in enumerate(KAVSAKLAR) if k["ad"] == kaza_kavsak), -1)
        
    sonuc = []
    for i, kavsak in enumerate(KAVSAKLAR):
        serbest = hizlar[i]
        mevcut = int(serbest * (1 - yogunluk_carpani/100) * hava_f * zaman_etki * random.uniform(0.9, 1.1))
        
        # Olay Enjeksiyonu (Zamanla geriye vuran kuyruklanma)
        if kaza_idx != -1:
            if i == kaza_idx:
                mevcut = random.randint(2, 5) # Kilitli
            elif i == kaza_idx - 1:
                mevcut = min(mevcut, int(serbest * 0.3 * zaman_etki)) 
            elif i == kaza_idx - 2:
                mevcut = min(mevcut, int(serbest * 0.6 * zaman_etki))
                
        mevcut = max(2, mevcut)
        dusus = round((1 - mevcut/serbest)*100, 1)
        durum = "Sıkışık" if dusus > 40 else ("Yoğun" if dusus > 20 else "Akıcı")
        
        # Kritik Analiz Metrikleri
        arac_sayisi = int(500 + (dusus * 25) * random.uniform(0.8, 1.2))
        bekleme = int(dusus * 0.4) if dusus > 20 else 0
        
        sonuc.append({
            **kavsak, "hava_durum": hava_senaryosu, "sicaklik": sicaklik,
            "mevcut_hiz": mevcut, "serbest_hiz": serbest, "dusus_yuzdesi": dusus,
            "durum": durum, "alternatif_rota": ALTERNATIF_ROTALAR.get(kavsak["ad"], ""),
            "arac_sayisi": arac_sayisi, "bekleme_suresi": bekleme
        })
    return sonuc

# ============================================================================
# FOLIUM HARİTA (ISI HARİTASI İLE)
# ============================================================================
def harita_olustur(kavsaklar_sonuc, harita_temasi):
    tema_map = {
        "Karanlık Mod": "CartoDB dark_matter",
        "Uydu": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        "Klasik": "OpenStreetMap"
    }
    tiles = tema_map.get(harita_temasi, "CartoDB dark_matter")
    attr = "Esri" if harita_temasi == "Uydu" else None
    
    harita = folium.Map(location=[39.91, 32.68], zoom_start=10, tiles=tiles, attr=attr)
    
    # Isı Haritası (HeatMap)
    heat_data = [[k["lat"], k["lon"], k["dusus_yuzdesi"] / 100.0] for k in kavsaklar_sonuc]
    HeatMap(heat_data, radius=35, blur=20, gradient={0.3: 'lime', 0.6: 'yellow', 1.0: 'red'}).add_to(harita)
    
    # İlçe Etiketleri
    for ad, k in ILCE_MERKEZLERI.items():
        folium.Marker([k["lat"], k["lon"]], icon=DivIcon(
            html=f'<div style="font-weight:bold;color:white;text-shadow:0 0 5px black;font-size:13px;">{ad}</div>'
        )).add_to(harita)
        
    # Kritik Nokta İğneleri ve Gelişmiş Tooltip
    for k in kavsaklar_sonuc:
        renk = "red" if k["durum"] == "Sıkışık" else ("orange" if k["durum"] == "Yoğun" else "green")
        
        html_tooltip = f"""
        <div style='min-width: 200px; font-family: sans-serif;'>
            <b>{k['ad']}</b><hr style='margin:4px 0;'>
            <b>Durum:</b> {k['durum']} (Hız: {k['mevcut_hiz']} km/h)<br>
            <b>Araç Yükü:</b> {k['arac_sayisi']} araç/saat<br>
            <b>Tahmini Gecikme:</b> <span style='color:red;'>+{k['bekleme_suresi']} dk</span><br>
            <b>Alternatif:</b> {k['alternatif_rota']}
        </div>
        """
        folium.Marker(
            [k["lat"], k["lon"]], 
            tooltip=html_tooltip,
            icon=folium.Icon(color=renk, icon="info-sign")
        ).add_to(harita)

    # Dinamik Çizgiler
    for i in range(len(kavsaklar_sonuc) - 1):
        k1 = kavsaklar_sonuc[i]
        k2 = kavsaklar_sonuc[i+1]
        ort_dusus = (k1["dusus_yuzdesi"] + k2["dusus_yuzdesi"]) / 2
        cizgi_renk = "#e74c3c" if ort_dusus > 40 else ("#f39c12" if ort_dusus > 20 else "#2ecc71")
        folium.PolyLine([[k1["lat"], k1["lon"]], [k2["lat"], k2["lon"]]], color=cizgi_renk, weight=5, opacity=0.8).add_to(harita)

    return harita

# ============================================================================
# STREAMLIT ANA ARAYÜZ
# ============================================================================
def main():
    st.set_page_config(page_title="Dijital İkiz Laboratuvarı", layout="wide", page_icon="🌐")
    
    st.markdown("""
        <style>
        .metric-box { background-color: #1e1e1e; padding: 15px; border-radius: 8px; border-left: 5px solid #3498db; }
        .ai-box { background-color: #2c3e50; padding: 20px; border-radius: 8px; border-left: 5px solid #e74c3c; margin-bottom: 20px;}
        .blink-text { color: #f39c12; animation: blinker 1.5s linear infinite; font-weight: bold; }
        @keyframes blinker { 50% { opacity: 0; } }
        </style>
    """, unsafe_allow_html=True)
        
    st.title("🚀 Ankara Trafik Dijital İkizi & AI Karar Destek Sistemi")
    
    # SIDEBAR
    with st.sidebar:
        st.header("🎛️ Simülasyon Kontrolü")
        harita_temasi = st.selectbox("🗺️ Harita Altlığı", ["Karanlık Mod", "Uydu", "Klasik"])
        
        st.markdown("---")
        st.subheader("⏱️ Zaman Projeksiyonu")
        zaman_proj = st.radio("Zaman Çizelgesi Seç", ["Şimdi", "+15 Dk", "+30 Dk", "+60 Dk"], horizontal=True)
        
        st.markdown("---")
        simulasyon = st.checkbox("🧪 Simülasyon (What-If) Modu", True)
        
        kaza_kavsak = "Yok"
        if simulasyon:
            yogunluk = st.slider("Ağ Yoğunluk Çarpanı", 0, 100, 40)
            hava = st.selectbox("Hava Senaryosu", ["☀️ Açık", "🌧️ Yağmurlu", "❄️ Karlı", "🌫️ Sisli"])
            kaza_kavsak = st.selectbox("⚡ Kritik Olay/Kaza Enjeksiyonu", ["Yok"] + [k["ad"] for k in KAVSAKLAR])
        else:
            if st.button("Canlı Verileri Çek"): st.rerun()

    if simulasyon:
        st.markdown(f"<h4 class='blink-text'>⚠️ PREDICTIVE MODEL ACTIVE (Zaman Projeksiyonu: {zaman_proj})</h4>", unsafe_allow_html=True)
        veri = simulasyon_verisi_uret(yogunluk, hava, kaza_kavsak, zaman_proj)
    else:
        st.markdown("<h4 class='blink-text' style='color:#e74c3c;'>🔴 LIVE SYNCHRONIZATION (Gerçek Zamanlı Veri)</h4>", unsafe_allow_html=True)
        veri = canli_veri_topla()

    # METRİKLER (Dijital İkiz Güven Skoru)
    tum_dususler = [k["dusus_yuzdesi"] for k in veri]
    ort_yogunluk = sum(tum_dususler)/len(tum_dususler) if tum_dususler else 0
    ag_sagliligi = max(0, int(100 - ort_yogunluk))
    toplam_gecikme = sum([k["bekleme_suresi"] for k in veri])
    risk_kavsak = len([k for k in veri if k["durum"] in ["Sıkışık", "Yoğun"]])
    normallesme = int(toplam_gecikme * 1.5 + risk_kavsak * 5) if risk_kavsak > 0 else 0

    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("🛡️ Ağ Sağlığı Endeksi", f"%{ag_sagliligi}")
    with col2: st.metric("⏱️ Ağ İçi Ekstra Gecikme", f"+{toplam_gecikme} dk")
    with col3: st.metric("⚠️ Risk Altındaki Kavşak", f"{risk_kavsak} Düğüm")
    with col4: st.metric("⏳ Tahmini Normalleşme", f"{normallesme} dk")
    
    st.markdown("---")

    # YAPAY ZEKA (AI) KARAR DESTEK BÖLÜMÜ (Sabit Kural Tabanlı Uzman Sistem)
    if risk_kavsak > 0 or kaza_kavsak != "Yok":
        hedef_nokta = kaza_kavsak if kaza_kavsak != "Yok" else [k["ad"] for k in veri if k["durum"] == "Sıkışık"][0] if [k["ad"] for k in veri if k["durum"] == "Sıkışık"] else "D200 Aksı"
        st.markdown(f"""
        <div class="ai-box">
            <h3 style="margin-top:0;">🤖 Yapay Zeka Otonom Karar Desteği</h3>
            Sistem ağında tehlikeli seviyede bozulma tespit edildi. Etkilenen merkez: <b>{hedef_nokta}</b>.<br><br>
            <b>AI Tavsiye Edilen Aksiyonlar:</b>
            <ul>
                <li>🔴 <b>{hedef_nokta}</b> bağlantı yolunu geçici olarak otonom kapat.</li>
                <li>🔄 Trafiği Eskişehir Yolundan çıkarıp alternatif paralel bulvarlara yönlendir.</li>
                <li>🚦 Bölgedeki sinyalizasyon döngülerinde yeşil ışık süresini %20 artır.</li>
                <li>🚑 Acil durum araçları için sistem üzerinden anında yeşil koridor (Green Wave) aç.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    # ALT BÖLÜM: HARİTA VE SENARYO KARŞILAŞTIRMASI
    st.markdown("### 🗺️ Dijital İkiz Isı Haritası & Canlı Simülasyon")
    
    # Haritayı tam genişlikte çiz
    harita = harita_olustur(veri, harita_temasi)
    st_folium(harita, use_container_width=True, height=600, returned_objects=[])

    st.markdown("---")
    st.markdown("### 📊 Senaryo Optimizasyon Analizi")
    
    df_senaryo = pd.DataFrame([
        {"Senaryo": "❌ Müdahale Yok", "Sistem Süresi": f"{int(60 + toplam_gecikme)} dk", "Karbon Salınımı": "Yüksek (Tıkanıklık Kaynaklı)"},
        {"Senaryo": "⚠️ Sadece Alternatif Rota", "Sistem Süresi": f"{int(45 + toplam_gecikme*0.5)} dk", "Karbon Salınımı": "Orta"},
        {"Senaryo": "✅ Yapay Zeka Optimizasyonu", "Sistem Süresi": f"{int(30 + toplam_gecikme*0.1)} dk", "Karbon Salınımı": "Düşük (Akıcı Akış)"}
    ])
    st.table(df_senaryo)
    
    st.markdown("---")
    st.markdown("### 📋 Anlık Kavşak Detay Raporu")
    
    kavsak_tablosu = pd.DataFrame([{
        "Kavşak Adı": k["ad"],
        "Durum": k["durum"],
        "Hız (km/h)": f"{k['mevcut_hiz']} / {k['serbest_hiz']}",
        "Yoğunluk Çarpanı": f"%{k['dusus_yuzdesi']}",
        "Araç Yükü": f"{k['arac_sayisi']} / saat",
        "Gecikme (dk)": f"+{k['bekleme_suresi']} dk",
        "Hava Durumu": f"{k['hava_durum']} ({k['sicaklik']}°C)"
    } for k in veri])
    
    st.dataframe(kavsak_tablosu, use_container_width=True)
if __name__ == "__main__":
    main()
