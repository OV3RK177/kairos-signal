import streamlit as st
import clickhouse_connect
import pandas as pd
import time
import os
from datetime import datetime

# --- CONFIG ---
# Force correct internal Docker hostname
CH_HOST = os.getenv('CLICKHOUSE_HOST', 'clickhouse-server')
CH_PASS = os.getenv('CLICKHOUSE_PASSWORD', 'kairos')

st.set_page_config(page_title="Kairos Mission Control", layout="wide", page_icon="🦅")

# --- CUSTOM CSS ---
st.markdown("""
    <style>
        .stMetric { background-color: #0E1117; padding: 15px; border-radius: 5px; border: 1px solid #303030; }
        [data-testid="stHeader"] { background-color: #000000; }
    </style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_client():
    return clickhouse_connect.get_client(host=CH_HOST, port=8123, username='default', password=CH_PASS)

def load_data():
    try:
        client = get_client()
        
        # 1. Recent Signals
        q_signals = "SELECT * FROM signal_ledger ORDER BY signal_time DESC LIMIT 50"
        df_signals = client.query_df(q_signals)
        
        # 2. Stats
        q_stats = """
        SELECT 
            count() as total,
            countIf(status = 'CLOSED') as closed,
            countIf(pnl_pct > 0 AND status = 'CLOSED') as wins
        FROM signal_ledger
        """
        df_stats = client.query_df(q_stats)
        
        return df_signals, df_stats
    except Exception as e:
        st.error(f"DB Connection Failed: {e}")
        return pd.DataFrame(), pd.DataFrame()

# --- HEADER ---
st.title("🦅 KAIROS // MISSION CONTROL")
st.caption(f"Connected to: {CH_HOST}")

# --- AUTO REFRESH ---
if st.button("🔄 Refresh Data"):
    st.rerun()

# --- MAIN LOOP ---
df_signals, df_stats = load_data()

if not df_stats.empty:
    total = df_stats.iloc[0]['total']
    closed = df_stats.iloc[0]['closed']
    wins = df_stats.iloc[0]['wins']
    win_rate = (wins / closed * 100) if closed > 0 else 0.0
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Signals", total)
    c2.metric("Closed Trades", closed)
    c3.metric("Win Rate", f"{win_rate:.1f}%")
    c4.metric("Active Signals", total - closed)

st.divider()

# --- LIVE FEED ---
st.subheader("📡 Live Signal Feed")
if not df_signals.empty:
    # Color code the actions
    def color_action(val):
        color = '#00FF00' if val == 'BUY' else '#FF0000'
        return f'color: {color}; font-weight: bold'
    
    st.dataframe(
        df_signals.style.applymap(color_action, subset=['action']),
        use_container_width=True,
        hide_index=True
    )
else:
    st.info("Waiting for first signal...")

