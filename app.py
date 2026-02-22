import streamlit as st
import json
import random
import os
from datetime import datetime, time
import pytz

# ===================== AYARLAR =====================
TIMEZONE = pytz.timezone("Europe/Istanbul")
MORNING_TIME = time(8, 0)
EVENING_TIME = time(20, 0)
GUNLUK_SORU_SAYISI = 5

QUESTIONS_FILE = "questions.json"
ASKED_FILE = "asked_questions.json"
MESSAGES_FILE = "messages.json"
USED_MESSAGES_FILE = "used_messages.json"
# ==================================================

st.set_page_config(page_title="Günün Seçilmiş Soruları", page_icon="🌸")
st.title("🌸 Günaydın Güzelliğim 💖")

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
asked_questions = load_json(ASKED_FILE, [])
messages = load_json(MESSAGES_FILE, [])
used_messages = load_json(USED_MESSAGES_FILE, [])
# ==================================================

# ===================== PERIOD KONTROL =====================
if "period" not in st.session_state or st.session_state.period != current_period:
    st.session_state.period = current_period
    st.session_state.q_index = 0
    st.session_state.today_questions = []
    st.session_state.show_message = None

    remaining = [q for q in questions if q["id"] not in asked_questions]

    if len(remaining) < GUNLUK_SORU_SAYISI:
        st.success("🎉 Tüm sorular tamamlandı!")
        st.stop()

    st.session_state.today_questions = random.sample(
        remaining, GUNLUK_SORU_SAYISI
    )
# ========================================================
# ==================================================

# ===================== ROMANTİK MESAJ GÖSTER =====================
if st.session_state.get("show_message"):
    st.success("💖 " + st.session_state.show_message)
    st.balloons()
    st.session_state.show_message = None
# ===============================================================
today_questions = st.session_state.today_questions
q_index = st.session_state.q_index

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
        # Soruyu işaretle
        asked_questions.append(q["id"])
        save_json(ASKED_FILE, asked_questions)

        # Romantik mesaj (tekrar etmeyen)
        available_messages = [m for m in messages if m not in used_messages]

        if available_messages:
            msg = random.choice(available_messages)
            used_messages.append(msg)
            save_json(USED_MESSAGES_FILE, used_messages)
            st.session_state.show_message = msg

        st.session_state.q_index += 1
        st.rerun()
    else:
        st.warning("❌ hadi bir daha deneyelim aşkım 💖💭")
# ==================================================  
