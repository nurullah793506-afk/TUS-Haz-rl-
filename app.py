import streamlit as st
import json
import random
import os
from datetime import datetime
import pytz
from supabase import create_client

# ===================== SUPABASE =====================

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

USER_ID = "main_user"

# ===================== AYARLAR =====================
TIMEZONE = pytz.timezone("Europe/Istanbul")
GUNLUK_SORU_SAYISI = 10

st.set_page_config(page_title="Günün Seçilmiş Soruları", page_icon="🌸")
st.title("🌸 Her İki Dünyamı Güzelleştiren Kadına 🌸")

QUESTIONS_FILE = "questions.json"
MESSAGES_FILE = "messages.json"
PROGRESS_FILE = "progress.json"
WRONG_FILE = "wrong_questions.json"

# ===================== SESSION STATE =====================
if "answered_correctly" not in st.session_state:
    st.session_state.answered_correctly = False

if "success_message" not in st.session_state:
    st.session_state.success_message = ""

if "wrong_answered_correctly" not in st.session_state:
    st.session_state.wrong_answered_correctly = False

if "wrong_success_message" not in st.session_state:
    st.session_state.wrong_success_message = ""

if "wrong_test_index" not in st.session_state:
    st.session_state.wrong_test_index = 0

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

# ===================== SUPABASE YARDIMCILAR =====================
def get_progress():
    result = supabase.table("app_progress").select("*").eq("user_id", USER_ID).execute()

    if result.data:
        return result.data[0]

    default_progress = {
        "user_id": USER_ID,
        "global_index": 0,
        "message_index": 0,
        "last_period": "",
        "period_counter": 0
    }

    supabase.table("app_progress").insert(default_progress).execute()
    return default_progress

def save_progress(progress):
    supabase.table("app_progress").upsert({
        "user_id": USER_ID,
        "global_index": progress["global_index"],
        "message_index": progress["message_index"],
        "last_period": progress["last_period"],
        "period_counter": progress["period_counter"]
    }).execute()

def get_wrong_ids():
    result = supabase.table("wrong_questions").select("question_id").eq("user_id", USER_ID).execute()

    if result.data:
        return [item["question_id"] for item in result.data]
    return []

def add_wrong_question(question_id):
    supabase.table("wrong_questions").upsert({
        "user_id": USER_ID,
        "question_id": question_id
    }).execute()

def remove_wrong_question(question_id):
    supabase.table("wrong_questions").delete().eq("user_id", USER_ID).eq("question_id", question_id).execute()

# ===================== VERİ YÜKLEME =====================
questions = load_json(QUESTIONS_FILE, [])
questions = sorted(questions, key=lambda x: x.get("id", 0))

messages = load_json(MESSAGES_FILE, [])

progress = get_progress()
wrong_ids = get_wrong_ids()

# ===================== ZAMAN KONTROLÜ =====================
now_dt = datetime.now(TIMEZONE)
current_hour = now_dt.hour
today_str = now_dt.strftime("%Y-%m-%d")

simdi_toplam_dakika = current_hour * 60 + now_dt.minute

sabah_baslangic = 11 * 60 + 30   # 08:30
aksam_baslangic = 20 * 60 + 30  # 20:30

if sabah_baslangic <= simdi_toplam_dakika < aksam_baslangic:
    current_slot = "sabah"
else:
    current_slot = "aksam"

period_id = f"{today_str}_{current_slot}"

if progress["last_period"] != period_id:
    progress["last_period"] = period_id
    progress["period_counter"] = 0
    save_progress(progress)

# ===================== SIDEBAR =====================
with st.sidebar:
    st.header("📊 İstatistikler")
    st.write(f"✅ Toplam Çözülen: {progress['global_index']}")
    st.write(f"❌ Yanlış Sayısı: {len(wrong_ids)}")

    st.divider()
    mode = st.radio(
        "Mod Seç",
        ["Günün Soruları", "Yanlış Testi"]
    )

    st.divider()
    if st.checkbox("📚 Yanlışlarımı Göster (Kalıcı Listem)"):
        if not wrong_ids:
            st.info("Hiç yanlışın yok, harikasın! 🌸")
        else:
            for q_id in wrong_ids:
                q_item = next((item for item in questions if item["id"] == q_id), None)
                if q_item:
                    with st.expander(f"Soru ID: {q_id}"):
                        st.write(f"**Soru:** {q_item['soru']}")
                        st.write(f"**Doğru:** {q_item['dogru']}")

# ===================== MOD 1: GÜNÜN SORULARI =====================
if mode == "Günün Soruları":
    if progress["global_index"] >= len(questions):
        st.success("🎉 İnanılmaz! Tüm sorular bitti. Sen bir şampiyonsun! 💖")
        st.balloons()

    elif progress["period_counter"] >= GUNLUK_SORU_SAYISI:
        st.warning(f"🌸 Bu vaktin ({current_slot}) için ayrılan {GUNLUK_SORU_SAYISI} soruyu bitirdin.")
        st.info("Bir sonraki vakit diliminde yeni soruların açılacak. Beklemede kal aşkım! ✨")

    else:
        current_idx = progress["global_index"]
        q = questions[current_idx]

        st.write(f"**Soru {progress['period_counter'] + 1} / {GUNLUK_SORU_SAYISI}**")
        st.subheader(q["soru"])

        if st.session_state.answered_correctly:
            st.balloons()
            st.success(st.session_state.success_message)

            if st.button("Sonraki Soruya Geç ➡️"):
                st.session_state.answered_correctly = False
                st.session_state.success_message = ""
                st.rerun()

        else:
            choice = st.radio("Cevabını seç:", q["secenekler"], key=f"q_{current_idx}")

            if st.button("Cevabı Onayla ✅"):
                if choice == q["dogru"]:
                    msg_idx = progress.get("message_index", 0)

                    if len(messages) > 0:
                        if msg_idx >= len(messages):
                            msg_idx = 0
                        current_msg = messages[msg_idx]
                    else:
                        current_msg = ""

                    progress["global_index"] += 1
                    progress["period_counter"] += 1
                    progress["message_index"] = msg_idx + 1

                    save_progress(progress)

                    st.session_state.answered_correctly = True
                    st.session_state.success_message = f"DOĞRU! 🌟 \n\n 💌 Mesajın: {current_msg}"
                    st.rerun()

                else:
                    st.error("❌ Yanlış cevap, tekrar dene bakalım 💖")

                    if q["id"] not in wrong_ids:
                        wrong_ids.append(q["id"])
                        add_wrong_question(q["id"])

# ===================== MOD 2: YANLIŞ TESTİ =====================
elif mode == "Yanlış Testi":
    wrong_questions = [q for q in questions if q["id"] in wrong_ids]

    if not wrong_questions:
        st.success("🌸 Yanlış listen boş. Hepsini toparlamışsın!")
    else:
        if st.session_state.wrong_test_index >= len(wrong_questions):
            st.session_state.wrong_test_index = 0

        q = wrong_questions[st.session_state.wrong_test_index]

        st.write(f"**Yanlış Testi {st.session_state.wrong_test_index + 1} / {len(wrong_questions)}**")
        st.subheader(q["soru"])

        if st.session_state.wrong_answered_correctly:
            st.balloons()
            st.success(st.session_state.wrong_success_message)

            if st.button("Sonraki Yanlış Soru ➡️"):
                st.session_state.wrong_answered_correctly = False
                st.session_state.wrong_success_message = ""
                st.session_state.wrong_test_index += 1
                st.rerun()

        else:
            choice = st.radio("Cevabını seç:", q["secenekler"], key=f"wrong_{q['id']}")

            if st.button("Yanlış Testi Cevabı Onayla ✅"):
                if choice == q["dogru"]:
                    remove_wrong_question(q["id"])
                    st.session_state.wrong_answered_correctly = True
                    st.session_state.wrong_success_message = "Harika! Bu soruyu yanlışlar listesinden çıkardım. 🌟"
                    st.rerun()
                else:
                    st.error("❌ Bu soru hâlâ takılıyor. Bir daha dene 💖")
