import pandas as pd
import streamlit as st

from govintel import ASSETS, db, search

st.session_state.setdefault("history", [])  # searches made in this browser session
st.session_state.setdefault("query", "")


def on_voice() -> None:
    """Runs before the rerun, so it can fill the text box with the transcript."""
    audio = st.session_state.get("voice")
    if not audio:
        return
    try:
        st.session_state["query"] = search.transcribe(audio.getvalue())
    except Exception as e:  # no speech, no internet, etc.
        st.session_state["voice_error"] = f"Could not understand the audio ({type(e).__name__})."


def save_search(query: str, english: str, results: list[dict]) -> None:
    try:
        db.execute(
            "INSERT INTO RESULT_CODES (ACTIVITY_NAME, DESCRIPTION, PREDICTED_NIC) "
            "VALUES (:p_query, :p_english, :p_result)",
            {"p_query": query, "p_english": english, "p_result": search.format_results(results)},
        )
    except Exception as e:  # the search result is still shown if saving fails
        st.warning(f"Result not saved to the database: {e}")


def results_table(results: list[dict]) -> None:
    st.dataframe(
        pd.DataFrame(results).rename(
            columns={"code": "NIC code", "description": "Description", "score": "Match"}
        ),
        hide_index=True,
        width="stretch",
        column_config={
            "Match": st.column_config.ProgressColumn(format="%.2f", min_value=0, max_value=1)
        },
    )


# ---------- Sidebar: options and this session's history ----------
with st.sidebar:
    use_llm = st.toggle(
        "Refine query with local LLM",
        value=False,
        help="Rewrites your description as keywords with Llama 3.2 1B (GPT4All) before "
        "searching. Slower; the first use downloads a ~0.8 GB model.",
    )
    st.subheader("📜 Search history")
    if st.session_state["history"]:
        for i, h in enumerate(reversed(st.session_state["history"]), start=1):
            st.markdown(f"**{i}.** {h['query']}  \n🚀 *{h['top']}*")
        if st.button("Clear history"):
            st.session_state["history"] = []
            st.rerun()
    else:
        st.caption("Your searches will appear here.")

# ---------- Header ----------
st.image(str(ASSETS / "mospi.png"), width="stretch")
st.markdown("<h1 style='text-align:center;'>GovINTEL.AI</h1>", unsafe_allow_html=True)
st.caption(
    "Describe a business activity in any language and get the five closest "
    "National Industrial Classification (NIC 2008) codes."
)

# ---------- Single search ----------
st.text_input(
    "Company description",
    key="query",
    placeholder="e.g. We manufacture cotton t-shirts and sell them online",
    max_chars=500,
    label_visibility="collapsed",
)
st.audio_input("🎙️ Or speak your description", key="voice", on_change=on_voice)
if err := st.session_state.pop("voice_error", None):
    st.warning(err)

if st.button("Find NIC Code", type="primary"):
    query = st.session_state["query"].strip()
    if not query:
        st.warning("Please enter a description first.")
    else:
        with st.spinner("Finding NIC codes..."):
            english = search.translate_to_english(query)
            results = search.find_nic_codes(english, top_n=5, use_llm=use_llm)
        st.session_state["last"] = {"query": query, "english": english, "results": results}
        if results:
            st.session_state["history"].append(
                {"query": query, "top": f"{results[0]['code']}: {results[0]['description']}"}
            )
            save_search(query, english, results)

if last := st.session_state.get("last"):
    st.subheader("🏷️ Classified NIC codes")
    if last["english"] != last["query"]:
        st.caption(f"Searched as: *{last['english']}*")
    results_table(last["results"])

# ---------- Bulk CSV ----------
st.divider()
st.header("Upload & process CSV")
st.caption("One row per company. Pick the column that holds the business description.")
uploaded = st.file_uploader("Upload CSV", type=["csv"])
if uploaded:
    if st.session_state.get("csv_file_id") != uploaded.file_id:  # new file: drop old output
        st.session_state["csv_file_id"] = uploaded.file_id
        st.session_state.pop("csv_out", None)
    df_in = pd.read_csv(uploaded)
    if df_in.empty:
        st.warning("The file has no rows.")
    else:
        cols = list(df_in.columns)
        desc_col = st.selectbox("Description column", cols, index=len(cols) - 1)
        translate = st.checkbox("Translate descriptions to English first", value=True)
        if st.button("Process CSV"):
            top_codes, top_descs, scores, all_codes = [], [], [], []
            bar = st.progress(0.0, text="Processing...")
            for n, text in enumerate(df_in[desc_col].fillna("").astype(str), start=1):
                text = text.strip()
                res = []
                if text:
                    english = search.translate_to_english(text) if translate else text
                    res = search.find_nic_codes(english, top_n=5, use_llm=use_llm)
                top_codes.append(res[0]["code"] if res else "")
                top_descs.append(res[0]["description"] if res else "")
                scores.append(res[0]["score"] if res else None)
                all_codes.append(", ".join(r["code"] for r in res))
                bar.progress(n / len(df_in), text=f"Processed {n} of {len(df_in)}")
            out = df_in.assign(
                **{
                    "Top NIC code": top_codes,
                    "Top NIC description": top_descs,
                    "Match": scores,
                    "Top 5 NIC codes": all_codes,
                }
            )
            st.session_state["csv_out"] = out
        if (out := st.session_state.get("csv_out")) is not None:
            st.dataframe(out.head(20), width="stretch", hide_index=True)
            st.download_button(
                "Download processed CSV",
                out.to_csv(index=False).encode("utf-8-sig"),
                file_name="processed_nic_codes.csv",
                mime="text/csv",
            )

# ---------- Footer ----------
st.divider()
st.subheader("Why choose us?")
for col, (title, text) in zip(
    st.columns(4),
    [
        ("⚡ Accuracy", "Semantic search over all 1,304 five-digit NIC 2008 codes."),
        ("⏳ Speed", "Results in about a second once the model is loaded."),
        ("🌐 Any language", "Descriptions are translated to English automatically."),
        ("📄 Bulk mode", "Classify a whole CSV of companies at once."),
    ],
):
    col.markdown(f"**{title}**")
    col.write(text)
