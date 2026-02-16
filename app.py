import streamlit as st
import streamlit.components.v1 as components
import json
import random
import os
from datetime import datetime, time, timedelta
import pytz
import base64
from PIL import Image
from io import BytesIO
from pathlib import Path

# ===================== AYARLAR =====================
TIMEZONE = pytz.timezone("Europe/Istanbul")
MORNING_TIME = time(3, 43)
EVENING_TIME = time(3,20)
GUNLUK_SORU_SAYISI = 5

BASE_DIR = Path(__file__).parent
QUESTIONS_FILE = BASE_DIR / "questions.json"
ASKED_FILE = BASE_DIR / "asked_questions.json"
WEEKLY_FILE = BASE_DIR / "weekly_scores.json"
WRONG_FILE = BASE_DIR / "wrong_questions.json"

MESSAGES_FILE = BASE_DIR / "messages.json"
USED_MESSAGES_FILE = BASE_DIR / "used_messages.json"

st.set_page_config(page_title="Mini TUS", page_icon="👑")

# ===================== BASE64 =====================
def get_base64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

def get_base64_resized(path):
    img = Image.open(path)
    img = img.convert("RGBA")
    img = img.resize((300, int(img.height * 300 / img.width)))
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode()

try:
    budgie_img = get_base64_resized(BASE_DIR / "static" / "budgie.png")
except:
    budgie_img = ""

try:
    budgie_sound = get_base64(BASE_DIR / "static" / "budgie.mp3")
except:
    budgie_sound = ""

# ===================== JSON =====================
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

def get_random_message():
    messages = load_json(MESSAGES_FILE, [])
    used = load_json(USED_MESSAGES_FILE, [])

    if len(messages) == 0:
        messages = used
        used = []
        save_json(MESSAGES_FILE, messages)
        save_json(USED_MESSAGES_FILE, used)

    if not messages:
        return None

    selected = random.choice(messages)
    messages.remove(selected)
    used.append(selected)

    save_json(MESSAGES_FILE, messages)
    save_json(USED_MESSAGES_FILE, used)

    return selected


questions = load_json(QUESTIONS_FILE, [])
asked_questions = load_json(ASKED_FILE, [])
weekly_scores = load_json(WEEKLY_FILE, {})
wrong_questions = load_json(WRONG_FILE, [])

now_dt = datetime.now(TIMEZONE)
today = now_dt.strftime("%Y-%m-%d")
now_time = now_dt.time()

# ===================== OTURUM =====================
if now_time >= MORNING_TIME or now_time < EVENING_TIME:
    if now_time >= MORNING_TIME:
        session_type = "morning"
        st.title("🌅 Günaydın - Sabah Testi")
    else:
        session_type = "evening"
        st.title("🌙 İyi akşamlar - Akşam Testi")
else:
    st.info("Test saati henüz gelmedi")
    st.stop()

session_key = f"{today}_{session_type}"
mode = st.sidebar.radio("Mod Seç", ["Günlük Test", "Yanlışlarım"])

st.sidebar.markdown("### 📊 Haftalık Performans")

scores = []
for i in range(6, -1, -1):
    day = (now_dt - timedelta(days=i)).strftime("%Y-%m-%d")
    scores.append(weekly_scores.get(day, 0))

st.sidebar.line_chart(scores)
st.sidebar.write(f"🏆 Haftalık Toplam: {sum(scores)}")
st.sidebar.write(f"❌ Yanlış Havuzu: {len(wrong_questions)}")

# ===================== GÜNLÜK TEST =====================
if mode == "Günlük Test":

    if "session_id" not in st.session_state or st.session_state.session_id != session_key:
        st.session_state.session_id = session_key
        st.session_state.q_index = 0
        st.session_state.correct_count = 0
        st.session_state.finished = False
        st.session_state.retry_first_attempt = True

        remaining = []
        wrong_dict = {w["id"]: w for w in wrong_questions}

        for q in questions:
            if q["id"] in asked_questions:
                continue

            wrong_entry = wrong_dict.get(q["id"])
            if wrong_entry:
                wrong_date = datetime.strptime(
                    wrong_entry["wrong_date"], "%Y-%m-%d"
                ).date()
                if (now_dt.date() - wrong_date).days < 2:
                    continue

            remaining.append(q)

        if len(remaining) < GUNLUK_SORU_SAYISI:
            st.success("🎉 Tüm sorular tamamlandı!")
            st.stop()

        st.session_state.today_questions = random.sample(
            remaining, GUNLUK_SORU_SAYISI
        )

    today_questions = st.session_state.today_questions
    q_index = st.session_state.q_index

    # 🔒 OTURUM BİTTİ Mİ
    if q_index >= len(today_questions):

        if not st.session_state.finished:
            weekly_scores[today] = weekly_scores.get(today, 0) + st.session_state.correct_count
            save_json(WEEKLY_FILE, weekly_scores)
            st.session_state.finished = True

       # 🎉 FULL PARTY EFFECT
        components.html(f"""
        <style>
        
        body {{
          overflow: hidden;
        }}
        
        @keyframes fall {{
          0% {{ transform: translateY(-10vh); opacity:1; }}
          100% {{ transform: translateY(110vh); opacity:0; }}
        }}
        
        @keyframes rise {{
          0% {{ transform: translateY(100vh); opacity:1; }}
          100% {{ transform: translateY(-20vh); opacity:0; }}
        }}
        
        @keyframes fly {{
          0% {{ transform: translateX(-10vw); }}
          100% {{ transform: translateX(110vw); }}
        }}
        
        .item {{
          position: fixed;
          font-size: 28px;
          z-index: 9999;
          pointer-events:none;
        }}
        
        </style>
        
        <!-- KALPLER -->
        <div class="item" style="left:10vw; animation:fall 6s linear infinite;">💖</div>
        <div class="item" style="left:25vw; animation:fall 5s linear infinite;">💖</div>
        <div class="item" style="left:40vw; animation:fall 7s linear infinite;">💖</div>
        <div class="item" style="left:60vw; animation:fall 6.5s linear infinite;">💖</div>
        <div class="item" style="left:80vw; animation:fall 5.5s linear infinite;">💖</div>
        
        <!-- KONFETİ -->
        <div class="item" style="left:15vw; animation:rise 4s linear infinite;">🎊</div>
        <div class="item" style="left:35vw; animation:rise 5s linear infinite;">🎊</div>
        <div class="item" style="left:55vw; animation:rise 3.5s linear infinite;">🎊</div>
        <div class="item" style="left:75vw; animation:rise 4.5s linear infinite;">🎊</div>
        
        <!-- KUŞLAR -->
        <img src="data:image/png;base64,{budgie_img}" 
             class="item" 
             style="top:20vh; width:80px; animation:fly 8s linear infinite;" />
        
        <img src="data:image/png;base64,{budgie_img}" 
             class="item" 
             style="top:50vh; width:90px; animation:fly 6s linear infinite;" />
        
        <img src="data:image/png;base64,{budgie_img}" 
             class="item" 
             style="top:70vh; width:85px; animation:fly 7s linear infinite;" />

        
        <audio autoplay>
        <source src="data:audio/mp3;base64,{budgie_sound}" type="audio/mp3">
        </audio>
        
        """, height=800)

        st.success("🎉 Oturum tamamlandı!")
        st.stop()

    q = today_questions[q_index]

    st.subheader(f"Soru {q_index + 1}")
    st.write(q["soru"])
