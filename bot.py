import time
import threading
import requests
import telebot
import os
from http.server import HTTPServer, BaseHTTPRequestHandler

# --- AYARLAR ---
TOKEN = "8245923172:AAFasi-hDWdRQtSp5iEENqFjM2RdXKDK6Nk"
GRUP_ID = "-1003385313491"
SAHSI_ID = "1585351156"
bot = telebot.TeleBot(TOKEN)

# Render'ın "Port yok" diye ağlamasını kesen bölüm
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
    "AVR. BOĞAZ": (41.084, 29.051), "AND. BOĞAZ": (41.082, 29.066),
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

def veri_cek(lat, lon):
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=True&hourly=surface_pressure,temperature_2m"
        res = requests.get(url, timeout=10).json()
        cw = res['current_weather']
        return {"hiz": cw['windspeed'], "yon": ruzgar_yonu(cw['winddirection']), "isi": cw['temperature'], "basinc": res['hourly']['surface_pressure'][0]}
    except: return None

def rapor_olustur(hedef_id):
    saat = time.strftime('%d.%m.%Y - %H:%M')
    msg = f"🚨 *BALIK SEANSI ANALİZİ*\n🗓 {saat}\n───────────────────\n"
    for m, c in {**MERALAR_1, **MERALAR_2}.items():
        d = veri_cek(c[0], c[1])
        if d: msg += f"📍 *{m}:* {d['hiz']}km/h {d['yon']} | 🌡 {d['isi']}°C\n"
    
    try:
        bot.send_message(hedef_id, msg + "\n© Balık Seansı", parse_mode="Markdown")
    except Exception as e: print(f"Hata: {e}")

@bot.message_handler(func=lambda m: m.text and m.text.lower() == "hava durumu")
def manuel(message):
    bot.reply_to(message, "⏳ Veriler çekiliyor...")
    rapor_olustur(message.chat.id)

def dongu():
    while True:
        rapor_olustur(GRUP_ID)
        rapor_olustur(SAHSI_ID)
        time.sleep(10800)

if __name__ == "__main__":
    threading.Thread(target=run_health_server, daemon=True).start()
    threading.Thread(target=dongu, daemon=True).start()
    print("Bot aktif!")
    bot.infinity_polling()
