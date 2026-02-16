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
MORNING_TIME = time(8, 00)
EVENING_TIME = time(20,00)
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
        st.title("🌅 Günaydın Güzelliğim - Hadi Uyanma Testlerimizi Çözelim")
    else:
        session_type = "evening"
        st.title("🌙 İyi akşamlar Sevdiceğim - Dizimizin Yeni Bölümü Yayınlandı")
else:
    st.info("Test saati henüz gelmedi")
    st.stop()

session_key = f"{today}_{session_type}"
mode = st.sidebar.radio("Mod Seç", ["Günlük Test", "Yanlışlarım"])

# ===================== YANLIŞLARIM =====================
if mode == "Yanlışlarım":

    st.title("📂 Yanlış Sorularım")

    if not wrong_questions:
        st.success("Yanlış soru yok 👑")
        st.stop()

    for w in wrong_questions:
        q = next((x for x in questions if x["id"] == w["id"]), None)
        if q:
            st.write("###", q["soru"])
            for sec in q["secenekler"]:
                st.write("-", sec)
            st.write("✅ Adamsın:", q["dogru"])
            st.write("---")

    st.stop()

# ===================== GÜNLÜK TEST =====================
if mode == "Günlük Test":

    if "session_id" not in st.session_state or st.session_state.session_id != session_key:
        st.session_state.session_id = session_key
        st.session_state.q_index = 0
        st.session_state.correct_count = 0

        # 🔥 EKLENENLER
        st.session_state.first_attempt_correct = 0
        st.session_state.first_attempt_done = set()

        st.session_state.finished = False

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
                if (now_dt.date() - wrong_date).days < 3:
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

    # OTURUM BİTTİ

    if q_index >= len(today_questions):
    
        if not st.session_state.finished:
            weekly_scores[today] = st.session_state.first_attempt_correct
            save_json(WEEKLY_FILE, weekly_scores)
            st.session_state.finished = True
    
        if st.session_state.first_attempt_correct >= 4:

            components.html(f"""
            <style>
            @keyframes fall {{0%{{transform:translateY(-10vh);}}100%{{transform:translateY(110vh);}}}}
            @keyframes rise {{0%{{transform:translateY(100vh);}}100%{{transform:translateY(-20vh);}}}}
            @keyframes fly {{0%{{transform:translateX(-10vw);}}100%{{transform:translateX(110vw);}}}}
            .item {{position:fixed;font-size:28px;z-index:9999;pointer-events:none;}}
            </style>

            <div class="item" style="left:10vw;animation:fall 6s linear infinite;">💖</div>
            <div class="item" style="left:30vw;animation:fall 5s linear infinite;">💖</div>
            <div class="item" style="left:50vw;animation:rise 4s linear infinite;">🎊</div>
            <div class="item" style="left:70vw;animation:rise 5s linear infinite;">🎊</div>

            <img src="data:image/png;base64,{budgie_img}"
                 class="item"
                 style="top:30vh;width:80px;animation:fly 8s linear infinite;" />

            <audio autoplay>
            <source src="data:audio/mp3;base64,{budgie_sound}" type="audio/mp3">
            </audio>
            """, height=600)

        st.success("🎉 Hadi iyisin bu bölüm bitti!")
        st.stop()

    q = today_questions[q_index]

    st.subheader(f"Soru {q_index + 1}")
    st.write(q["soru"])

    if "show_message" in st.session_state:
        st.success(f"🎉 {st.session_state.show_message}")
        del st.session_state["show_message"]

    options = q["secenekler"]
    selected = st.radio("Cevabınız:", options, key=f"radio_{q_index}")

    if st.button("Cevapla", key=f"btn_{q_index}"):

        # 🔥 ilk deneme mi?
        is_first_try = q["id"] not in st.session_state.first_attempt_done

        if selected == q["dogru"]:

            st.session_state.correct_count += 1

            # 🔥 ilk denemede doğruysa say
            if is_first_try:
                st.session_state.first_attempt_correct += 1

            st.session_state.first_attempt_done.add(q["id"])

            asked_questions.append(q["id"])
            save_json(ASKED_FILE, asked_questions)

            msg = get_random_message()
            if msg:
                st.session_state.show_message = msg

            st.session_state.q_index += 1
            st.rerun()

        else:
            st.error("OLmadı Aşkım ❌ Hadi tekrar deneyekim.")

            if is_first_try:
                st.session_state.first_attempt_done.add(q["id"])

            if not any(w["id"] == q["id"] for w in wrong_questions):
                wrong_questions.append({
                    "id": q["id"],
                    "wrong_date": today
                })
                save_json(WRONG_FILE, wrong_questions)
# ===================== İSTATİSTİK PANELİ =====================
st.sidebar.markdown("---")
st.sidebar.subheader("📊 İstatistikler")

today_score = weekly_scores.get(today, 0)

st.sidebar.write("📅 Bugün İlk Deneme Doğru:", today_score)

if GUNLUK_SORU_SAYISI > 0:
    success_rate = round((today_score / GUNLUK_SORU_SAYISI) * 100, 1)
else:
    success_rate = 0

st.sidebar.write("🎯 Başarı Oranı:", f"%{success_rate}")

st.sidebar.write("🧠 Toplam Çözülen Soru:", len(asked_questions))
st.sidebar.write("❌ Toplam Yanlış Soru:", len(wrong_questions))

st.sidebar.markdown("### 📈 Son 7 Gün")

sorted_days = sorted(weekly_scores.keys(), reverse=True)[:7]

for day in sorted_days:
    st.sidebar.write(f"{day} → {weekly_scores[day]} doğru")
