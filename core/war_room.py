import streamlit as st
import pandas as pd
import clickhouse_connect
import os

st.set_page_config(page_title="KAIROS", layout="wide", page_icon="👁️")
CH_HOST = os.getenv('CLICKHOUSE_HOST', 'localhost')

try:
    client = clickhouse_connect.get_client(host=CH_HOST, username='default', password='kairos')
except:
    st.error("🔌 Database Offline"); st.stop()

st.title("👁️ KAIROS: LIVE DATA FEED")
st.markdown("---")

# 1. DATA DIAGNOSTICS
with st.expander("🛠️ SYSTEM DIAGNOSTICS (Click to Open)", expanded=False):
    try:
        count_q = "SELECT count() FROM metrics"
        total_rows = client.query(count_q).result_rows[0][0]
        st.write(f"**Total Data Points:** {total_rows}")
        st.write("Latest 5 Entries:")
        st.dataframe(client.query_df("SELECT timestamp, project_slug, metric_name, metric_value FROM metrics ORDER BY timestamp DESC LIMIT 5"))
    except Exception as e: st.error(f"Read Error: {e}")

st.markdown("---")

# 2. MARKETS (Fail-Safe: Shows ANY recent data)
c1, c2 = st.columns(2)

with c1:
    st.subheader("📈 STOCKS")
    try:
        # Get latest price for STOCK_ assets, ignoring time limits
        q = """
        SELECT 
            replace(project_slug, 'STOCK_', '') as Ticker, 
            argMax(metric_value, timestamp) as Price_USD,
            max(timestamp) as Last_Updated
        FROM metrics 
        WHERE project_slug LIKE 'STOCK_%' AND metric_name = 'price_usd'
        GROUP BY project_slug 
        ORDER BY Price_USD DESC
        """
        st.dataframe(client.query_df(q), use_container_width=True)
    except: st.warning("No Stock Data")

with c2:
    st.subheader("🪙 CRYPTO (Top 20)")
    try:
        q = """
        SELECT 
            project_slug as Asset, 
            argMax(metric_value, timestamp) as Market_Cap,
            max(timestamp) as Last_Updated
        FROM metrics 
        WHERE metric_name = 'market_cap' 
        GROUP BY project_slug 
        ORDER BY Market_Cap DESC 
        LIMIT 20
        """
        st.dataframe(client.query_df(q), use_container_width=True)
    except: st.warning("No Crypto Data")

st.markdown("---")

# 3. SHADOW MARKET (Insiders)
st.subheader("🕵️ SHADOW MARKET")
c1, c2 = st.columns(2)
with c1:
    try:
        # Show last 10 insider buys, ANY time
        q = """
        SELECT timestamp, replace(project_slug, 'INSIDER_', '') as Ticker, metric_value as Amount 
        FROM metrics 
        WHERE project_slug LIKE 'INSIDER_%' 
        ORDER BY timestamp DESC LIMIT 10
        """
        st.dataframe(client.query_df(q), use_container_width=True, hide_index=True)
    except: pass
with c2:
    try:
        q = """
        SELECT timestamp, replace(project_slug, 'GOV_', '') as Ticker 
        FROM metrics 
        WHERE project_slug LIKE 'GOV_%' 
        ORDER BY timestamp DESC LIMIT 10
        """
        st.dataframe(client.query_df(q), use_container_width=True, hide_index=True)
    except: pass

# 4. PHYSICAL WORLD
st.subheader("🌍 DEPIN SECTOR")
try:
    q = """
    SELECT project_slug as Network, argMax(metric_value, timestamp) as Cap 
    FROM metrics 
    WHERE metric_name='market_cap' 
    GROUP BY project_slug 
    ORDER BY Cap DESC LIMIT 20
    """
    st.bar_chart(client.query_df(q).set_index('Network'))
except: pass
