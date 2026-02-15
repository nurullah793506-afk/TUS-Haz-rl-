import streamlit as st
import streamlit.components.v1 as components
import json
import random
import os
from datetime import datetime, time, timedelta
import pytz
import base64
from PIL import Image

# ===================== AYARLAR =====================
TIMEZONE = pytz.timezone("Europe/Istanbul")
MORNING_TIME = time(8, 0)
EVENING_TIME = time(0, 16)
GUNLUK_SORU_SAYISI = 5

QUESTIONS_FILE = "questions.json"
ASKED_FILE = "asked_questions.json"
WEEKLY_FILE = "weekly_scores.json"
WRONG_FILE = "wrong_questions.json"

st.set_page_config(page_title="Mini TUS", page_icon="👑")

# ===================== BASE64 =====================
def get_base64_resized(path):
    img = Image.open(path)
    img = img.resize((300, int(img.height * 300 / img.width)))
    img.save("temp.png")
    with open("temp.png", "rb") as f:
        return base64.b64encode(f.read()).decode()

budgie_img = get_base64_resized("static/budgie.png")
budgie_sound = get_base64("static/budgie.mp3")


# ===================== JSON YÜKLE =====================
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

# ===================== OTURUM BELİRLE =====================
if MORNING_TIME <= now_time < EVENING_TIME:
    session_type = "morning"
    st.title("🌅 Günaydın 💖 Sabah Testi")
elif now_time >= EVENING_TIME:
    session_type = "evening"
    st.title("🌙 İyi akşamlar 💜 Akşam Testi")
else:
    st.info("Test saati henüz gelmedi 💖 (08:00 veya 20:00)")
    st.stop()

session_key = f"{today}_{session_type}"

# ===================== MOD =====================
mode = st.sidebar.radio("Mod Seç", ["Günlük Test", "Yanlışlarım"])

# ===================== HAFTALIK PANEL =====================
st.sidebar.markdown("### 📊 Haftalık Performans")

scores = []
for i in range(6, -1, -1):
    day = (now_dt - timedelta(days=i)).strftime("%Y-%m-%d")
    scores.append(weekly_scores.get(day, 0))

st.sidebar.line_chart(scores)
st.sidebar.write(f"🏆 Haftalık Toplam: {sum(scores)}")
st.sidebar.write(f"❌ Yanlış Havuzu: {len(wrong_questions)}")

# =========================================================
# ===================== GÜNLÜK TEST =======================
# =========================================================
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
            <div class="celebration">
                <div class="title">👑 HARİKASIN 👑</div>
            </div>

            <audio id="budgieSound" src="data:audio/mp3;base64,{budgie_sound}"></audio>

            <style>
            body {{ margin:0; overflow:hidden; }}
            html, body {{
            height: 100%;
            }}

            .celebration {{
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: radial-gradient(circle, #1e3c72, #2a5298);
                overflow: hidden;
            }}

            .title {{
                position: absolute;
                top: 10%;
                width: 100%;
                text-align: center;
                font-size: 60px;
                color: gold;
                font-weight: bold;
                text-shadow: 2px 2px 10px black;
            }}


            .bird {{
                position: absolute;
                width: 120px;
                height: auto;
                z-index: 9999;
            }}

            @keyframes flyRight {{
              0% {{ transform: translateX(-120px) translateY(0px) rotate(-5deg); }}
              100% {{ transform: translateX(110vw) translateY(0px) rotate(0deg); }}
            }}

            @keyframes flyLeft {{
              0% {{ transform: translateX(110vw) translateY(0px) rotate(5deg); }}
              100% {{ transform: translateX(-120px) translateY(0px) rotate(0deg); }}
            }}
            </style>

            <script>
            const celebration = document.querySelector('.celebration');
            const colors = [0, 60, 200];

            for (let i = 0; i < 12; i++) {{

                let bird = document.createElement('img');
                bird.src = "data:image/png;base64,{budgie_img}";
                bird.className = 'bird';
                
                bird.style.width = "120px";
                bird.style.left = Math.random() * 90 + "vw";
                bird.style.top = Math.random() * 90 + "vh";
                bird.style.zIndex = "9999";

                let hue = colors[Math.floor(Math.random() * colors.length)];
                bird.style.filter = "hue-rotate(" + hue + "deg) saturate(1.3)";

                let duration = 3 + Math.random() * 3;
                bird.style.top = Math.random() * 90 + 'vh';

                if (Math.random() < 0.5) {{
                    bird.style.animation = "flyRight " + duration + "s linear infinite";
                }} else {{
                    bird.style.animation = "flyLeft " + duration + "s linear infinite";
                }}

                celebration.appendChild(bird);
            }}

            const sound = document.getElementById("budgieSound");
            sound.play().catch(()=>{{}});
            </script>
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
            st.warning("Olmadı Aşkım bir daha deneyelim 💖")
            if not any(w["id"] == q["id"] for w in wrong_questions):
                wrong_questions.append({"id": q["id"], "date": today})
                save_json(WRONG_FILE, wrong_questions)
