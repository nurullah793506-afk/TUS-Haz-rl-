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
MORNING_TIME = time(8, 0)
EVENING_TIME = time(2, 13)
GUNLUK_SORU_SAYISI = 5

BASE_DIR = Path(__file__).parent
QUESTIONS_FILE = BASE_DIR / "questions.json"
ASKED_FILE = BASE_DIR / "asked_questions.json"
WEEKLY_FILE = BASE_DIR / "weekly_scores.json"
WRONG_FILE = BASE_DIR / "wrong_questions.json"

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
except Exception as e:
    st.error(f"Görsel yüklenemedi: {e}")
    budgie_img = ""

try:
    budgie_sound = get_base64(BASE_DIR / "static" / "budgie.mp3")
except Exception as e:
    st.error(f"Ses dosyası yüklenemedi: {e}")
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

questions = load_json(QUESTIONS_FILE, [])
asked_questions = load_json(ASKED_FILE, [])
weekly_scores = load_json(WEEKLY_FILE, {})
wrong_questions = load_json(WRONG_FILE, [])

now_dt = datetime.now(TIMEZONE)
today = now_dt.strftime("%Y-%m-%d")
now_time = now_dt.time()

# ===================== OTURUM =====================
if MORNING_TIME <= now_time < EVENING_TIME:
    session_type = "morning"
    st.title("🌅 Günaydın - Sabah Testi")
elif now_time >= EVENING_TIME:
    session_type = "evening"
    st.title("🌙 İyi akşamlar - Akşam Testi")
else:
    st.info("Test saati henüz gelmedi (08:00 veya 20:00)")
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

        remaining = [q for q in questions if q["id"] not in asked_questions]

        if len(remaining) < GUNLUK_SORU_SAYISI:
            st.success("🎉 Tüm sorular tamamlandı!")
            st.stop()

        st.session_state.today_questions = random.sample(
            remaining, GUNLUK_SORU_SAYISI
        )

    today_questions = st.session_state.today_questions
    q_index = st.session_state.q_index

    if q_index >= len(today_questions):

        if not st.session_state.finished:
            weekly_scores[today] = weekly_scores.get(today, 0) + st.session_state.correct_count
            save_json(WEEKLY_FILE, weekly_scores)
            st.session_state.finished = True

        if st.session_state.correct_count >= 4:

            components.html(f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
html, body {{
  height: 100%;
  margin: 0;
  overflow: hidden;
}}
.celebration {{
  position: fixed;
  inset: 0;
  background: linear-gradient(180deg, #ff87c6 0%, #ff6fb1 100%);
}}
.title {{
  position: absolute;
  top: 8%;
  width: 100%;
  text-align: center;
  font-size: 56px;
  color: white;
  font-weight: bold;
}}
.bird {{
  position: absolute;
  width: 120px;
  height: auto;
}}
@keyframes flyRight {{
  0% {{ transform: translateX(-15vw); }}
  100% {{ transform: translateX(115vw); }}
}}
@keyframes flyLeft {{
  0% {{ transform: translateX(115vw) scaleX(-1); }}
  100% {{ transform: translateX(-15vw) scaleX(-1); }}
}}
.confetti {{
  position: absolute;
  width: 8px;
  height: 16px;
  opacity: 0.8;
  animation: confettiUp linear infinite;
}}

@keyframes confettiUp {{
  0% {{ transform: translateY(110vh) rotate(0deg); }}
  100% {{ transform: translateY(-10vh) rotate(720deg); }}
}}

.balloon {{
  position: absolute;
  width: 40px;
  height: 55px;
  border-radius: 50%;
  animation: balloonDown linear infinite;
}}

.balloon::after {{
  content: "";
  position: absolute;
  width: 2px;
  height: 30px;
  background: white;
  left: 50%;
  top: 55px;
}}

@keyframes balloonDown {{
  0% {{ transform: translateY(-20vh); }}
  100% {{ transform: translateY(110vh); }}
}}

.heart {{
  position: absolute;
  width: 18px;
  height: 18px;
  background: #ff4d88;
  transform: rotate(-45deg);
  animation: heartFall linear infinite;
}}

.heart:before,
.heart:after {{
  content: "";
  position: absolute;
  width: 18px;
  height: 18px;
  background: #ff4d88;
  border-radius: 50%;
}}

.heart:before {{
  top: -9px;
  left: 0;
}}

.heart:after {{
  left: 9px;
  top: 0;
}}

@keyframes heartFall {{
  0% {{ transform: translateY(-20vh) rotate(-45deg); }}
  100% {{ transform: translateY(110vh) rotate(-45deg); }}
}}

</style>
</head>
<body>
<div class="celebration" id="celebration">
  <div class="title">👑 Harikasın 👑</div>
  <audio autoplay src="data:audio/mp3;base64,{budgie_sound}"></audio>
</div>

<script>
const root = document.getElementById("celebration");

for (let i = 0; i < 12; i++) {{

  const bird = document.createElement("div");
  bird.className = "bird";
  bird.style.top = Math.random()*80 + "vh";
  bird.style.animation = (Math.random()<0.5 ?
      "flyRight " : "flyLeft ") + (3+Math.random()*3)+"s linear infinite";

  const color = "hsl(" + (Math.random()*360) + ", 80%, 60%)";

  bird.innerHTML =
  '<svg width="60" height="40" viewBox="0 0 60 40">' +
    '<ellipse cx="30" cy="25" rx="20" ry="12" fill="' + color + '" />' +
    '<circle cx="48" cy="20" r="6" fill="' + color + '" />' +
    '<polygon points="54,20 60,23 54,26" fill="orange"/>' +
    '<circle cx="50" cy="18" r="2" fill="black"/>' +
  '</svg>';

  root.appendChild(bird);
}}



// CONFETTI
for (let i = 0; i < 40; i++) {{
  const confetti = document.createElement("div");
  confetti.className = "confetti";
  confetti.style.left = Math.random()*100 + "vw";
  confetti.style.background = "hsl(" + (Math.random()*360) + ", 100%, 60%)";
  confetti.style.animationDuration = (3+Math.random()*3)+"s";
  root.appendChild(confetti);
}}

// BALLOONS
for (let i = 0; i < 12; i++) {{
  const balloon = document.createElement("div");
  balloon.className = "balloon";
  balloon.style.left = Math.random()*100 + "vw";
  balloon.style.background = "hsl(" + (Math.random()*360) + ", 70%, 60%)";
  balloon.style.animationDuration = (6+Math.random()*4)+"s";
  root.appendChild(balloon);
}}

// HEARTS
for (let i = 0; i < 25; i++) {{
  const heart = document.createElement("div");
  heart.className = "heart";
  heart.style.left = Math.random()*100 + "vw";
  heart.style.animationDuration = (4+Math.random()*4) + "s";
  heart.style.animationDelay = (Math.random()*3) + "s";
  root.appendChild(heart);
}}
</script>
</body>
</html>
""", height=900)

        else:
            st.success("🎉 Oturum tamamlandı!")

        st.stop()

    q = today_questions[q_index]

    st.subheader(f"Soru {q_index + 1}")
    st.write(q["soru"])

    choice = st.radio("Seç:", q["secenekler"], key=f"{session_type}_{q_index}")

    if st.button("Onayla"):
        if choice == q["dogru"]:
            asked_questions.append(q["id"])
            save_json(ASKED_FILE, asked_questions)
            st.session_state.correct_count += 1
            st.session_state.q_index += 1
            st.rerun()
        else:
            st.warning("Yanlış oldu, tekrar deneyelim.")
            if not any(w["id"] == q["id"] for w in wrong_questions):
                wrong_questions.append({"id": q["id"], "date": today})
                save_json(WRONG_FILE, wrong_questions)
