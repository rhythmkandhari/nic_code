#.\venv\Scripts\activate
import os
from html import escape
import streamlit as st
import pandas as pd
import speech_recognition as sr
import torch
from gpt4all import GPT4All
from sentence_transformers import SentenceTransformer, util
from deep_translator import GoogleTranslator
from final_k.local_db import get_connection


st.set_page_config(page_title="GovINTEL.AI · NIC Code Finder", page_icon="🏷️", layout="wide")

# Stops Streamlit's file watcher from crashing on torch.classes ("Examining the path of torch.classes raised")
torch.classes.__path__ = []

st.session_state.setdefault("is_authenticated", False)
st.session_state.setdefault("user_email", "anonymous")
st.session_state.setdefault("query", "")


# ───────────────────────── Models & data ─────────────────────────

@st.cache_resource
def load_gpt4all():
    # allow_download=False: load the local file without fetching the model list from gpt4all.io
    name = "Llama-3.2-1B-Instruct-Q4_0.gguf"
    path = os.path.join(os.path.expanduser("~"), ".cache", "gpt4all")
    # cuda is ~8x faster than kompute (Vulkan) on the RTX 3050 Ti; needs `pip install gpt4all[cuda]`
    for device in ("cuda", "kompute", "cpu"):
        try:
            m = GPT4All(name, model_path=path, allow_download=False, device=device)
            print(f"GPT4All loaded on {device}: {m.device or 'CPU'}")
            return m
        except Exception as e:
            print(f"GPT4All could not load on {device} ({e})")
            if device == "cuda":
                print("  -> CUDA libraries missing in this Python environment. Start the app with run.bat "
                      "(uses the project venv) for full GPU speed.")
    raise RuntimeError("Could not load the GPT4All model on any device")

@st.cache_resource
def load_sentence_transformer():
    return SentenceTransformer("all-MiniLM-L6-v2").to("cpu")

@st.cache_resource
def load_nic_data(file_path="final_k/NIC_5digit.csv"):
    """NIC table plus one embedding per description, computed once and cached."""
    nic = pd.read_csv(file_path)
    nic["NICcode"] = nic["NICcode"].astype(str).str.zfill(5)  # Ensure 5-digit NIC codes
    embeddings = semantic_model.encode(
        nic["NIC description"].tolist(), convert_to_tensor=True, dtype=torch.float32
    ).cpu()
    return nic, embeddings

model = load_gpt4all()
semantic_model = load_sentence_transformer()
df, nic_embeddings = load_nic_data()

# NIC 2008 sections, by range of the first two digits (division)
NIC_SECTIONS = [
    (1, 3, "A", "Agriculture, forestry & fishing"),
    (5, 9, "B", "Mining & quarrying"),
    (10, 33, "C", "Manufacturing"),
    (35, 35, "D", "Electricity, gas & steam supply"),
    (36, 39, "E", "Water supply & waste management"),
    (41, 43, "F", "Construction"),
    (45, 47, "G", "Wholesale & retail trade"),
    (49, 53, "H", "Transportation & storage"),
    (55, 56, "I", "Accommodation & food service"),
    (58, 63, "J", "Information & communication"),
    (64, 66, "K", "Financial & insurance"),
    (68, 68, "L", "Real estate"),
    (69, 75, "M", "Professional, scientific & technical"),
    (77, 82, "N", "Administrative & support services"),
    (84, 84, "O", "Public administration & defence"),
    (85, 85, "P", "Education"),
    (86, 88, "Q", "Health & social work"),
    (90, 93, "R", "Arts, entertainment & recreation"),
    (94, 96, "S", "Other service activities"),
    (97, 98, "T", "Households as employers"),
    (99, 99, "U", "Extraterritorial organisations"),
]

def nic_section(code):
    division = int(code[:2])
    for lo, hi, letter, name in NIC_SECTIONS:
        if lo <= division <= hi:
            return f"Section {letter} · {name}"
    return ""


# ───────────────────────── Search logic ─────────────────────────

def refine_query(details):
    """Refine user query into a structured format using GPT-4All"""
    prompt = f"Convert the following business description into a structured search query: {details}"
    response = model.generate(prompt, max_tokens=50)
    return response.strip()

def search_nic(details, top_n=5):
    """Return the top_n most similar NIC codes as dicts with code, description and score (0-1)."""
    refined_query = refine_query(details)
    query_embedding = semantic_model.encode([refined_query], convert_to_tensor=True, dtype=torch.float32).cpu()
    scores = util.cos_sim(query_embedding, nic_embeddings)[0]
    top = torch.topk(scores, top_n)
    return [
        {"code": df.iloc[i]["NICcode"], "description": df.iloc[i]["NIC description"], "score": max(0.0, s)}
        for s, i in zip(top.values.tolist(), top.indices.tolist())
    ]

def matches_to_text(matches):
    """'code: description' per line — the format stored in the database and the CSV export."""
    return "\n".join(f"{m['code']}: {m['description']}" for m in matches)

def translate_to_english(text):
    """Translate to English; never crashes the page if Google is unreachable."""
    if text.isascii():
        return text  # already English, no translation (or network) needed
    try:
        return GoogleTranslator(source='auto', target='en').translate(text)
    except Exception as e:
        print(f"Google Translate failed ({type(e).__name__}), using original text")
        st.warning("⚠️ Translation is unavailable right now (offline or rate-limited). "
                   "Searching with your original text; results are best in English.")
        return text

def recognize_speech():
    """Returns (text, error_message)."""
    recognizer = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=1)
            audio = recognizer.listen(source, timeout=8, phrase_time_limit=20)
        return recognizer.recognize_google(audio), None
    except sr.WaitTimeoutError:
        return None, "Didn't hear anything. Click Speak and try again."
    except sr.UnknownValueError:
        return None, "Couldn't understand the audio. Please try again."
    except sr.RequestError:
        return None, "Voice input needs an internet connection."
    except Exception as e:
        return None, f"Microphone error: {e}"

def run_search(text):
    with st.spinner("Finding the best-matching NIC codes…"):
        translated = translate_to_english(text)
        matches = search_nic(translated)
    st.session_state["last_search"] = {"query": text, "translated": translated, "matches": matches}
    try:
        with get_connection() as conn:  # commits automatically
            cur = conn.execute(
                """INSERT INTO RESULT_CODES (ACTIVITY_NAME, NIC_CODE, DESCRIPTION, PREDICTED_NIC, USER_NAME)
                   VALUES (?, ?, ?, ?, ?)""",
                (text, "N/A", translated, matches_to_text(matches), st.session_state["user_email"]),
            )
        print("✅ Saved search, entry ID:", cur.lastrowid)
    except Exception as e:
        st.error(f"❌ Saving failed: {e}")
        print("❌ DB Error:", e)


# ───────────────────────── Callbacks ─────────────────────────

EXAMPLES = {
    "🥖 Bakery": "Bakery that makes bread, cakes and biscuits",
    "📱 Phone repair": "Shop that repairs mobile phones and sells accessories",
    "💻 Software": "Company that develops software applications for clients",
    "🐄 Dairy farm": "Dairy farm producing and selling cow milk",
    "🚚 Transport": "Trucking company carrying goods between cities",
    "👗 Clothing store": "Small shop selling readymade clothes",
}

def on_example():
    choice = st.session_state.get("example")
    if choice:
        st.session_state["query"] = EXAMPLES[choice]
        st.session_state["pending_search"] = True
    st.session_state["example"] = None  # un-highlight the chip

def on_voice():
    st.toast("🎙️ Listening… speak now")
    text, error = recognize_speech()
    if text:
        st.session_state["query"] = text
    else:
        st.session_state["notice"] = error


# ───────────────────────── Styles ─────────────────────────

def html(markup, target=None):
    # Strip indentation so Markdown doesn't treat indented HTML as a code block
    (target or st).markdown("".join(line.strip() for line in markup.splitlines()), unsafe_allow_html=True)

html("""
<style>
:root {
  --navy:#14286B; --blue:#1E3A8A; --saffron:#F28C28; --green:#138808;
  --ink:#0F172A; --muted:#5B6475; --line:#E3E8F2;
}
[data-testid="stMainBlockContainer"], .block-container { max-width: 1150px; padding-top: 3.6rem; }
[data-testid="stImage"] img { border-radius: 14px; }

/* Hero */
.hero { position:relative; overflow:hidden; border-radius:20px; padding:2.4rem 2.6rem 2.6rem; margin:.4rem 0 1.4rem;
        background:linear-gradient(135deg,#14286B 0%,#1E3A8A 55%,#2D52BE 100%); color:#fff; }
.hero::before { content:""; position:absolute; right:-80px; top:-90px; width:320px; height:320px; border-radius:50%;
                background:radial-gradient(circle, rgba(242,140,40,.38), transparent 68%); }
.hero::after { content:""; position:absolute; left:0; right:0; bottom:0; height:5px;
               background:linear-gradient(90deg,#FF9933 0 33.3%,#FFFFFF 33.3% 66.6%,#138808 66.6%); }
.hero-badge { display:inline-block; font-size:.78rem; letter-spacing:.03em; padding:.3rem .8rem; border-radius:999px;
              background:rgba(255,255,255,.12); border:1px solid rgba(255,255,255,.25); }
.flag { display:inline-block; width:18px; height:12px; border-radius:2px; margin-right:.5rem; vertical-align:-1px;
        background:linear-gradient(#FF9933 0 33.3%,#FFFFFF 33.3% 66.6%,#138808 66.6%); }
.hero-title { font-size:2.5rem; line-height:1.12; font-weight:800; margin:.9rem 0 .7rem; max-width:760px; }
.hero-title span { color:#FFB66B; }
.hero-sub { color:#DCE3F5; font-size:1.05rem; line-height:1.55; max-width:720px; }
.hero-stats { display:flex; flex-wrap:wrap; gap:2.4rem; margin-top:1.7rem; position:relative; }
.hero-stats div { display:flex; flex-direction:column; }
.hero-stats b { font-size:1.45rem; color:#fff; }
.hero-stats small { font-size:.74rem; color:#B9C4E4; text-transform:uppercase; letter-spacing:.07em; }

/* Cards & inputs */
.st-key-search_card { background:#fff; border:1px solid var(--line); border-radius:16px;
                       box-shadow:0 4px 18px rgba(20,40,107,.06); padding:1.2rem 1.3rem .7rem; }
.st-key-search_card button p { white-space:nowrap; }
.st-key-search_card [data-testid="stWidgetLabel"] p { color:var(--muted); font-size:.82rem; }
[data-testid="stTextInput"] input { font-size:1.05rem; padding:.8rem 1rem; }
[data-testid="stTextInput"] [data-baseweb="input"] { border-radius:12px; }
.stButton button, .stFormSubmitButton button, .stDownloadButton button { border-radius:10px; font-weight:600; min-height:2.9rem; }
button[data-baseweb="tab"] p { font-weight:600; font-size:.98rem; }

/* Section headings */
.eyebrow { color:var(--saffron); font-size:.75rem; font-weight:700; letter-spacing:.12em; text-transform:uppercase; margin-top:1.8rem; }
.section-title { color:var(--ink); font-size:1.35rem; font-weight:750; margin:.2rem 0 .9rem; }
.muted { color:var(--muted); }

/* Results */
.results-head { margin:1.4rem 0 .9rem; }
.results-head .section-title { margin:0; }
.searched-as { color:var(--muted); font-size:.92rem; margin-top:.2rem; }
.result { display:flex; gap:1rem; background:#fff; border:1px solid var(--line); border-radius:14px; padding:1rem 1.2rem;
          margin-bottom:.7rem; box-shadow:0 1px 2px rgba(15,23,42,.04); transition:box-shadow .15s, transform .15s; }
.result:hover { box-shadow:0 8px 22px rgba(20,40,107,.09); transform:translateY(-1px); }
.result.best { border:1.5px solid var(--saffron); box-shadow:0 8px 24px rgba(242,140,40,.13); }
.rank { flex:none; width:36px; height:36px; border-radius:10px; display:flex; align-items:center; justify-content:center;
        background:#EEF2FB; color:var(--blue); font-weight:800; }
.best .rank { background:var(--saffron); color:#fff; }
.r-body { flex:1; min-width:0; }
.r-top { display:flex; align-items:center; flex-wrap:wrap; gap:.5rem; margin-bottom:.3rem; }
.mono { font-family:Consolas, "SFMono-Regular", Menlo, monospace !important; }
.code { font-weight:700; font-size:1.08rem; letter-spacing:.07em; color:var(--navy); background:#EEF2FB; padding:.1rem .55rem; border-radius:6px; }
.tag { font-size:.72rem; font-weight:600; padding:.18rem .6rem; border-radius:999px; background:#F1F5F9; color:var(--muted); }
.tag.best-tag { background:#FFF1E3; color:#B45309; }
.r-desc { color:var(--ink); font-size:1rem; line-height:1.45; }
.meter { display:flex; align-items:center; gap:.6rem; margin-top:.6rem; }
.track { flex:1; max-width:240px; height:6px; border-radius:999px; background:#EDF1F7; overflow:hidden; }
.fill { height:100%; border-radius:999px; background:linear-gradient(90deg,#1E3A8A,#4F7BE8); }
.best .fill { background:linear-gradient(90deg,#F28C28,#F7B977); }
.meter small { color:var(--muted); font-size:.78rem; }
.empty { text-align:center; color:var(--muted); padding:1.6rem 1rem .6rem; }
.empty b { color:var(--ink); }

/* Steps & features */
.grid { display:grid; gap:1rem; }
.grid.three { grid-template-columns:repeat(3,1fr); }
.grid.four { grid-template-columns:repeat(4,1fr); }
@media (max-width:900px) { .grid.three, .grid.four { grid-template-columns:1fr 1fr; } .hero-title { font-size:1.9rem; } }
.tile { background:#fff; border:1px solid var(--line); border-radius:14px; padding:1.2rem 1.25rem; }
.tile .num { color:var(--saffron); font-weight:800; font-size:.8rem; letter-spacing:.1em; }
.tile .ic { width:42px; height:42px; border-radius:11px; display:flex; align-items:center; justify-content:center;
            background:#EEF2FB; font-size:1.25rem; margin-bottom:.75rem; }
.tile .t { color:var(--ink); font-weight:700; font-size:1rem; margin:.25rem 0 .3rem; }
.tile p { color:var(--muted); font-size:.9rem; line-height:1.5; margin:0; }

/* Sidebar history */
.h-item { background:#fff; border:1px solid var(--line); border-radius:10px; padding:.55rem .75rem; margin-bottom:.45rem; }
.h-q { color:var(--ink); font-size:.88rem; font-weight:600; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.h-c { color:var(--muted); font-size:.76rem; margin-top:.15rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.h-c .mono { color:var(--blue); font-weight:700; }

.foot { text-align:center; color:var(--muted); font-size:.82rem; margin-top:2.6rem; padding:1.2rem 0 .4rem; border-top:1px solid var(--line); }
</style>
""")


# ───────────────────────── Header ─────────────────────────

st.image("mospi.png", use_container_width=True)

html(f"""
<div class="hero">
  <span class="hero-badge"><span class="flag"></span>National Industrial Classification · NIC 2008</span>
  <div class="hero-title">Find the right <span>NIC code</span> for any business in seconds</div>
  <div class="hero-sub">Describe what a business does in your own words. GovINTEL.AI reads the description and suggests the best-matching NIC codes, no exact keywords needed.</div>
  <div class="hero-stats">
    <div><b>{len(df):,}</b><small>5-digit codes</small></div>
    <div><b>21</b><small>sections covered</small></div>
    <div><b>Top 5</b><small>matches per search</small></div>
    <div><b>On-device</b><small>AI, works offline</small></div>
  </div>
</div>
""")


# ───────────────────────── Search / Bulk tabs ─────────────────────────

tab_search, tab_bulk = st.tabs(["🔎  Find a code", "📄  Bulk classify (CSV)"])

with tab_search:
    with st.container(key="search_card"):
        with st.form("search_form", border=False):
            c1, c2 = st.columns([4, 1], vertical_alignment="bottom")
            c1.text_input(
                "Describe the business", key="query", max_chars=500, label_visibility="collapsed",
                placeholder="e.g. A small shop that repairs mobile phones and sells accessories",
            )
            submitted = c2.form_submit_button("Search", type="primary", icon=":material/search:",
                                              use_container_width=True)

        e1, e2 = st.columns([4, 1], vertical_alignment="center")
        e1.pills("Try an example", list(EXAMPLES), key="example", on_change=on_example)
        e2.button("Speak", icon=":material/mic:", on_click=on_voice, use_container_width=True,
                  help="Describe the business by voice (needs internet)")

    notice = st.session_state.pop("notice", None)
    if notice:
        st.warning(notice)

    if submitted or st.session_state.pop("pending_search", False):
        text = st.session_state["query"].strip()
        if text:
            run_search(text)
        else:
            st.warning("Please describe the business first.")

    last = st.session_state.get("last_search")
    if last:
        searched_as = ""
        if last["translated"] != last["query"]:
            searched_as = f' · searched as “{escape(last["translated"])}”'
        html(f"""
        <div class="results-head">
          <div class="section-title">Top {len(last["matches"])} matching NIC codes</div>
          <div class="searched-as">for “{escape(last["query"])}”{searched_as}</div>
        </div>
        """)
        cards = []
        for rank, m in enumerate(last["matches"], start=1):
            best = rank == 1
            pct = round(m["score"] * 100)
            best_tag = '<span class="tag best-tag">★ Best match</span>' if best else ""
            cards.append(
                f'<div class="result{" best" if best else ""}">'
                f'<div class="rank">{rank}</div>'
                f'<div class="r-body">'
                f'<div class="r-top"><span class="code mono">{m["code"]}</span>'
                f'<span class="tag">{escape(nic_section(m["code"]))}</span>'
                f'{best_tag}</div>'
                f'<div class="r-desc">{escape(m["description"])}</div>'
                f'<div class="meter"><div class="track"><div class="fill" style="width:{pct}%"></div></div>'
                f'<small>{pct}% similarity</small></div>'
                f'</div></div>'
            )
        html("".join(cards))
    else:
        html("""
        <div class="empty">
          <b>Your matches will appear here.</b><br>
          Type a description above, pick an example, or use voice input.
        </div>
        """)

with tab_bulk:
    html("""
    <div class="section-title" style="margin-top:.6rem">Classify many businesses at once</div>
    <p class="muted">Upload a CSV with two columns and <b>no header row</b>: company name, then business description. Every row gets its top 5 NIC codes, and you can download the result.</p>
    """)
    sample_csv = (
        "Sharma Bakers,Bakery that makes bread cakes and biscuits\n"
        "QuickFix Mobiles,Shop that repairs mobile phones\n"
        "Ganga Logistics,Trucking company carrying goods between cities\n"
    ).encode("utf-8")
    st.download_button("Download sample CSV", sample_csv, "sample_businesses.csv", "text/csv",
                       icon=":material/download:")

    uploaded_file = st.file_uploader("Upload CSV", type=["csv"])
    if uploaded_file:
        df_input = pd.read_csv(uploaded_file, header=None, names=["Company Name", "Details"])
        df_input = df_input.dropna(subset=["Details"]).reset_index(drop=True)
        st.caption(f"{len(df_input)} businesses found in **{uploaded_file.name}**")

        if st.button("Classify all", type="primary", icon=":material/play_arrow:"):
            progress = st.progress(0.0, text="Starting…")
            all_matches = []
            for i, details in enumerate(df_input["Details"], start=1):
                all_matches.append(search_nic(str(details)))
                progress.progress(i / len(df_input), text=f"Classified {i} of {len(df_input)}")
            progress.empty()
            df_input["Top NIC Code"] = [m[0]["code"] for m in all_matches]
            df_input["Top Match"] = [m[0]["description"] for m in all_matches]
            df_input["NIC Codes"] = [matches_to_text(m) for m in all_matches]
            st.session_state["bulk_result"] = (uploaded_file.name, df_input)

        bulk = st.session_state.get("bulk_result")
        if bulk and bulk[0] == uploaded_file.name:
            result_df = bulk[1]
            st.success(f"Classified {len(result_df)} businesses.")
            st.dataframe(result_df[["Company Name", "Details", "Top NIC Code", "Top Match"]],
                         use_container_width=True, hide_index=True)
            st.download_button("Download results CSV", result_df.to_csv(index=False).encode("utf-8-sig"),
                               "processed_nic_codes.csv", "text/csv", type="primary",
                               icon=":material/download:")


# ───────────────────────── How it works / Features ─────────────────────────

html(f"""
<div class="eyebrow">How it works</div>
<div class="section-title">Three steps to the right code</div>
<div class="grid three">
  <div class="tile"><div class="num">STEP 01</div><div class="t">Describe the business</div>
    <p>Type, speak, or upload a CSV. Plain language works; you can also write in Hindi and other languages.</p></div>
  <div class="tile"><div class="num">STEP 02</div><div class="t">AI compares meanings</div>
    <p>The description is compared with all {len(df):,} NIC 2008 activity descriptions by meaning, not keywords.</p></div>
  <div class="tile"><div class="num">STEP 03</div><div class="t">Pick your code</div>
    <p>Review the top 5 matches with their sections and similarity, and choose the best fit.</p></div>
</div>

<div class="eyebrow">Why GovINTEL.AI</div>
<div class="section-title">Built for accurate, fast classification</div>
<div class="grid four">
  <div class="tile"><div class="ic">🧠</div><div class="t">Understands language</div>
    <p>Handles synonyms and everyday phrasing instead of exact keyword matches.</p></div>
  <div class="tile"><div class="ic">⚡</div><div class="t">Fast, on your device</div>
    <p>GPU-accelerated AI runs locally, so results come back in seconds.</p></div>
  <div class="tile"><div class="ic">🔒</div><div class="t">Private by design</div>
    <p>Searches are stored in a local database on this computer, not in the cloud.</p></div>
  <div class="tile"><div class="ic">📜</div><div class="t">History tracking</div>
    <p>Log in to keep a record of past searches and revisit them anytime.</p></div>
</div>

<div class="foot">GovINTEL.AI · Based on the National Industrial Classification (NIC) 2008 · Suggestions should be verified before official use</div>
""")


# ───────────────────────── Sidebar ─────────────────────────

st.sidebar.image("GovINTEL.AI.png", use_container_width=True)
st.sidebar.markdown("#### 📜 Search history")
if st.session_state["is_authenticated"]:
    try:
        with get_connection() as conn:
            history_records = conn.execute(
                "SELECT ACTIVITY_NAME, PREDICTED_NIC FROM RESULT_CODES WHERE USER_NAME = ? ORDER BY ID DESC LIMIT 20",
                (st.session_state["user_email"],),
            ).fetchall()
        if history_records:
            items = []
            for user_input, nic_codes in history_records:
                top_code, _, top_desc = (nic_codes or "").split("\n")[0].partition(": ")
                items.append(
                    f'<div class="h-item"><div class="h-q" title="{escape(user_input)}">{escape(user_input)}</div>'
                    f'<div class="h-c"><span class="mono">{escape(top_code)}</span> · {escape(top_desc)}</div></div>'
                )
            html("".join(items), target=st.sidebar)
        else:
            st.sidebar.info("No history yet.")
    except Exception as e:
        st.sidebar.error(f"Could not load history: {e}")
else:
    st.sidebar.info("Login to see your history.")


if st.sidebar.button("Clear history", icon=":material/delete:", use_container_width=True):
    if st.session_state["is_authenticated"]:
        try:
            with get_connection() as conn:
                conn.execute("DELETE FROM RESULT_CODES WHERE USER_NAME = ?", (st.session_state["user_email"],))
            st.rerun()  # redraw the sidebar with the now-empty history
        except Exception as e:
            st.sidebar.error(f"Error clearing history: {e}")
    else:
        st.sidebar.warning("Login first to clear history.")

st.sidebar.divider()
font_choice = st.sidebar.selectbox("🔤 Choose Font Style:", ["Default", "Dyslexic-Friendly"])
st.session_state["font_style"] = font_choice

dyslexic_font_url = "https://fonts.cdnfonts.com/css/opendyslexic"
if st.session_state["font_style"] == "Dyslexic-Friendly":
    font_import, font_stack = f"@import url('{dyslexic_font_url}');", "'OpenDyslexic', sans-serif"
else:
    font_import, font_stack = "", "'Segoe UI', system-ui, -apple-system, Roboto, Arial, sans-serif"

# Skip Streamlit's icon font (stIconMaterial) and code text (.mono) so they keep their own fonts
st.markdown(f"""<style>{font_import}
*:not([data-testid="stIconMaterial"]):not(.mono) {{ font-family: {font_stack} !important; }}
</style>""", unsafe_allow_html=True)
