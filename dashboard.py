import streamlit as st
import clickhouse_connect
import pandas as pd
import subprocess
import time
from datetime import datetime

# PAGE CONFIG
st.set_page_config(page_title="KAIROS LIVE HUD", layout="wide", page_icon="🦁")

# STYLES
st.markdown("""
    <style>
    .metric-card { background-color: #1E1E1E; padding: 15px; border-radius: 10px; border: 1px solid #333; }
    .stDataFrame { border: 1px solid #333; border-radius: 5px; }
    </style>
""", unsafe_allow_html=True)

# DB CONNECTION
@st.cache_resource
def get_client():
    return clickhouse_connect.get_client(host='localhost', port=8123, username='default', password='kairos')

try:
    client = get_client()
except:
    st.error("❌ Database Connection Failed")
    st.stop()

# HEADER
st.title("🦁 KAIROS OPERATIONS CENTER")
st.caption("Autonomous AI Hedge Fund | Live System Monitor")

# MAIN LOOP
placeholder = st.empty()

while True:
    with placeholder.container():
        # 1. FETCH DATA
        try:
            # Scoreboard Data (Standard Query)
            stats_query = """
                SELECT 
                    count() as total, 
                    countIf(pnl_percent > 0) as wins,
                    avg(pnl_percent) as avg_pnl
                FROM signal_ledger
            """
            stats = client.query(stats_query).result_rows[0]
            
            # Active Signals (Dataframe Query)
            signals_df = client.query_df("""
                SELECT timestamp, asset, action, confidence, signal_price, source 
                FROM signals 
                ORDER BY timestamp DESC LIMIT 5
            """)
            
            # Trade Ledger (Dataframe Query)
            ledger_df = client.query_df("""
                SELECT timestamp, asset, signal_price, pnl_percent, status 
                FROM signal_ledger 
                ORDER BY timestamp DESC LIMIT 10
            """)
            
        except Exception as e:
            st.error(f"Data Fetch Error: {e}")
            time.sleep(5)
            continue

        # 2. RENDER SCOREBOARD
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Trades", stats[0])
        
        # Avoid division by zero
        win_rate = (stats[1] / stats[0] * 100) if stats[0] > 0 else 0.0
        c2.metric("Win Rate", f"{win_rate:.1f}%")
        
        c3.metric("Avg PnL", f"{stats[2]:.2f}%")
        
        # Check Services
        try:
            trader_check = subprocess.run(["systemctl", "is-active", "kairos-trader"], capture_output=True, text=True).stdout.strip()
            status_icon = "🟢" if trader_check == "active" else "🔴"
            c4.metric("Trader Status", f"{status_icon} {trader_check.upper()}")
        except:
            c4.metric("Trader Status", "❓ UNKNOWN")

        st.markdown("---")

        # 3. RENDER TABLES
        col_signal, col_ledger = st.columns(2)
        
        with col_signal:
            st.subheader("📡 Brain Signals (Incoming)")
            if not signals_df.empty:
                st.dataframe(signals_df, use_container_width=True, hide_index=True)
            else:
                st.info("No signals yet...")

        with col_ledger:
            st.subheader("💰 Execution Ledger (Filled)")
            if not ledger_df.empty:
                st.dataframe(ledger_df, use_container_width=True, hide_index=True)
            else:
                st.info("No trades executed yet...")

        st.markdown("---")

        # 4. LIVE LOGS (Tail)
        st.subheader("🖥️ System Logs (Live Tail)")
        log_col1, log_col2 = st.columns(2)
        
        with log_col1:
            st.caption("🧠 Cortex (Brain)")
            try:
                logs_brain = subprocess.check_output("journalctl -u kairos-cortex -n 15 --no-pager".split()).decode()
                st.code(logs_brain, language="text")
            except: st.warning("Cannot read Cortex logs")

        with log_col2:
            st.caption("⚔️ Trader (Execution)")
            try:
                logs_trader = subprocess.check_output("journalctl -u kairos-trader -n 15 --no-pager".split()).decode()
                st.code(logs_trader, language="text")
            except: st.warning("Cannot read Trader logs")

        # Timestamp footer
        st.caption(f"Last Update: {datetime.now().strftime('%H:%M:%S')}")
        
    # REFRESH RATE
    time.sleep(2)
