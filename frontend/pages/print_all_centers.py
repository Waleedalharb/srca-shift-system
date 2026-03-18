# frontend/pages/print_all_centers.py
import streamlit as st
import pandas as pd
from datetime import datetime
import calendar
from utils.constants import SHIFT_TYPES

st.set_page_config(page_title="طباعة جميع المراكز", layout="wide")

st.markdown("""
<style>
@media print {
    .stAppHeader, .stSidebar, .stDeployButton, footer, header,
    .stButton, .stSelectbox, .stNumberInput, .stRadio,
    [data-testid="stDecoration"], [data-testid="stToolbar"] {
        display: none !important;
    }
    .main > div { padding: 0 !important; max-width: 100% !important; }
    body { background: white; font-family: 'Arial', sans-serif; }
    table { border-collapse: collapse; width: 100%; font-size: 10pt; }
    th { background: #1e3c72 !important; color: white !important; }
    td, th { border: 1px solid #dee2e6; padding: 4px; text-align: center; }
}
</style>
""", unsafe_allow_html=True)

st.title("🖨️ تقرير شامل لجميع المراكز")
st.info("هذه صفحة طباعة جميع المراكز - قيد التطوير")