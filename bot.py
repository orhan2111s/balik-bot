import time
import threading
import requests
import telebot

# --- AYARLAR ---
TOKEN = "8245923172:AAFasi-hDWdRQtSp5iEENqFjM2RdXKDK6Nk"
GRUP_ID = "-1003385313491"
SAHSI_ID = "1585351156"
bot = telebot.TeleBot(TOKEN)

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
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=True&hourly=surface_pressure,cloudcover,precipitation,temperature_2m&models=best_match"
        res = requests.get(url, timeout=15).json()
        cw = res['current_weather']
        
        try:
            m_url = f"https://marine-api.open-meteo.com/v1/marine?latitude={lat}&longitude={lon}&current=wave_height,ocean_current_velocity"
            m_res = requests.get(m_url, timeout=15).json()
            dalga = m_res['current']['wave_height']
            akinti = m_res['current']['ocean_current_velocity'] * 1.94384 
        except:
            dalga, akinti = 0.25, 1.1

        return {
            "hiz": cw['windspeed'], "yon": ruzgar_yonu(cw['winddirection']),
            "dalga": round(dalga, 2), "isi": cw['temperature'],
            "basinc": res['hourly']['surface_pressure'][0],
            "yagis": "Yok" if res['hourly']['precipitation'][0] == 0 else "Var",
            "akinti": round(akinti, 1), "bulut": res['hourly']['cloudcover'][0]
        }
    except: return None

def rapor_olustur(hedef_id):
    saat = time.strftime('%d.%m.%Y - %H:%M')
    
    # --- 1. PARÇA ---
    msg1 = f"🚨 *BALIK SEANSI ANALİZİ (1/2)*\n🗓 {saat}\n"
    msg1 += "───────────────────\n"
    for m, c in MERALAR_1.items():
        d = veri_cek(c[0], c[1])
        if d:
            msg1 += f"📍 *{m}:* {d['hiz']}km/h {d['yon']} | 🌊 {d['dalga']}mt | 🌡 {d['isi']}°C\n"
    
    try:
        bot.send_message(hedef_id, msg1, parse_mode="Markdown")
        print(f"1. mesaj {hedef_id} adresine gitti.")
        time.sleep(3) # Telegramı yormamak için bekletme
        
        # --- 2. PARÇA ---
        msg2 = f"🚨 *BALIK SEANSI ANALİZİ (2/2)*\n───────────────────\n"
        for m, c in MERALAR_2.items():
            d = veri_cek(c[0], c[1])
            if d:
                msg2 += f"📍 *{m}:* {d['hiz']}km/h {d['yon']} | 🌊 {d['dalga']}mt | 🌡 {d['isi']}°C\n"
        
        msg2 += "\n© Balık Seansı"
        bot.send_message(hedef_id, msg2, parse_mode="Markdown")
        print(f"2. mesaj {hedef_id} adresine gitti.")
    except Exception as e:
        print(f"HATA OLUŞTU: {e}")

@bot.message_handler(func=lambda m: m.text and m.text.lower() == "hava durumu")
def manuel(message):
    bot.reply_to(message, "⏳ İstasyonlara bağlanılıyor...")
    rapor_olustur(message.chat.id)

def dongu():
    # Başlarken bir tane fırlat
    rapor_olustur(GRUP_ID)
    rapor_olustur(SAHSI_ID)
    while True:
        time.sleep(10800)
        rapor_olustur(GRUP_ID)

if __name__ == "__main__":
    threading.Thread(target=dongu, daemon=True).start()
    print("Bot aktif! Grubu ve seni dinliyor...")
    bot.infinity_polling(timeout=20)
