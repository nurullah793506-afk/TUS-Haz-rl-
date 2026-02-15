import streamlit as st
import json
import random
import os
from datetime import datetime, time, timedelta
import pytz

# ===================== AYARLAR =====================
TIMEZONE = pytz.timezone("Europe/Istanbul")
MORNING_TIME = time(8, 0)
EVENING_TIME = time(23, 40)
GUNLUK_SORU_SAYISI = 5

QUESTIONS_FILE = "questions.json"
ASKED_FILE = "asked_questions.json"
WEEKLY_FILE = "weekly_scores.json"
WRONG_FILE = "wrong_questions.json"

st.set_page_config(page_title="Mini TUS", page_icon="👑")

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

        # ===================== >=4 KUTLAMA =====================
        if st.session_state.correct_count >= 4:

            st.markdown("""
            <div class="celebration">
                <div class="title">👑 HARİKASIN 👑</div>
            </div>

            <audio id="budgieSound">
                <source src="budgie.mp3" type="audio/mpeg">
            </audio>

            <style>
            .celebration {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: radial-gradient(circle, #1e3c72, #2a5298);
                z-index: 9999;
                overflow: hidden;
                animation: fadeOut 5s forwards;
            }

            .title {
                position: absolute;
                top: 10%;
                width: 100%;
                text-align: center;
                font-size: 60px;
                color: gold;
                font-weight: bold;
                text-shadow: 2px 2px 10px black;
            }

            .bird {
                position: absolute;
                width: 80px;
            }

            @keyframes flyRight {
              0% { transform: translateX(-120px) translateY(0px) rotate(-5deg); }
              25% { transform: translateX(25vw) translateY(-25px) rotate(5deg); }
              50% { transform: translateX(50vw) translateY(20px) rotate(-4deg); }
              75% { transform: translateX(75vw) translateY(-15px) rotate(3deg); }
              100% { transform: translateX(110vw) translateY(0px) rotate(0deg); }
          }

            @keyframes flyLeft {
                0% { transform: translateX(110vw) translateY(0px) rotate(5deg); }
                25% { transform: translateX(75vw) translateY(-20px) rotate(-5deg); }
                50% { transform: translateX(50vw) translateY(25px) rotate(4deg); }
                75% { transform: translateX(25vw) translateY(-15px) rotate(-3deg); }
                100% { transform: translateX(-120px) translateY(0px) rotate(0deg); }
            }
            
            @keyframes jumpUp {
                0% { transform: translateY(100vh) rotate(-10deg); }
                50% { transform: translateY(40vh) rotate(10deg); }
                100% { transform: translateY(-120px) rotate(-5deg); }
            }

            @keyframes fadeOut {
                0% {opacity: 1;}
                90% {opacity: 1;}
                100% {opacity: 0; visibility: hidden;}
            }
            </style>

            <script>
            const celebration = document.querySelector('.celebration');

            const colors = [0, 60, 200];

            for (let i = 0; i < 12; i++) {

                let bird = document.createElement('img');
                bird.src = 'budgie.png';
                bird.className = 'bird';

                let hue = colors[Math.floor(Math.random() * colors.length)];
                bird.style.filter = `hue-rotate(${hue}deg) saturate(1.3)`;

                let randomType = Math.random();
                let duration = 3 + Math.random() * 3;

                if (randomType < 0.4) {
                    bird.style.top = Math.random() * 90 + 'vh';
                    bird.style.animation = `flyRight ${duration}s linear infinite`;
                }
                else if (randomType < 0.8) {
                    bird.style.top = Math.random() * 90 + 'vh';
                    bird.style.animation = `flyLeft ${duration}s linear infinite`;
                }
                else {
                    bird.style.left = Math.random() * 90 + 'vw';
                    bird.style.animation = `jumpUp ${duration}s linear infinite`;
                }

                celebration.appendChild(bird);
            }

            const sound = document.getElementById("budgieSound");
            let count = 0;

            function playSound() {
                if (count < 3) {
                    sound.currentTime = 0;
                    sound.play();
                    count++;
                }
            }

            sound.addEventListener("ended", playSound);
            playSound();

            </script>
            """, unsafe_allow_html=True)

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

# =========================================================
# ===================== YANLIŞLARIM =======================
# =========================================================
if mode == "Yanlışlarım":

    st.header("❌ Yanlışlarım")

    eligible_ids = []
    for w in wrong_questions:
        wrong_date = datetime.strptime(w["date"], "%Y-%m-%d").date()
        if (now_dt.date() - wrong_date).days >= 2:
            eligible_ids.append(w["id"])

    eligible_questions = [q for q in questions if q["id"] in eligible_ids]

    if not eligible_questions:
        st.info("2 gün dolmuş yanlış yok 💖")
        st.stop()

    if "wrong_mode" not in st.session_state:
        st.session_state.wrong_mode = random.sample(
            eligible_questions,
            min(5, len(eligible_questions))
        )
        st.session_state.wrong_index = 0

    wrong_list = st.session_state.wrong_mode
    wrong_index = st.session_state.wrong_index

    if wrong_index >= len(wrong_list):
        st.success("🎉 Yanlış tekrar tamamlandı!")
        del st.session_state.wrong_mode
        del st.session_state.wrong_index
        st.stop()

    q = wrong_list[wrong_index]

    st.subheader(f"Yanlış Soru {wrong_index + 1}")
    st.write(q["soru"])

    choice = st.radio("Seç:", q["secenekler"], key=f"wrong_{wrong_index}")

    if st.button("Onayla"):
        if choice == q["dogru"]:
            st.success("Doğru 👑 Soru silindi.")
            wrong_questions = [w for w in wrong_questions if w["id"] != q["id"]]
            save_json(WRONG_FILE, wrong_questions)
        else:
            st.warning("Tekrar çalış 😏")

        st.session_state.wrong_index += 1
        st.rerun()
