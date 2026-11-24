"""Semantic NIC code search: translate -> (optional LLM refine) -> embed -> cosine top-k."""
from __future__ import annotations

import io
import threading

import streamlit as st
import torch
from sentence_transformers import SentenceTransformer, util

from . import db

EMBED_MODEL = "all-MiniLM-L6-v2"
LLM_MODEL = "Llama-3.2-1B-Instruct-Q4_0.gguf"
_llm_lock = threading.Lock()  # GPT4All is not safe to call from two sessions at once


@st.cache_resource(show_spinner="Loading the embedding model (first run downloads ~90 MB)...")
def load_embedder() -> SentenceTransformer:
    return SentenceTransformer(EMBED_MODEL, device="cpu")


@st.cache_resource(show_spinner="Indexing NIC codes...")
def load_index():
    """Embed every NIC code in the database once; call refresh_index() after edits."""
    rows = db.fetch_all(
        "SELECT NIC_CODE, ACTIVITY_NAME, DESCRIPTION FROM NIC_CODES ORDER BY NIC_CODE"
    )
    texts = [
        f"{r['ACTIVITY_NAME']}. {r['DESCRIPTION']}" if r["ACTIVITY_NAME"] else r["DESCRIPTION"]
        for r in rows
    ]
    emb = load_embedder().encode(
        texts, convert_to_tensor=True, normalize_embeddings=True, batch_size=64
    )
    return rows, emb


def refresh_index() -> None:
    load_index.clear()


@st.cache_resource(show_spinner="Loading the local LLM (first run downloads ~0.8 GB)...")
def load_llm():
    from gpt4all import GPT4All  # imported lazily: only needed when refinement is on

    return GPT4All(LLM_MODEL, device="cpu")


def refine_query(text: str) -> str:
    llm = load_llm()
    system = (
        "You turn business descriptions into a short list of industry and activity "
        "keywords. Reply with the keywords only, comma separated, nothing else."
    )
    with _llm_lock, llm.chat_session(system_prompt=system):
        out = llm.generate(text, max_tokens=40, temp=0)
    return out.strip() or text


def translate_to_english(text: str) -> str:
    """Translate any language to English; on network failure return the text unchanged."""
    try:
        from deep_translator import GoogleTranslator

        return GoogleTranslator(source="auto", target="en").translate(text) or text
    except Exception:
        return text


def transcribe(audio_bytes: bytes) -> str:
    """Speech-to-text for audio recorded in the browser (WAV from st.audio_input)."""
    import speech_recognition as sr

    recognizer = sr.Recognizer()
    with sr.AudioFile(io.BytesIO(audio_bytes)) as source:
        audio = recognizer.record(source)
    return recognizer.recognize_google(audio)


def find_nic_codes(text: str, top_n: int = 5, use_llm: bool = False) -> list[dict]:
    """Return [{code, description, score}] best matches for an English description."""
    rows, index = load_index()
    if not rows:
        return []
    model = load_embedder()
    query = model.encode([text], convert_to_tensor=True, normalize_embeddings=True)[0]
    if use_llm:
        refined = model.encode(
            [refine_query(text)], convert_to_tensor=True, normalize_embeddings=True
        )[0]
        query = torch.nn.functional.normalize(query + refined, dim=0)
    scores = util.cos_sim(query, index)[0]
    top = torch.topk(scores, k=min(top_n, len(rows)))
    return [
        {
            "code": rows[i]["NIC_CODE"],
            "description": rows[i]["DESCRIPTION"],
            "score": round(float(s), 3),
        }
        for s, i in zip(top.values.tolist(), top.indices.tolist())
    ]


def format_results(results: list[dict]) -> str:
    return "\n".join(f"{r['code']}: {r['description']}" for r in results)
