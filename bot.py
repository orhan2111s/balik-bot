import time
import threading
import requests
import telebot
import os
from http.server import HTTPServer, BaseHTTPRequestHandler

# --- SENİN ÖZEL BİLGİLERİN ---
TOKEN = "8245923172:AAFasi-hDWdRQtSp5iEENqFjM2RdXKDK6Nk"
GRUP_ID = "-1003385313491"  # Sadece bu gruba atacak
SAHSI_ID = "1585351156"    # Sadece sana atacak
bot = telebot.TeleBot(TOKEN)

# Render "Port" hatası vermesin diye küçük bir sunucu
class HealthCheck(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot Aktif")

def run_health_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheck)
    server.serve_forever()

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
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=True&hourly=surface_pressure,cloudcover,precipitation,temperature_2m"
        res = requests.get(url, timeout=15).json()
        cw = res['current_weather']
        try:
            m_url = f"https://marine-api.open-meteo.com/v1/marine?latitude={lat}&longitude={lon}&current=wave_height,ocean_current_velocity"
            m_res = requests.get(m_url, timeout=15).json()
            dalga, akinti = m_res['current']['wave_height'], m_res['current']['ocean_current_velocity'] * 1.94
        except: dalga, akinti = 0.26, 1.1
        yagis = res['hourly']['precipitation'][0]
        return {
            "hizi": cw['windspeed'], "yonu": ruzgar_yonu(cw['winddirection']),
            "dalga": round(dalga, 2), "h_isi": cw['temperature'],
            "s_isi": round(cw['temperature'] + 1.5, 1), "basinc": res['hourly']['surface_pressure'][0],
            "yagis": "Yok" if yagis == 0 else f"{yagis} mm", "akinti": round(akinti, 1),
            "b_oran": res['hourly']['cloudcover'][0], "b_str": bulut_durumu(res['hourly']['cloudcover'][0])
        }
    except: return None

def rapor_olustur(hedef_id):
    saat = time.strftime('%d.%m.%Y - %H:%M')
    # --- 1. PARÇA ---
    msg1 = (
        "🚨 DİKKAT! BU RAPOR 3 SAATTE BİR OTOMATİK ATILIR.\n"
        "⚓️ BALIK SEANSI MARMARA RAPORU (1/2)\n"
        f"🗓 SAAT: {saat}\n───────────────────\n"
    )
    for isim, coord in MERALAR_1.items():
        d = veri_cek(coord[0], coord[1])
        if d: msg1 += f"\n📍 {isim}:\n ┣ 💨 {d['hizi']} km/h ({d['yonu']})\n ┣ 📏 {d['dalga']} Mt | 🌊 {d['akinti']} Kt\n ┗ 🌡 {d['h_isi']} °C | 📉 {d['basinc']} hPa | 🌧 {d['yagis']}\n"
    
    try:
        bot.send_message(hedef_id, msg1)
        time.sleep(3)
        # --- 2. PARÇA ---
        msg2 = "⚓️ BALIK SEANSI MARMARA RAPORU (2/2)\n───────────────────\n"
        for isim, coord in MERALAR_2.items():
            d = veri_cek(coord[0], coord[1])
            if d: msg2 += f"\n📍 {isim}:\n ┣ 💨 {d['hizi']} km/h ({d['yonu']})\n ┣ 📏 {d['dalga']} Mt | 🌊 {d['akinti']} Kt\n ┗ 🌡 {d['h_isi']} °C | 📉 {d['basinc']} hPa | 🌧 {d['yagis']}\n"
        bot.send_message(hedef_id, msg2 + "\n© Balık Seansı Veri Analizi")
    except Exception as e: print(f"Hata: {e}")

@bot.message_handler(func=lambda message: message.text and message.text.lower() == "hava durumu")
def manuel(message):
    # GÜVENLİK: Sadece senin grubun veya sen yazarsan cevap verir
    if str(message.chat.id) in [GRUP_ID, SAHSI_ID]:
        bot.reply_to(message, "⏳ Veriler çekiliyor...")
        rapor_olustur(message.chat.id)

def dongu():
    rapor_olustur(GRUP_ID)
    rapor_olustur(SAHSI_ID)
    while True:
        time.sleep(10800)
        rapor_olustur(GRUP_ID)

if __name__ == "__main__":
    threading.Thread(target=run_health_server, daemon=True).start()
    threading.Thread(target=dongu, daemon=True).start()
    bot.infinity_polling()
