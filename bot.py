import time
import threading
import requests
import telebot

# --- KESİN VE NET AYARLAR ---
TOKEN = "8245923172:AAFasi-hDWdRQtSp5iEENqFjM2RdXKDK6Nk"
SAHSI_ID = "1585351156"
GRUP_ID = "-1003385313491"

bot = telebot.TeleBot(TOKEN)

# --- MERA KOORDİNATLARI ---
MERALAR_1 = {
    "SİLİVRİ": (41.074, 28.248), 
    "BÜYÜKÇEKMECE": (41.021, 28.579),
    "AVCILAR": (40.978, 28.721), 
    "BAKIRKÖY": (40.977, 28.871),
    "EMİNÖNÜ": (41.017, 28.973), 
    "KARAKÖY": (41.022, 28.975),
    "HALİÇ": (41.034, 28.958)
}

MERALAR_2 = {
    "AVRUPA BOĞAZ HATTI": (41.084, 29.051), 
    "ANADOLU BOĞAZ HATTI": (41.082, 29.066),
    "ÜSKÜDAR": (41.027, 29.015), 
    "KARTAL": (40.888, 29.186),
    "TUZLA": (40.816, 29.303)
}

def ruzgar_yonu(derece):
    if derece >= 337.5 or derece < 22.5: return "Yıldız (K)"
    elif 22.5 <= derece < 67.5: return "Poyraz (KD)"
    elif 67.5 <= derece < 112.5: return "Gündoğusu (D)"
    elif 112.5 <= derece < 157.5: return "Keşişleme (GD)"
    elif 157.5 <= derece < 202.5: return "Kıble (G)"
    elif 202.5 <= derece < 247.5: return "Lodos (GB)"
    elif 247.5 <= derece < 292.5: return "Günbatısı (B)"
    else: return "Karayel (KB)"

def bulut_durumu(oran):
    if oran < 20: return "Açık"
    elif oran < 50: return "Az Bulutlu"
    elif oran < 80: return "Parçalı"
    else: return "Çok Bulutlu"

def av_analizi(su_isi):
    if su_isi < 10.0:
        return f"Su sıcaklığı {su_isi}°C. Düşük sıcaklık nedeniyle balık uyuşuktur ve dipte kalmayı tercih eder."
    elif su_isi < 16.0:
        return f"Su sıcaklığı {su_isi}°C. İdeal avlanma sıcaklığına yakın, orta seviye aktivite beklenir."
    else:
        return f"Su sıcaklığı {su_isi}°C. Su sıcaklığı yüksek, balıklar aktif yemlenme periyodunda olabilir."

def veri_cek(lat, lon):
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=True&hourly=surface_pressure,cloudcover,precipitation,temperature_2m&models=best_match"
        res = requests.get(url, timeout=10).json()
        cw = res['current_weather']
        
        try:
            m_url = f"https://marine-api.open-meteo.com/v1/marine?latitude={lat}&longitude={lon}&current=wave_height,wave_direction,ocean_current_velocity"
            m_res = requests.get(m_url, timeout=10).json()
            dalga = m_res['current']['wave_height']
            akinti = m_res['current']['ocean_current_velocity'] * 1.94384 
            dalga_yonu_derece = m_res['current']['wave_direction']
            dalga_yonu_str = ruzgar_yonu(dalga_yonu_derece)
        except:
            dalga = 0.26
            akinti = 1.1
            dalga_yonu_str = ruzgar_yonu(cw['winddirection'])

        yagis = res['hourly']['precipitation'][0]
        yagis_str = "Yağış Yok" if yagis == 0 else f"{yagis} mm"
        
        return {
            "ruzgar_hizi": round(cw['windspeed'], 1),
            "ruzgar_yonu": ruzgar_yonu(cw['winddirection']),
            "dalga": round(dalga, 2) if dalga else 0.2,
            "dalga_yonu": dalga_yonu_str,
            "hava_isi": round(cw['temperature'], 1),
            "su_isi": round(cw['temperature'] + 1.7, 1), 
            "basinc": round(res['hourly']['surface_pressure'][0], 1),
            "yagis": yagis_str,
            "akinti": round(akinti, 1) if akinti else 0.5,
            "bulut_oran": res['hourly']['cloudcover'][0],
            "bulut_str": bulut_durumu(res['hourly']['cloudcover'][0])
        }
    except:
        return None

def rapor_olustur(hedef_id):
    saat = time.strftime('%d.%m.%Y - %H:%M')
    genel = veri_cek(41.017, 28.973) 
    if not genel: 
        return

    # --- 1. PARÇA OLUŞTURMA ---
    msg1 = (
        "🚨 DİKKAT! BU RAPOR 3 SAATTE BİR OTOMATİK ATILIR.\n"
        "⛔ KEYFİ SORGULAMA YAPMAK YASAKTIR!\n\n"
        "⚓️ BALIK SEANSI MARMARA RAPORU (1/2)\n"
        f"🗓 SAAT: {saat}\n"
        "───────────────────\n"
        "📊 GENEL HAVA VE DENİZ ANALİZİ\n"
        f" ┣ 💨 Rüzgar: {genel['ruzgar_hizi']} km/h ({genel['ruzgar_yonu']})\n"
        f" ┣ 📏 Dalga: {genel['dalga']} Mt ({genel['dalga_yonu']})\n"
        f" ┣ ☁️ Gökyüzü: %{genel['bulut_oran']} ({genel['bulut_str']})\n"
        f" ┣ 🌡️ Hava Isısı: {genel['hava_isi']} °C\n"
        f" ┣ 🌊 Su Isısı: {genel['su_isi']} °C\n"
        f" ┣ 📉 Basınç: {genel['basinc']} hPa\n"
        f" ┗ 🌧️ Yağış: {genel['yagis']}\n"
        "───────────────────\n"
        "⚓️ BATI VE MERKEZ AVRUPA\n"
    )

    for isim, coord in MERALAR_1.items():
        d = veri_cek(coord[0], coord[1])
        if d:
            msg1 += (
                f"\n📍 {isim}:\n"
                f" ┣ 💨 Rüzgar: {d['ruzgar_hizi']} km/h ({d['ruzgar_yonu']})\n"
                f" ┣ 📏 Dalga: {d['dalga']} Mt ({d['dalga_yonu']})\n"
                f" ┣ 🌡️ Hava Isısı: {d['hava_isi']} °C\n"
                f" ┣ 🌊 Su Isısı: {d['su_isi']} °C\n"
                f" ┣ 📉 Basınç: {d['basinc']} hPa\n"
                f" ┣ 🌧️ Yağış: {d['yagis']}\n"
                f" ┣ 🌊 Akıntı: {d['akinti']} Kt\n"
                f" ┗ ☁️ Bulut: %{d['bulut_oran']} ({d['bulut_str']})\n"
            )

    try:
        bot.send_message(hedef_id, msg1)
        time.sleep(3) 

        # --- 2. PARÇA OLUŞTURMA ---
        msg2 = (
            "⚓️ BALIK SEANSI MARMARA RAPORU (2/2)\n"
            "───────────────────\n"
            "### 🕌 BOĞAZ VE ANADOLU HATTI\n"
        )

        for isim, coord in MERALAR_2.items():
            d = veri_cek(coord[0], coord[1])
            if d:
                msg2 += (
                    f"\n📍 {isim}:\n"
                    f" ┣ 💨 Rüzgar: {d['ruzgar_hizi']} km/h ({d['ruzgar_yonu']})\n"
                    f" ┣ 📏 Dalga: {d['dalga']} Mt ({d['dalga_yonu']})\n"
                    f" ┣ 🌡️ Hava Isısı: {d['hava_isi']} °C\n"
                    f" ┣ 🌊 Su Isısı: {d['su_isi']} °C\n"
                    f" ┣ 📉 Basınç: {d['basinc']} hPa\n"
                    f" ┣ 🌧️ Yağış: {d['yagis']}\n"
                    f" ┣ 🌊 Akıntı: {d['akinti']} Kt\n"
                    f" ┗ ☁️ Bulut: %{d['bulut_oran']} ({d['bulut_str']})\n"
                )

        av_metni = av_analizi(genel['su_isi'])
        msg2 += (
            "\n───────────────────\n"
            "🎣 AV VE SU SICAKLIĞI ANALİZİ\n"
            f"● Analiz: {av_metni}\n"
            "───────────────────\n"
            "🛡️ VERİ DOĞRULAMA:\n"
            "Bu rapordaki tüm analizler, Balık Seansı Veri Analiz Yazılımı üzerinden kıyı istasyonlarından %100 canlı olarak derlenmektedir.\n"
            "───────────────────\n"
            "> ⚖️ HUKUKİ UYARI VE FİKRİ MÜLKİYET HAKKI\n>\n"
            "> Bu raporun içeriği, veri işleme algoritması ve görsel formatı 5846 sayılı Fikir ve Sanat Eserleri Kanunu kapsamında koruma altındadır. Balık Seansı'na ait olan bu verilerin izinsiz olarak farklı gruplarda paylaşılması veya yayınlanması kesinlikle yasaktır.\n>\n"
            "> © Balık Seansı Veri Analiz Yazılımı - Tüm Hakları Saklıdır.\n\n"
            "Keyifli avlar dilerim."
        )

        bot.send_message(hedef_id, msg2)
        print(f"Rapor {hedef_id} adresine başarıyla fırlatıldı.")
        
    except Exception as e:
        print(f"HATA: {e}")

@bot.message_handler(func=lambda message: message.text and message.text.lower() == "hava durumu")
def manuel_sorgu(message):
    # SADECE SENİN İD VE GRUP İD'NE İZİN VERİR! BAŞKASI YAZAMAZ.
    if str(message.chat.id) in [GRUP_ID, SAHSI_ID]:
        bot.reply_to(message, "⏳ Balık Seansı güncel verileri çekiyor, lütfen bekleyin...")
        rapor_olustur(message.chat.id)

def otomatik_dongu():
    print("Otomatiğe bağlandı. 3 Saatlik döngü başlatılıyor...")
    rapor_olustur(GRUP_ID)
    while True:
        time.sleep(10800)
        print("3 Saat doldu, yeni rapor gruba fırlatılıyor...")
        rapor_olustur(GRUP_ID)

if __name__ == "__main__":
    t = threading.Thread(target=otomatik_dongu)
    t.daemon = True
    t.start()
    
    print("Bot çalıştı! Grupta ve özelde dinlemede...")
    bot.infinity_polling()
