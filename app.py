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

@keyframes fallDown {{
  0% {{ transform: translateY(-10vh); opacity:1; }}
  100% {{ transform: translateY(110vh); opacity:0; }}
}}

@keyframes floatUp {{
  0% {{ transform: translateY(0vh); opacity:1; }}
  100% {{ transform: translateY(-120vh); opacity:0; }}
}}

@keyframes flyAcross {{
  0% {{ transform: translateX(-15vw); }}
  100% {{ transform: translateX(115vw); }}
}}

.party {{
  position: fixed;
  font-size: 28px;
  pointer-events:none;
  z-index:9999;
}}

</style>

<script>

function randomBetween(min,max){{
  return Math.random()*(max-min)+min;
}}

function createHearts(){{
  for(let i=0;i<40;i++){{
    let el=document.createElement("div");
    el.innerHTML="💖";
    el.className="party";
    el.style.left=Math.random()*100+"vw";
    el.style.top="-10vh";
    el.style.animation=`fallDown ${randomBetween(4,7)}s linear forwards`;
    el.style.animationDelay=randomBetween(0,3)+"s";
    document.body.appendChild(el);
    setTimeout(()=>el.remove(),8000);
  }}
}}

function createConfetti(){{
  for(let i=0;i<40;i++){{
    let el=document.createElement("div");
    el.innerHTML="🎊";
    el.className="party";
    el.style.left=Math.random()*100+"vw";
    el.style.top="100vh";
    el.style.animation=`floatUp ${randomBetween(3,6)}s linear forwards`;
    el.style.animationDelay=randomBetween(0,2)+"s";
    document.body.appendChild(el);
    setTimeout(()=>el.remove(),7000);
  }}
}}

function createBirds(){{
  for(let i=0;i<6;i++){{
    let el=document.createElement("div");
    el.innerHTML="🐦";
    el.className="party";
    el.style.top=Math.random()*80+"vh";
    el.style.fontSize="36px";
    el.style.animation=`flyAcross ${randomBetween(5,8)}s linear forwards`;
    el.style.animationDelay=randomBetween(0,2)+"s";
    document.body.appendChild(el);
    setTimeout(()=>el.remove(),9000);
  }}
}}

createHearts();
createConfetti();
createBirds();

</script>

<audio autoplay>
<source src="data:audio/mp3;base64,{budgie_sound}" type="audio/mp3">
</audio>

""", height=800)

        st.success("🎉 Oturum tamamlandı!")
        st.stop()

    q = today_questions[q_index]

    st.subheader(f"Soru {q_index + 1}")
    st.write(q["soru"])
