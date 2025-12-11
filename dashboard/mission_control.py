import streamlit as st
import pandas as pd
import plotly.express as px
import clickhouse_connect
import os
from dotenv import load_dotenv

st.set_page_config(page_title="KAIROS DEEP SCAN", page_icon="🐙", layout="wide", initial_sidebar_state="collapsed")
load_dotenv()
client = clickhouse_connect.get_client(host=os.getenv('CLICKHOUSE_HOST', 'localhost'), port=8123, username='default', password=os.getenv('CLICKHOUSE_PASSWORD', 'kairos'))

st.title("🐙 KAIROS OVERNIGHT SIMULATION")

# --- 1. LIVE P&L TRACKER ---
st.subheader("💰 LIVE P&L TRACKER")
try:
    ledger_query = "SELECT timestamp, asset, action, signal_price, current_price, pnl_percent FROM signal_ledger WHERE action = 'BUY' ORDER BY timestamp DESC"
    ledger = client.query_df(ledger_query)
    
    if not ledger.empty:
        wins = ledger[ledger['pnl_percent'] > 0]
        win_rate = (len(wins) / len(ledger)) * 100
        
        k1, k2, k3 = st.columns(3)
        k1.metric("Total Trades", len(ledger))
        k2.metric("Win Rate", f"{win_rate:.1f}%")
        k3.metric("Best Trade", f"{ledger['pnl_percent'].max():.2f}%")
        
        st.dataframe(ledger.style.format({"signal_price": "${:.4f}", "current_price": "${:.4f}", "pnl_percent": "{:+.2f}%"}), use_container_width=True)
    else:
        st.info("Waiting for overnight trades...")
except: pass

st.markdown("---")

# --- 2. DEEP SWARM PRICES ---
st.subheader("Tier 3 Assets (The Dark List)")
deep_df = client.query_df("SELECT project_slug, argMax(metric_value, timestamp) as price FROM metrics WHERE metric_name = 'price' GROUP BY project_slug")
if not deep_df.empty:
    st.dataframe(deep_df, use_container_width=True)
