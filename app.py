import streamlit as st
import json
import random
import os
from datetime import datetime
import pytz

# ===================== AYARLAR =====================
TIMEZONE = pytz.timezone("Europe/Istanbul")
GUNLUK_SORU_SAYISI = 10  # Her slotta (sabah/akşam) kaç soru sorulacak

st.set_page_config(page_title="Günün Seçilmiş Soruları", page_icon="🌸")
st.title("🌸 Her 2 Dünyamı Güzelleştiren Kadına 🌸")

QUESTIONS_FILE = "questions.json"
MESSAGES_FILE = "messages.json"
USED_MESSAGES_FILE = "used_messages.json"
PROGRESS_FILE = "progress.json"
WRONG_FILE = "wrong_questions.json"

# ===================== JSON YARDIMCILAR =====================
def load_json(path, default):
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default, f, ensure_ascii=False, indent=2)
        return default
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except:
            return default

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ===================== VERİ YÜKLEME =====================
questions = load_json(QUESTIONS_FILE, [])
questions = sorted(questions, key=lambda x: x.get("id", 0))

messages = load_json(MESSAGES_FILE, [])
used_messages = load_json(USED_MESSAGES_FILE, [])
# Progress yapısını güncelledik: period_counter o anki vakitte kaç soru çözüldüğünü tutar
progress = load_json(PROGRESS_FILE, {"global_index": 0, "last_period": "", "period_counter": 0})
wrong_ids = load_json(WRONG_FILE, [])

# ===================== ZAMAN KONTROLÜ =====================
now_dt = datetime.now(TIMEZONE)
current_hour = now_dt.hour
today_str = now_dt.strftime("%Y-%m-%d")

# Slot belirleme (Sabah 08-20, Akşam 20-08)
# Hassas saat ayarı örneği (08:30 ve 18:30 için)
simdi_toplam_dakika = current_hour * 60 + now_dt.minute

sabah_baslangic = 8 * 60 + 30  # 08:30
aksam_baslangic = 18 * 60 + 30 # 18:30

if sabah_baslangic <= simdi_toplam_dakika < aksam_baslangic:
    current_slot = "sabah"
else:
    current_slot = "aksam"

period_id = f"{today_str}_{current_slot}"

# EĞER VAKİT DEĞİŞTİYSE SAYAÇLARI GÜNCELLE
if progress["last_period"] != period_id:
    progress["last_period"] = period_id
    progress["period_counter"] = 0  # Yeni vakit başladı, 10 soru hakkı tanımlandı
    save_json(PROGRESS_FILE, progress)

# ===================== YANLIŞ SORULAR (SIDEBAR) =====================
# Sidebar'ı en üstte tanımlıyoruz ki soru bitse bile hep orada kalsın
with st.sidebar:
    st.header("📊 İstatistikler")
    st.write(f"✅ Toplam Çözülen: {progress['global_index']}")
    st.write(f"❌ Yanlış Listesi: {len(wrong_ids)}")
    
    st.divider()
    show_wrongs = st.checkbox("📚 Yanlış Sorularımı Göster")
    if show_wrongs:
        if not wrong_ids:
            st.info("Henüz yanlışın yok! 🌸")
        else:
            for q_id in wrong_ids:
                q_item = next((item for item in questions if item["id"] == q_id), None)
                if q_item:
                    with st.expander(f"Soru: {q_item['soru'][:30]}..."):
                        st.write(f"**Soru:** {q_item['soru']}")
                        st.write(f"**Doğru Cevap:** {q_item['dogru']}")

# ===================== SORU MANTIĞI =====================

# 1. Genel limit kontrolü (Tüm sorular bitti mi?)
if progress["global_index"] >= len(questions):
    st.success("🎉 İnanılmaz! Tüm testleri bitirdin. Sen bir harikasın! 💖")
    st.balloons()

# 2. Vakitlik limit kontrolü (Bu sabah/akşam 10 soru çözüldü mü?)
elif progress["period_counter"] >= GUNLUK_SORU_SAYISI:
    st.warning(f"🌸 Bu vaktin ({current_slot}) için ayrılan {GUNLUK_SORU_SAYISI} soruyu tamamladın!")
    st.info("Bir sonraki vakitte (sabah 08:00 veya akşam 20:00) yeni soruların hazır olacak. Dinlen biraz aşkım! ✨")

# 3. Soru sorma aşaması
else:
    current_idx = progress["global_index"]
    q = questions[current_idx]
    
    st.write(f"**Soru {progress['period_counter'] + 1} / {GUNLUK_SORU_SAYISI}**")
    st.subheader(q["soru"])
    
    choice = st.radio("Cevabını seç:", q["secenekler"], key=f"q_{current_idx}")
    
    if st.button("Cevabı Onayla ✅"):
        if choice == q["dogru"]:
            st.balloons()
            
            # Mesaj seçimi
            available_msgs = [m for m in messages if m not in used_messages]
            if not available_msgs: 
                used_messages = []
                available_msgs = messages
            new_msg = random.choice(available_msgs) if available_msgs else "Harikasın! 💖"
            used_messages.append(new_msg)
            
            # İLERLEME KAYDI
            progress["global_index"] += 1    # Genel sırayı bir artır
            progress["period_counter"] += 1 # Bu vakit çözülen sayısını bir artır
            
            save_json(PROGRESS_FILE, progress)
            save_json(USED_MESSAGES_FILE, used_messages)
            
            st.success(f"DOĞRU! 🌟 \n\n 💌 {new_msg}")
            
            if st.button("Sonraki Soruya Geç ➡️"):
                st.rerun()
        else:
            st.error("❌ Yanlış cevap aşkım, bir daha düşünmek ister misin?")
            
            # Yanlışı kalıcı listeye ekle
            if q["id"] not in wrong_ids:
                wrong_ids.append(q["id"])
                save_json(WRONG_FILE, wrong_ids)
