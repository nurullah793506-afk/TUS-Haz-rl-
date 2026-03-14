import streamlit as st
import json
import os
import re
import hashlib
from datetime import datetime, timedelta
import pytz
from supabase import create_client
import streamlit.components.v1 as components

# ===================== SUPABASE =====================

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

USER_ID = "main_user"

# ===================== AYARLAR =====================
TIMEZONE = pytz.timezone("Europe/Istanbul")
GUNLUK_SORU_SAYISI = 10

# BURAYA İSTEDİĞİN 2 SAATİ GİR
TEST_SAATLERI = ["11:43", "20:00"]

st.set_page_config(page_title="Günün Seçilmiş Soruları", page_icon="🌸")
st.title("🌸 Sonsuza kadar hastanım ben… İyi ki varsın doktorum ❤️🌸")

QUESTIONS_FILE = "questions.json"
MESSAGES_FILE = "messages.json"
PROGRESS_FILE = "progress.json"
WRONG_FILE = "wrong_questions.json"
INFO_FILE = "bilgikarti.json"

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

if "card_show_answer" not in st.session_state:
    st.session_state.card_show_answer = False

if "card_index" not in st.session_state:
    st.session_state.card_index = 0

if "card_order" not in st.session_state:
    st.session_state.card_order = []

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

# ===================== FAVORİ KART YARDIMCILARI =====================
def get_favorite_card_ids():
    result = supabase.table("favorite_cards").select("card_id").eq("user_id", USER_ID).execute()
    if result.data:
        return [item["card_id"] for item in result.data]
    return []

def add_favorite_card(card_id):
    supabase.table("favorite_cards").upsert({
        "user_id": USER_ID,
        "card_id": card_id
    }).execute()

def remove_favorite_card(card_id):
    supabase.table("favorite_cards").delete().eq("user_id", USER_ID).eq("card_id", card_id).execute()

# ===================== ZAMAN YARDIMCILARI =====================
def saat_to_dakika(saat_str):
    saat, dakika = map(int, saat_str.split(":"))
    return saat * 60 + dakika

def get_period_id(now_dt, test_saatleri):
    today_str = now_dt.strftime("%Y-%m-%d")
    simdi_toplam_dakika = now_dt.hour * 60 + now_dt.minute

    sorted_slots = sorted(test_saatleri, key=saat_to_dakika)
    first_slot = sorted_slots[0]
    second_slot = sorted_slots[1]

    first_minutes = saat_to_dakika(first_slot)
    second_minutes = saat_to_dakika(second_slot)

    if simdi_toplam_dakika >= second_minutes:
        active_slot = second_slot
        active_date = today_str
    elif simdi_toplam_dakika >= first_minutes:
        active_slot = first_slot
        active_date = today_str
    else:
        yesterday = now_dt - timedelta(days=1)
        active_slot = second_slot
        active_date = yesterday.strftime("%Y-%m-%d")

    return f"{active_date}_{active_slot}"

# ===================== KART YARDIMCILARI =====================
def clean_info_note(note):
    note = str(note).strip()
    note = note.replace('\\"', '"')
    note = note.strip('"')
    note = re.sub(r"^\s*Bilgi notu:\s*", "", note, flags=re.IGNORECASE)
    return note.strip()

def card_id_from_text(text):
    return hashlib.md5(text.encode("utf-8")).hexdigest()

def prepare_info_cards(notes):
    cleaned = []
    seen = set()

    for note in notes:
        c = clean_info_note(note)
        if c and c not in seen:
            seen.add(c)
            cleaned.append({
                "id": card_id_from_text(c),
                "text": c
            })

    return cleaned

def get_cards():
    cards = prepare_info_cards(info_cards_raw)

    if not cards:
        st.session_state.card_order = []
        st.session_state.card_index = 0
        return []

    current_ids = [card["id"] for card in cards]

    if not st.session_state.card_order:
        st.session_state.card_order = current_ids.copy()
    else:
        # JSON güncellenirse yeni kartları ekle, silinenleri çıkar
        existing = [cid for cid in st.session_state.card_order if cid in current_ids]
        new_ids = [cid for cid in current_ids if cid not in existing]
        st.session_state.card_order = existing + new_ids

    card_map = {card["id"]: card for card in cards}
    ordered_cards = [card_map[cid] for cid in st.session_state.card_order if cid in card_map]

    if st.session_state.card_index >= len(ordered_cards):
        st.session_state.card_index = 0

    return ordered_cards

def go_next_card(cards):
    if not cards:
        return
    if st.session_state.card_index < len(cards) - 1:
        st.session_state.card_index += 1
    st.session_state.card_show_answer = False

def go_prev_card(cards):
    if not cards:
        return
    if st.session_state.card_index > 0:
        st.session_state.card_index -= 1
    st.session_state.card_show_answer = False

# ===================== VERİ YÜKLEME =====================
questions = load_json(QUESTIONS_FILE, [])
questions = sorted(questions, key=lambda x: x.get("id", 0))

messages = load_json(MESSAGES_FILE, [])
info_cards_raw = load_json(INFO_FILE, [])

progress = get_progress()
wrong_ids = get_wrong_ids()
favorite_card_ids = get_favorite_card_ids()

# ===================== ZAMAN KONTROLÜ =====================
now_dt = datetime.now(TIMEZONE)
period_id = get_period_id(now_dt, TEST_SAATLERI)

if progress["last_period"] != period_id:
    progress["last_period"] = period_id
    progress["period_counter"] = 0
    save_progress(progress)

# ===================== SWIPE =====================
query_params = st.query_params
swipe_action = query_params.get("swipe", None)
mode_from_query = query_params.get("mode", None)

# ===================== SIDEBAR =====================
with st.sidebar:
    st.header("📊 İstatistikler")
    st.write(f"✅ Toplam Çözülen: {progress['global_index']}")
    st.write(f"❌ Yanlış Sayısı: {len(wrong_ids)}")
    st.write(f"⭐ Favori Kart: {len(favorite_card_ids)}")

    st.divider()
    mode = st.radio(
        "Mod Seç",
        ["Günün Soruları", "Yanlış Testi", "Bilgi Kartları"]
    )

    st.divider()
    st.write(f"🕒 Test Saatleri: {TEST_SAATLERI[0]} / {TEST_SAATLERI[1]}")
    st.write(f"📌 Aktif Slot: {period_id}")

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

    st.divider()
    if st.checkbox("⭐ Favori Kartlarımı Göster"):
        cards = get_cards()
        favorite_cards = [c for c in cards if c["id"] in favorite_card_ids]

        if not favorite_cards:
            st.info("Henüz favori kartın yok 🌸")
        else:
            for i, card in enumerate(favorite_cards, start=1):
                with st.expander(f"Favori Kart {i}"):
                    st.write(card["text"])

# ===================== MOD 1: GÜNÜN SORULARI =====================
if mode == "Günün Soruları":
    if progress["global_index"] >= len(questions):
        st.success("🎉 İnanılmaz! Tüm sorular bitti. Sen bir şampiyonsun! 💖")
        st.balloons()

    elif progress["period_counter"] >= GUNLUK_SORU_SAYISI:
        st.warning(f"🌸 Bu zaman dilimi için ayrılan {GUNLUK_SORU_SAYISI} soruyu bitirdin.")
        st.info("Bir sonraki zaman diliminde yeni soruların açılacak. Beklemede kal aşkım! ✨")

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

# ===================== MOD 3: BİLGİ KARTLARI =====================
elif mode == "Bilgi Kartları":
    cards = get_cards()

    if not cards:
        st.info("Henüz bilgi kartı yok 🌸")
        st.caption("GitHub projenin içine 'bilgikarti.json' dosyası ekleyip kartlarını oraya yazabilirsin.")
        st.stop()

    # swipe query yakalama
    if swipe_action and mode_from_query == "cards":
        if swipe_action == "next":
            go_next_card(cards)
        elif swipe_action == "prev":
            go_prev_card(cards)
        st.query_params.clear()
        st.rerun()

    # swipe js
    components.html(
        """
        <script>
        const threshold = 80;
        let startX = 0;
        let endX = 0;
        let mouseDown = false;

        function sendSwipe(direction) {
            const url = new URL(window.parent.location.href);
            url.searchParams.set("swipe", direction);
            url.searchParams.set("mode", "cards");
            window.parent.location.href = url.toString();
        }

        document.addEventListener("touchstart", function(e) {
            startX = e.changedTouches[0].screenX;
        }, {passive: true});

        document.addEventListener("touchend", function(e) {
            endX = e.changedTouches[0].screenX;
            const diff = endX - startX;
            if (Math.abs(diff) > threshold) {
                if (diff > 0) {
                    sendSwipe("next");
                } else {
                    sendSwipe("prev");
                }
            }
        }, {passive: true});

        document.addEventListener("mousedown", function(e) {
            mouseDown = true;
            startX = e.screenX;
        });

        document.addEventListener("mouseup", function(e) {
            if (!mouseDown) return;
            mouseDown = false;
            endX = e.screenX;
            const diff = endX - startX;
            if (Math.abs(diff) > threshold) {
                if (diff > 0) {
                    sendSwipe("next");
                } else {
                    sendSwipe("prev");
                }
            }
        });
        </script>
        """,
        height=0,
    )

    current_card = cards[st.session_state.card_index]
    is_favorite = current_card["id"] in favorite_card_ids

    progress_ratio = (st.session_state.card_index + 1) / len(cards)
    st.progress(progress_ratio)
    st.write(f"**Bilgi Kartı {st.session_state.card_index + 1} / {len(cards)}**")
    st.caption("Sağa kaydır → sonraki kart | Sola kaydır → önceki kart")

    st.markdown(
        """
        <style>
        .flash-card {
            background: linear-gradient(135deg, #fff7f9, #f8fbff);
            border-radius: 22px;
            padding: 35px 25px;
            min-height: 260px;
            display: flex;
            align-items: center;
            justify-content: center;
            text-align: center;
            box-shadow: 0 6px 20px rgba(0,0,0,0.08);
            border: 1px solid #eee;
            margin-bottom: 12px;
        }
        .flash-front {
            font-size: 28px;
            font-weight: 700;
            color: #444;
        }
        .flash-back {
            font-size: 27px;
            font-weight: 600;
            color: #111;
            line-height: 1.6;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    if st.session_state.card_show_answer:
        safe_text = current_card["text"].replace("<", "&lt;").replace(">", "&gt;")
        st.markdown(
            f'<div class="flash-card"><div class="flash-back">{safe_text}</div></div>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            '<div class="flash-card"><div class="flash-front">📌 Kartı görmek için çevir</div></div>',
            unsafe_allow_html=True
        )

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        if st.button("⬅️ Önceki Kart", use_container_width=True):
            go_prev_card(cards)
            st.rerun()

    with c2:
        if st.button("👀 Kartı Çevir", use_container_width=True):
            st.session_state.card_show_answer = not st.session_state.card_show_answer
            st.rerun()

    with c3:
        if st.button("Sonraki Kart ➡️", use_container_width=True):
            go_next_card(cards)
            st.rerun()

    with c4:
        fav_text = "⭐ Çıkar" if is_favorite else "🤍 Favori"
        if st.button(fav_text, use_container_width=True):
            if is_favorite:
                remove_favorite_card(current_card["id"])
            else:
                add_favorite_card(current_card["id"])
            st.rerun()
