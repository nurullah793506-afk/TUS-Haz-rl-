import streamlit as st
import streamlit.components.v1 as components
import sqlite3
import json
import random
from datetime import datetime, time, timedelta
import pytz
import base64
from PIL import Image
from io import BytesIO
from pathlib import Path

# ===================== AYARLAR =====================
TIMEZONE = pytz.timezone("Europe/Istanbul")
MORNING_TIME = time(8, 0)
EVENING_TIME = time(20, 0)
GUNLUK_SORU_SAYISI = 5

BASE_DIR = Path(__file__).parent
QUESTIONS_FILE = BASE_DIR / "questions.json"
MESSAGES_FILE = BASE_DIR / "messages.json"

def load_first_try_messages():
    try:
        with open(MESSAGES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("first_try", [])
    except:
        return []

FIRST_TRY_MESSAGES = load_first_try_messages()




st.set_page_config(page_title="Mini TUS", page_icon="👑")

# ===================== DATABASE =====================
DB_FILE = BASE_DIR / "tus.db"

conn = sqlite3.connect(DB_FILE, check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS progress (
    question_id INTEGER PRIMARY KEY,
    status TEXT,
    next_review TEXT
)
""")

conn.commit()

# ===================== YARDIMCI =====================

def load_questions():
    with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def get_base64_resized(path):
    img = Image.open(path)
    img = img.convert("RGBA")
    img = img.resize((300, int(img.height * 300 / img.width)))
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode()

questions = load_questions()
# ===================== SABİT MESAJLAR =====================

RECOVERY_MESSAGES = [
    "Bak gördün mü, vazgeçmeyince oluyormuş 💛",
    "İkinci denemede bile parlıyorsun 😌",
]

WRONG_MESSAGES = [
    "Olmadı ama sorun değil, devam 💕",
    "Hata yapmak serbest, vazgeçmek yasak 💛",
]

FINISH_MESSAGES = [
    "Bugünkü performansınla kalbimde kadro garantiledin 💖",
    "Bugün de zekana aşık oldum 😌",
]



now_dt = datetime.now(TIMEZONE)
today = now_dt.strftime("%Y-%m-%d")
now_time = now_dt.time()

# ===================== OTURUM =====================
if MORNING_TIME <= now_time < EVENING_TIME:
    session_type = "morning"
    st.title("🌅 Günaydın Güzelliğim")
else:
    session_type = "evening"
    st.title("🌙 İyi Akşamlar Sevdiceğim")

session_key = today
mode = st.sidebar.radio("Mod Seç", ["Günlük Test", "Yanlışlarım"])

# ===================== GÜNLÜK TEST =====================

if mode == "Günlük Test":

    if "session_id" not in st.session_state or st.session_state.session_id != session_key:
        st.session_state.session_id = session_key
        st.session_state.q_index = 0
        st.session_state.first_attempt_correct = 0
        st.session_state.first_attempt_done = set()
        

        remaining = []

        for q in questions:
            cursor.execute(
                "SELECT status, next_review FROM progress WHERE question_id=?",
                (q["id"],)
            )
            row = cursor.fetchone()

            if row is None:
                remaining.append(q)
                continue

            status, next_review = row

            if status == "correct":
                continue

            if status == "wrong":
                review_date = datetime.strptime(next_review, "%Y-%m-%d").date()
                if now_dt.date() >= review_date:
                    remaining.append(q)

        if not remaining:
            st.success("🎉 Tüm sorular tamamlandı!")
            st.stop()

        st.session_state.today_questions = random.sample(
            remaining,
            min(GUNLUK_SORU_SAYISI, len(remaining))
        )


    today_questions = st.session_state.today_questions
    q_index = st.session_state.q_index

    if q_index >= len(today_questions):
        st.success("🎉 Hadi iyisin bu bölüm bitti!")
        st.success(random.choice(FINISH_MESSAGES))
        st.write(f"İlk denemede doğru: {st.session_state.first_attempt_correct}")
        st.stop()

    q = today_questions[q_index]

    st.subheader(f"Soru {q_index + 1}")
    st.write(q["soru"])

    selected = st.radio(
        "Cevabınız:",
        q["secenekler"],
        key=f"radio_{q_index}"
    )

    if st.button("Cevapla", key=f"btn_{q_index}"):

        is_first_try = q["id"] not in st.session_state.first_attempt_done

        if selected == q["dogru"]:
        
            if is_first_try:
                st.session_state.first_attempt_correct += 1
        
                if FIRST_TRY_MESSAGES:
                    message = random.choice(FIRST_TRY_MESSAGES)
                else:
                    message = "💖"
        
            else:
                message = random.choice(RECOVERY_MESSAGES)
        
            st.success(message)
        
            st.session_state.first_attempt_done.add(q["id"])
        
            cursor.execute("""
                INSERT OR REPLACE INTO progress (question_id, status, next_review)
                VALUES (?, 'correct', NULL)
            """, (q["id"],))
            conn.commit()
        
            st.session_state.q_index += 1
            st.rerun()

        else:

            st.error(random.choice(WRONG_MESSAGES))

            if is_first_try:
                st.session_state.first_attempt_done.add(q["id"])

            next_review_date = (now_dt + timedelta(days=2)).strftime("%Y-%m-%d")

            cursor.execute("""
                INSERT OR REPLACE INTO progress (question_id, status, next_review)
                VALUES (?, 'wrong', ?)
            """, (q["id"], next_review_date))
            conn.commit()

# ===================== YANLIŞLARIM =====================

if mode == "Yanlışlarım":

    cursor.execute("SELECT question_id FROM progress WHERE status='wrong'")
    rows = cursor.fetchall()

    if not rows:
        st.info("Henüz yanlış yaptığın soru yok 🎉")
        st.stop()

    wrong_ids = [r[0] for r in rows]
    wrong_list = [q for q in questions if q["id"] in wrong_ids]

    for q in wrong_list:
        st.subheader("Yanlış Soru")
        st.write(q["soru"])
        st.write("Doğru Cevap:", q["dogru"])
        st.markdown("---")

    st.stop()

# ===================== İSTATİSTİK =====================

st.sidebar.markdown("---")
st.sidebar.subheader("📊 İstatistik")

cursor.execute("SELECT COUNT(*) FROM progress WHERE status='correct'")
correct_total = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM progress WHERE status='wrong'")
wrong_total = cursor.fetchone()[0]

st.sidebar.write("✅ Toplam Doğru:", correct_total)
st.sidebar.write("❌ Toplam Yanlış:", wrong_total)
