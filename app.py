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
    img = img.convert("RGBA")  # format uyumsuzsa sorun çıkmasın
    img = img.resize((300, int(img.height * 300 / img.width)))
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode()

# Görselleri/SES'i yükle
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
    st.title("🌅 Günaydın - Sabah Testi")
elif now_time >= EVENING_TIME:
    session_type = "evening"
    st.title("🌙 İyi akşamlar - Akşam Testi")
else:
    st.info("Test saati henüz gelmedi (08:00 veya 20:00)")
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

            # ===================== KUTLAMA EKRANI (PEMBE, KONFETİ, KALP, UÇAN KUŞLAR) =====================
components.html(f"""
<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<style>
  :root {{
    --pink-1: #ffa7d6;
    --pink-2: #ff87c6;
    --pink-3: #ff6fb1;
    --heart:  #ff4d88;
  }}

  html, body {{
    height: 100%;
    margin: 0;
    overflow: hidden;
  }}

  /* === PEMBE ARKA PLAN (görseldeki stil) === */
  .celebration {{
    position: fixed;
    inset: 0;
    background:
      radial-gradient(circle at 30% 20%, var(--pink-1), transparent 65%),
      radial-gradient(circle at 70% 80%, var(--pink-2), transparent 55%),
      linear-gradient(180deg, var(--pink-2) 0%, var(--pink-3) 100%);
  }}

  .title {{
    position: absolute;
    top: 6%;
    width: 100%;
    text-align: center;
    font-size: 56px;
    color: #fff;
    font-weight: 800;
    text-shadow: 0 2px 0 #c33f70, 0 6px 14px rgba(0,0,0,.25);
    letter-spacing: .5px;
    z-index: 6;
  }}

  /* === KUŞLAR === */
  .bird {{
    position: absolute;
    width: 120px;
    height: auto;
    z-index: 4;
    will-change: transform, filter;
    /* Tüm kuşu renklendir: */
    filter: hue-rotate(var(--hue,0deg)) saturate(1.35) brightness(1.05)
            drop-shadow(0 6px 10px rgba(0,0,0,.25));
  }}

  /* Sağa doğru dalgalı uçuş */
  @keyframes flyRight {{
    0%   {{ transform: translateX(-15vw) translateY(calc(var(--startY))); }}
    20%  {{ transform: translateX(10vw)  translateY(calc(var(--startY) + 0.7*var(--amp))); }}
    40%  {{ transform: translateX(35vw)  translateY(calc(var(--startY) - 0.7*var(--amp))); }}
    60%  {{ transform: translateX(60vw)  translateY(calc(var(--startY) + 0.7*var(--amp))); }}
    80%  {{ transform: translateX(85vw)  translateY(calc(var(--startY) - 0.7*var(--amp))); }}
    100% {{ transform: translateX(115vw) translateY(calc(var(--startY))); }}
  }}

  /* Sola doğru dalgalı uçuş (kuş yönüne baksın diye scaleX(-1)) */
  @keyframes flyLeft {{
    0%   {{ transform: translateX(115vw) translateY(calc(var(--startY))) scaleX(-1); }}
    20%  {{ transform: translateX(90vw)  translateY(calc(var(--startY) + 0.7*var(--amp))) scaleX(-1); }}
    40%  {{ transform: translateX(65vw)  translateY(calc(var(--startY) - 0.7*var(--amp))) scaleX(-1); }}
    60%  {{ transform: translateX(40vw)  translateY(calc(var(--startY) + 0.7*var(--amp))) scaleX(-1); }}
    80%  {{ transform: translateX(15vw)  translateY(calc(var(--startY) - 0.7*var(--amp))) scaleX(-1); }}
    100% {{ transform: translateX(-15vw) translateY(calc(var(--startY))) scaleX(-1); }}
  }}

  /* === PARÇACIKLAR === */

  /* KONFETİ: aşağıdan yukarı */
  .confetti {{
    position: absolute;
    top: 105vh;               /* başlangıçta ekranın altında */
    width: 8px;
    height: 14px;
    background: #fff;
    opacity: .95;
    z-index: 5;
    pointer-events: none;
    transform: rotate(0deg);
    border-radius: 2px;
    box-shadow: 0 2px 6px rgba(0,0,0,.15);
    animation: rise linear forwards;
  }}
  @keyframes rise {{
    0%   {{ transform: translateY(0) rotate(0deg);   opacity: .98; }}
    100% {{ transform: translateY(-120vh) rotate(360deg); opacity: .9; }}
  }}

  /* KALP: yukarıdan aşağı */
  .heart {{
    position: absolute;
    top: -6vh;
    width: 14px;
    height: 14px;
    transform: rotate(-45deg);
    z-index: 3;
    pointer-events: none;
    animation: fall linear forwards;
  }}
  .heart:before, .heart:after {{
    content: "";
    position: absolute;
    width: 14px; height: 14px;
    background: var(--heart);
    border-radius: 50%;
  }}
  .heart:before {{ left: 7px; }}
  .heart:after  {{ top: -7px; }}
  @keyframes fall {{
    0%   {{ transform: translateY(0) rotate(-45deg);   opacity: .95; }}
    100% {{ transform: translateY(120vh) rotate(-45deg); opacity: .9; }}
  }}

  /* Statik minik serpiştirmeler; görsele benzer doku */
  .static-sprinkles {{
    position: absolute;
    inset: 0;
    z-index: 1;
    background-image:
      radial-gradient(circle 3px at 10% 20%, #ffe0ef 95%, transparent 96%),
      radial-gradient(circle 2.5px at 20% 80%, #ffd2ea 95%, transparent 96%),
      radial-gradient(circle 3px at 80% 30%, #ffe0ef 95%, transparent 96%),
      radial-gradient(circle 2.5px at 60% 60%, #ffd2ea 95%, transparent 96%),
      radial-gradient(circle 3px at 30% 50%, #ffe0ef 95%, transparent 96%),
      radial-gradient(circle 2.5px at 70% 75%, #ffd2ea 95%, transparent 96%);
    opacity: .45;
    pointer-events: none;
  }}
</style>
</head>
<body>
  <div class="celebration" id="celebration">
      <div class="static-sprinkles"></div>
      <div class="title">👑 Harikasın 👑</div>
      <audio id="budgieSound" src="data:audio/mp3;base64,{budgie_sound}"></audio>
  </div>

<script>
(function() {{
  const root = document.getElementById('celebration');

  // Ses
  const sound = document.getElementById("budgieSound");
  sound.play().catch(()=>{{}});

  // === UÇAN MUHABBET KUŞLARI ===
  const BIRD_COUNT = 12;
  const hues = [0, 35, 90, 180, 220, 290];

  function rnd(min, max) {{ return Math.random() * (max - min) + min; }}

  for (let i = 0; i < BIRD_COUNT; i++) {{
    const bird = document.createElement('img');
    bird.src = "data:image/png;base64,{budgie_img}";
    bird.className = 'bird';

    const startY = Math.floor(rnd(5, 85));       // 5..85 vh
    const amp    = Math.floor(rnd(6, 18));       // 6..18 vh
    const size   = rnd(90, 140);                 // px
    const hue    = hues[Math.floor(Math.random()*hues.length)];
    const dur    = rnd(3, 6).toFixed(2);         // 3..6 sn
    const delay  = rnd(0, 2).toFixed(2);

    bird.style.setProperty('--startY', startY + 'vh');
    bird.style.setProperty('--amp', amp + 'vh');
    bird.style.setProperty('--hue', hue + 'deg');
    bird.style.width = size + 'px';

    if (Math.random() < 0.5) {{
      bird.style.animation = `flyRight ${dur}s linear ${delay}s infinite`;
    }} else {{
      bird.style.animation = `flyLeft  ${dur}s linear ${delay}s infinite`;
    }}

    root.appendChild(bird);
  }}

  // === KONFETİ (Aşağıdan Yukarı) ===
  const CONFETTI_COUNT = 130;
  const confettiColors = ['#ffffff', '#ffd54f', '#ff7abf', '#8be9ff', '#bfff7a', '#ffc1e3'];

  for (let i = 0; i < CONFETTI_COUNT; i++) {{
    const c = document.createElement('div');
    c.className = 'confetti';
    c.style.left = rnd(0, 100) + 'vw';
    c.style.background = confettiColors[Math.floor(Math.random()*confettiColors.length)];
    c.style.width  = rnd(6, 10) + 'px';
    c.style.height = rnd(10, 18) + 'px';
    c.style.animationDuration = rnd(3, 7).toFixed(2) + 's';
    c.style.animationDelay    = rnd(0, 3).toFixed(2) + 's';
    c.style.transform = `rotate(${rnd(0,360)}deg)`;
    root.appendChild(c);
  }}

  // === KALPLER (Yukarıdan Aşağı) ===
  const HEART_COUNT = 45;
  for (let i = 0; i < HEART_COUNT; i++) {{
    const h = document.createElement('div');
    h.className = 'heart';
    h.style.left = rnd(0, 100) + 'vw';
    h.style.animationDuration = rnd(4, 8).toFixed(2) + 's';
    h.style.animationDelay    = rnd(0, 4).toFixed(2) + 's';
    h.style.opacity = (0.7 + Math.random()*0.3).toFixed(2);
    root.appendChild(h);
  }}
}})();
</script>
</body>
</html>
""", height=900)
</style>
</head>
<body>
  <div class="celebration" id="celebration">
      <div class="static-sprinkles"></div>
      <div class="title">👑 Harikasın 👑</div>
      <audio id="budgieSound" src="data:audio/mp3;base64,{budgie_sound}"></audio>
  </div>

<script>
(function() {{
  const root = document.getElementById('celebration');

  // ====== Ses
  const sound = document.getElementById("budgieSound");
  sound.play().catch(()=>{{}});

  // ====== Renk setleri (tam kuşa uygulanır)
  const hueSet = [0, 35, 90, 180, 220, 290];

  // ====== Uçan kuşlar
  const BIRD_COUNT = 12;
  for (let i = 0; i < BIRD_COUNT; i++) {{
    const bird = document.createElement('img');
    bird.src = "data:image/png;base64,{budgie_img}";
    bird.className = 'bird';

    // Başlangıç yüksekliği ve dalga genliği
    const startY = Math.floor(Math.random() * 80);   // 0..80 vh
    const amp    = Math.floor(6 + Math.random() * 12); // 6..18 vh
    bird.style.setProperty('--startY', startY + 'vh');
    bird.style.setProperty('--amp', amp + 'vh');

    // Boyut ufak varyasyonlar
    const size = 100 + Math.random() * 40; // px
    bird.style.width = size + 'px';

    // Renk – tüm görsele filtre uygula
    const hue = hueSet[Math.floor(Math.random() * hueSet.length)];
    bird.style.filter = `hue-rotate(${hue}deg) saturate(1.25) drop-shadow(0 6px 10px rgba(0,0,0,.25))`;

    // Hız
    const duration = (3 + Math.random() * 3).toFixed(2); // 3..6 s

    // Yön
    if (Math.random() < 0.5) {{
      bird.style.animation = `flyRight ${duration}s linear infinite`;
    }} else {{
      bird.style.animation = `flyLeft ${duration}s linear infinite`;
    }}

    // Rastgele bir gecikme
    bird.style.animationDelay = `${Math.random()*2}s`;
    root.appendChild(bird);
  }}

  // ====== Konfeti + Kalpler
  const CONFETTI_COUNT = 140;
  const HEART_COUNT    = 40;

  function rand(min, max) {{ return Math.random() * (max - min) + min; }}

  const confettiColors = ['#ffffff', '#ffd54f', '#ff7abf', '#8be9ff', '#bfff7a', '#ffc1e3'];

  for (let i = 0; i < CONFETTI_COUNT; i++) {{
    const c = document.createElement('div');
    c.className = 'confetti';
    c.style.left = rand(0, 100) + 'vw';
    c.style.background = confettiColors[Math.floor(Math.random()*confettiColors.length)];
    c.style.transform = `rotate(${rand(0, 360)}deg)`;
    c.style.animation = `fall ${rand(3, 7).toFixed(2)}s linear ${rand(0, 3).toFixed(2)}s infinite`;
    c.style.width  = rand(6, 10) + 'px';
    c.style.height = rand(10, 18) + 'px';
    root.appendChild(c);
  }}

  for (let i = 0; i < HEART_COUNT; i++) {{
    const h = document.createElement('div');
    h.className = 'heart';
    h.style.left = rand(0, 100) + 'vw';
    h.style.animationDuration = rand(4, 8).toFixed(2) + 's';
    h.style.animationDelay    = rand(0, 4).toFixed(2) + 's';
    h.style.opacity = (0.7 + Math.random()*0.3).toFixed(2);
    root.appendChild(h);
  }}

}})();
</script>
</body>
</html>
            """, height=900)
            # ===================== KUTLAMA EKRANI SONU =====================

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
