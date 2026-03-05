import streamlit as st
import json
import random
import os
from datetime import datetime, time
import pytz

# ===================== AYARLAR =====================
TIMEZONE = pytz.timezone("Europe/Istanbul")
MORNING_TIME = time(8, 00)
EVENING_TIME = time(18, 50)
GUNLUK_SORU_SAYISI = 10

st.set_page_config(page_title="Günün Seçilmiş Soruları", page_icon="🌸")
st.title("🌸 Günaydın Güzelliğim 💖")

QUESTIONS_FILE = "questions.json"
MESSAGES_FILE = "messages.json"
USED_MESSAGES_FILE = "used_messages.json"
PROGRESS_FILE = "progress.json"
WRONG_FILE = "wrong_questions.json"
# ==================================================

# ===================== JSON YARDIMCILAR =====================
def load_json(path, default):
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default, f, ensure_ascii=False, indent=2)
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
# ==========================================================

# ===================== VERİLER =====================
questions = load_json(QUESTIONS_FILE, [])
messages = load_json(MESSAGES_FILE, [])
used_messages = load_json(USED_MESSAGES_FILE, [])
progress = load_json(PROGRESS_FILE, {})
wrong_questions = load_json(WRONG_FILE, [])  # <-- st.write'den önce yüklendi
questions = sorted(questions, key=lambda x: x["id"])
# ==================================================

# ===================== YANLIŞ SORULAR =====================
st.write(f"📊 Toplam yanlış soru: {len(wrong_questions)}")
if st.button("📚 Yanlış Sorularımı Gör"):

    if not wrong_questions:
        st.info("Henüz yanlış yaptığın soru yok 🌸")

    else:
        st.subheader("Yanlış Yaptığın Sorular")

        for q in questions:
            if q["id"] in wrong_questions:
                st.write("Soru:", q["soru"])
                for idx, secenek in enumerate(q["secenekler"]):
                    st.write(f"{chr(65+idx)}) {secenek}")
                st.write("Doğru cevap:", q["dogru"])
                st.markdown("---")

# ==========================================================


# ===================== SLOT KONTROL =====================
now_dt = datetime.now(TIMEZONE)
now = now_dt.time()
today = now_dt.strftime("%Y-%m-%d")

slot = None

if MORNING_TIME <= now < EVENING_TIME:
    slot = "morning"
elif now >= EVENING_TIME:
    slot = "evening"
else:
    st.info("⏰ Sorular sabah 08:00 ve akşam 20:00'de açılır 💖")
    st.stop()

current_period = f"{today}_{slot}"
# ========================================================



# ===================== PERIOD KONTROL =====================

if progress.get("period") != current_period:

    global_index = progress.get("global_index", 0)

    today_questions = questions[global_index:global_index + GUNLUK_SORU_SAYISI]

    if len(today_questions) == 0:
        st.success("🎉 Tüm sorular tamamlandı!")
        st.stop()

    progress = {
        "period": current_period,
        "q_index": 0,
        "global_index": global_index
    }

    save_json(PROGRESS_FILE, progress)

# Session state'i progress'ten doldur
st.session_state.q_index = progress["q_index"]
# ========================================================
# ===================== MESAJ GÖSTER =====================
if "show_message" in st.session_state and st.session_state.show_message:
    st.success("💖 " + st.session_state.show_message)
    st.balloons()
    st.session_state.show_message = None
# ========================================================

# ===================== ROMANTİK MESAJ GÖSTER =====================

# ===============================================================
global_index = progress["global_index"]
today_questions = questions[global_index:global_index + GUNLUK_SORU_SAYISI]
q_index = st.session_state.q_index
st.session_state.today_questions = questions[global_index:global_index + GUNLUK_SORU_SAYISI]
if q_index >= len(today_questions):
    st.success("🎉 Bugünün tüm sorularını tamamladın!")
    st.stop()

# ===================== SORU =====================
q = today_questions[q_index]

st.subheader(f"📝 Soru {q_index + 1}")
st.write(q["soru"])

choice = st.radio(
    "Cevabını seç:",
    q["secenekler"],
    key=f"choice_{q_index}"
)

if st.button("Cevabı Onayla ✅"):

    if choice == q["dogru"]:


        available_messages = [
            m for m in messages if m not in used_messages
        ]

        if available_messages:
            msg = random.choice(available_messages)
            used_messages.append(msg)
            save_json(USED_MESSAGES_FILE, used_messages)

            # 👉 BURASI ÖNEMLİ
            st.session_state.show_message = msg
        else:
            st.session_state.show_message = "💌 Tüm mesajlar kullanıldı 💖"

        st.session_state.q_index += 1
        progress["global_index"] = progress["global_index"] + 1
        
        progress["q_index"] = st.session_state.q_index
        save_json(PROGRESS_FILE, progress)
        
        st.rerun()

    else:
        
            if q["id"] not in wrong_questions:
                wrong_questions.append(q["id"])
                save_json(WRONG_FILE, wrong_questions)
        
            st.warning("❌ hadi bir daha deneyelim aşkım 💖💭")
# ==================================================
