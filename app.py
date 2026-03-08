import streamlit as st
import json
import random
import os
from datetime import datetime
import pytz

# ===================== AYARLAR =====================
TIMEZONE = pytz.timezone("Europe/Istanbul")
GUNLUK_SORU_SAYISI = 10  # Her slotta (sabah/akşam) kaç yeni soru eklenecek

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
# Soruları ID'ye göre sıralıyoruz ki hep aynı sırada gitsin
questions = sorted(questions, key=lambda x: x.get("id", 0))

messages = load_json(MESSAGES_FILE, [])
used_messages = load_json(USED_MESSAGES_FILE, [])
progress = load_json(PROGRESS_FILE, {"global_index": 0, "last_period": ""})
wrong_ids = load_json(WRONG_FILE, [])

# ===================== ZAMAN KONTROLÜ =====================
now_dt = datetime.now(TIMEZONE)
current_hour = now_dt.hour
today_str = now_dt.strftime("%Y-%m-%d")

# Slot belirleme (Sabah 08-20, Akşam 20-08)
if 8 <= current_hour < 20:
    current_slot = "sabah"
else:
    current_slot = "aksam"

period_id = f"{today_str}_{current_slot}"

# ===================== YANLIŞ SORULAR BÖLÜMÜ =====================
with st.sidebar:
    st.header("📊 İstatistikler")
    st.write(f"✅ Çözülen Toplam: {progress['global_index']}")
    st.write(f"❌ Yanlış Listesi: {len(wrong_ids)}")
    
    if st.checkbox("📚 Yanlış Sorularımı Göster"):
        st.subheader("Hatalı Sorular Arşivi")
        if not wrong_ids:
            st.info("Harikasın, hiç yanlışın yok! 🌸")
        else:
            for q_id in wrong_ids:
                # Soru listesinden ilgili soruyu bul
                q_item = next((item for item in questions if item["id"] == q_id), None)
                if q_item:
                    with st.expander(f"Soru ID: {q_id}"):
                        st.write(q_item["soru"])
                        st.write(f"🎯 Doğru Cevap: **{q_item['dogru']}**")

# ===================== SORU MANTIĞI =====================

# Eğer yeni bir döneme girdiysek (örn: sabahtan akşama geçtik)
# Burada bir kısıtlama istersen ekleyebilirsin, şu an kesintisiz devam ediyor.

current_idx = progress.get("global_index", 0)

if current_idx >= len(questions):
    st.success("🎉 İnanılmaz! Tüm soruları tamamladın aşkım. Yeni soruları beklemede kal! 💖")
    st.balloons()
else:
    q = questions[current_idx]
    
    st.info(f"📍 Şu an {current_idx + 1}. sorudasın")
    st.subheader(f"📝 Soru")
    st.write(q["soru"])
    
    # Seçenekleri göster
    choice = st.radio("Cevabını seç:", q["secenekler"], key=f"q_{current_idx}")
    
    if st.button("Cevabı Onayla ✅"):
        if choice == q["dogru"]:
            # DOĞRU CEVAP
            st.balloons()
            
            # Rastgele mesaj seçimi
            available_msgs = [m for m in messages if m not in used_messages]
            if not available_msgs: # Mesajlar bittiyse sıfırla
                used_messages = []
                available_msgs = messages
            
            new_msg = random.choice(available_msgs) if available_msgs else "Harikasın! 💖"
            used_messages.append(new_msg)
            
            # İlerlemeyi kaydet
            progress["global_index"] += 1
            progress["last_period"] = period_id
            
            save_json(PROGRESS_FILE, progress)
            save_json(USED_MESSAGES_FILE, used_messages)
            
            st.success(f"DOĞRU! 🌟 \n\n 💌 Mesajın: {new_msg}")
            
            # Bir sonraki soruya geçmek için sayfayı yenile
            if st.button("Sonraki Soruya Geç ➡️"):
                st.rerun()
        else:
            # YANLIŞ CEVAP
            st.error("❌ Ah, bu sefer olmadı ama pes etmek yok! 💖")
            
            # Yanlışı kalıcı listeye ekle (eğer daha önce eklenmediyse)
            if q["id"] not in wrong_ids:
                wrong_ids.append(q["id"])
                save_json(WRONG_FILE, wrong_ids)
            
            st.info("Bu soru 'Yanlış Sorularım' listesine eklendi, oradan tekrar bakabilirsin.")

# ==========================================================
