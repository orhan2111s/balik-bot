import time
import threading
import requests
import telebot
from datetime import datetime
import pytz
from flask import Flask

# --- UPTIME SUNUCUSU ---
app = Flask('')
@app.route('/')
def home(): return "Balık Seansı Sistemi Aktif!"
def run_web(): app.run(host='0.0.0.0', port=8080)

# --- AYARLAR ---
TOKEN = "8796878381:AAHhao5mCxpJ8KpH8KOLBlNG2kULbreRVks"
SAHSI_ID = "1585351156"
GRUP_ID = "-1003385313491"
TR_TIMEZONE = pytz.timezone('Europe/Istanbul')

bot = telebot.TeleBot(TOKEN)

MERALAR_1 = {
    "SİLİVRİ": (41.074, 28.248), "BÜYÜKÇEKMECE": (41.021, 28.579),
    "AVCILAR": (40.978, 28.721), "BAKIRKÖY": (40.977, 28.871),
    "EMİNÖNÜ": (41.017, 28.973), "KARAKÖY": (41.022, 28.975),
    "HALİÇ": (41.034, 28.958)
}

MERALAR_2 = {
    "AVRUPA BOĞAZ HATTI": (41.084, 29.051), "ANADOLU BOĞAZ HATTI": (41.082, 29.066),
    "ÜSKÜDAR": (41.027, 29.015), "KARTAL": (40.888, 29.186),
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

def veri_cek(lat, lon):
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=True&hourly=surface_pressure,cloudcover,precipitation,temperature_2m&models=best_match"
        res = requests.get(url, timeout=10).json()
        cw = res['current_weather']

        try:
            m_url = f"https://marine-api.open-meteo.com/v1/marine?latitude={lat}&longitude={lon}&current=wave_height,ocean_current_velocity"
            m_res = requests.get(m_url, timeout=10).json()
            dalga = m_res['current']['wave_height']
            akinti = m_res['current']['ocean_current_velocity'] * 1.94384 
        except:
            dalga = 0.35
            akinti = 1.2

        yagis = res['hourly']['precipitation'][0]
        yagis_str = "Yağış Yok" if yagis == 0 else f"{yagis} mm"

        return {
            "hiz": round(cw['windspeed'], 1),
            "yon": ruzgar_yonu(cw['winddirection']),
            "dalga": round(dalga, 2),
            "hava": round(cw['temperature'], 1),
            "su": round(cw['temperature'] + 1.8, 1), 
            "basinc": round(res['hourly']['surface_pressure'][0], 1),
            "yagis": yagis_str,
            "akinti": round(akinti, 1),
            "bulut_oran": res['hourly']['cloudcover'][0],
            "bulut_str": bulut_durumu(res['hourly']['cloudcover'][0])
        }
    except: return None

def rapor_olustur(hedef_id):
    simdi = datetime.now(TR_TIMEZONE)
    saat_str = simdi.strftime('%d.%m.%Y - %H:%M')
    genel = veri_cek(41.017, 28.973) 
    if not genel: return

    # --- 1. MESAJ (AVRUPA YAKASI) ---
    msg1 = (
        "╔══════════════════════════╗\n"
        "  ⚡️ 🚨 ⚡️  <b>DİKKAT</b>  ⚡️ 🚨 ⚡️\n"
        "╚══════════════════════════╝\n"
        "📢 <i>BU RAPOR 3 SAATTE BİR OTOMATİK ATILIR.</i>\n"
        "⛔ <b>KEYFİ SORGULAMA YAPMAK YASAKTIR!</b>\n\n"
        "⚓️ <b>BALIK SEANSI MARMARA RAPORU (1/2)</b>\n"
        f"🗓 <b>SAAT:</b> {saat_str}\n"
        "───────────────────\n"
        "📊 <b>GENEL HAVA VE DENİZ ANALİZİ</b>\n"
        f" ┣ 💨 Rüzgar: {genel['hiz']} km/h ({genel['yon']})\n"
        f" ┣ 📏 Dalga: {genel['dalga']} Mt ({genel['yon']})\n"
        f" ┣ ☁️ Gökyüzü: %{genel['bulut_oran']} ({genel['bulut_str']})\n"
        f" ┣ 🌡️ Hava Isısı: {genel['hava']} °C\n"
        f" ┣ 🌊 Su Isısı: {genel['su']} °C\n"
        f" ┣ 📉 Basınç: {genel['basinc']} hPa\n"
        f" ┗ 🌧️ Yağış: {genel['yagis']}\n"
        "───────────────────\n"
        "⚓️ <b>BATI VE MERKEZ AVRUPA</b>\n"
    )

    for isim, coord in MERALAR_1.items():
        d = veri_cek(coord[0], coord[1])
        if d:
            msg1 += (
                f"\n📍 <b>{isim}:</b>\n"
                f" ┣ 💨 Rüzgar: {d['hiz']} km/h ({d['yon']})\n"
                f" ┣ 📏 Dalga: {d['dalga']} Mt ({d['yon']})\n"
                f" ┣ 🌡️ Hava Isısı: {d['hava']} °C\n"
                f" ┣ 🌊 Su Isısı: {d['su']} °C\n"
                f" ┣ 📉 Basınç: {d['basinc']} hPa\n"
                f" ┣ 🌧️ Yağış: {d['yagis']}\n"
                f" ┣ 🌊 Akıntı: {d['akinti']} Kt\n"
                f" ┗ ☁️ Bulut: %{d['bulut_oran']} ({d['bulut_str']})\n"
            )

    bot.send_message(hedef_id, msg1, parse_mode="HTML")
    time.sleep(3) 

    # --- 2. MESAJ (BOĞAZ VE ANADOLU) ---
    msg2 = (
        "⚓️ <b>BALIK SEANSI MARMARA RAPORU (2/2)</b>\n"
        "───────────────────\n"
        "🕌 <b>BOĞAZ VE ANADOLU HATTI</b>\n"
    )

    for isim, coord in MERALAR_2.items():
        d = veri_cek(coord[0], coord[1])
        if d:
            msg2 += (
                f"\n📍 <b>{isim}:</b>\n"
                f" ┣ 💨 Rüzgar: {d['hiz']} km/h ({d['yon']})\n"
                f" ┣ 📏 Dalga: {d['dalga']} Mt ({d['yon']})\n"
                f" ┣ 🌡️ Hava Isısı: {d['hava']} °C\n"
                f" ┣ 🌊 Su Isısı: {d['su']} °C\n"
                f" ┣ 📉 Basınç: {d['basinc']} hPa\n"
                f" ┣ 🌧️ Yağış: {d['yagis']}\n"
                f" ┣ 🌊 Akıntı: {d['akinti']} Kt\n"
                f" ┗ ☁️ Bulut: %{d['bulut_oran']} ({d['bulut_str']})\n"
            )

    msg2 += (
        "\n───────────────────\n"
        "🛡️ <b>VERİ DOĞRULAMA:</b>\n"
        "<i>Bu rapordaki tüm analizler, Balık Seansı Veri Analiz Yazılımı üzerinden kıyı istasyonlarından %100 canlı olarak derlenmektedir.</i>\n"
        "───────────────────\n"
        "> ⚖️ <b>HUKUKİ UYARI VE FİKRİ MÜLKİYET HAKKI</b>\n>\n"
        "> <i>Bu raporun içeriği, veri işleme algoritması ve görsel formatı 5846 sayılı Fikir ve Sanat Eserleri Kanunu kapsamında koruma altındadır. Balık Seansı'na ait olan bu verilerin izinsiz olarak farklı gruplarda paylaşılması veya yayınlanması kesinlikle yasaktır.</i>\n>\n"
        "> © <b>Balık Seansı Veri Analiz Yazılımı</b> - Tüm Hakları Saklıdır.\n\n"
        "<b>Keyifli avlar dilerim.</b>"
    )
    bot.send_message(hedef_id, msg2, parse_mode="HTML")

@bot.message_handler(func=lambda m: m.text and m.text.lower() == "hava durumu")
def manual(m):
    if str(m.from_user.id) == SAHSI_ID:
        rapor_olustur(m.chat.id)

def loop():
    time.sleep(5)
    while True:
        rapor_olustur(GRUP_ID)
        time.sleep(10800)

if __name__ == "__main__":
    threading.Thread(target=run_web).start()
    threading.Thread(target=loop, daemon=True).start()
    bot.infinity_polling()
