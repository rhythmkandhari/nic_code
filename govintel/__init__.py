"""Shared helpers for the GovINTEL.AI Streamlit app."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT
NIC_CSV = ROOT / "final_k" / "NIC_5digit.csv"
