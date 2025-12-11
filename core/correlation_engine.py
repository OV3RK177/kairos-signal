import clickhouse_connect
import psycopg2
import pandas as pd
import numpy as np
import os
from dotenv import load_dotenv
from tabulate import tabulate

load_dotenv()
CH_HOST = os.getenv('CLICKHOUSE_HOST', 'localhost')
CH_PASS = os.getenv('CLICKHOUSE_PASSWORD', 'kairos') 
PG_HOST = os.getenv('POSTGRES_HOST', 'localhost')
PG_PASS = os.getenv('POSTGRES_PASSWORD', 'kairos') 

# Mapping to link disparate names (e.g. 'dimo' vs 'DIMO')
LINK_MAP = {
    'dimo': 'DIMO', 'flux': 'FLUX', 'mysterium': 'MYST',
    'helium': 'HNT', 'helium-iot': 'IOT', 'helium-mobile': 'MOBILE',
    'render': 'RNDR', 'grass': 'GRASS', 'hivemapper': 'HONEY'
}

def fetch_physical():
    """Get 7 Days of Hardware Stats from ClickHouse"""
    print("... Pulling Physical Layer (ClickHouse) ...")
    try:
        client = clickhouse_connect.get_client(host=CH_HOST, port=8123, username='default', password=CH_PASS)
        query = """
        SELECT toStartOfHour(timestamp) as ts, project_slug, metric_name, avg(metric_value) 
        FROM metrics 
        WHERE timestamp > now() - INTERVAL 7 DAY 
        AND (metric_name LIKE '%node%' OR metric_name LIKE '%vehicle%' OR metric_name LIKE '%gpu%')
        GROUP BY ts, project_slug, metric_name
        ORDER BY ts ASC
        """
        df = client.query_df(query)
        if not df.empty:
            df['ts'] = pd.to_datetime(df['ts']).dt.tz_localize(None)
            # Create unique ID: "DIMO_connected_vehicles"
            df['key'] = df['project_slug'].map(LINK_MAP).fillna(df['project_slug']).str.upper() + "_" + df['metric_name']
            return df.pivot_table(index='ts', columns='key', values='avg(metric_value)')
    except Exception as e:
        print(f"Physical Data Error: {e}")
    return pd.DataFrame()

def fetch_financial():
    """Get 7 Days of Price Action from Postgres"""
    print("... Pulling Financial Layer (Postgres) ...")
    try:
        conn = psycopg2.connect(host=PG_HOST, database="kairos_meta", user="doadmin", password=PG_PASS)
        query = """
        SELECT 
            to_timestamp(floor((extract('epoch' from time) / 3600 )) * 3600) as ts, 
            project, AVG(value) 
        FROM live_metrics 
        WHERE time > NOW() - INTERVAL '7 days' 
        AND metric = 'price_usd'
        GROUP BY 1, 2 ORDER BY 1 ASC
        """
        df = pd.read_sql(query, conn)
        conn.close()
        
        if not df.empty:
            df['ts'] = pd.to_datetime(df['ts']).dt.tz_localize(None)
            df['key'] = df['project'].str.upper() + "_PRICE"
            return df.pivot_table(index='ts', columns='key', values='avg')
    except Exception as e:
        print(f"Financial Data Error: {e}")
    return pd.DataFrame()

def analyze():
    # 1. Load Data
    df_phys = fetch_physical()
    df_fin = fetch_financial()
    
    if df_phys.empty and df_fin.empty:
        print("❌ CRITICAL: Both databases returned zero rows for the last 7 days.")
        return

    # 2. FUSION (Merge on Time)
    # We use an outer join to keep all history, then forward fill gaps
    print(f"... Fusing Datasets ({len(df_phys)} phys rows, {len(df_fin)} fin rows) ...")
    merged = pd.merge(df_phys, df_fin, left_index=True, right_index=True, how='outer')
    merged = merged.ffill().bfill() # Fill gaps to allow correlation
    
    if len(merged) < 5:
        print(f"❌ Not enough overlapping history ({len(merged)} hours). Need more uptime.")
        return

    # 3. CORRELATION MATRIX
    print("... 🕸️  Calculating Pearson Correlations ...")
    corr = merged.corr(method='pearson')
    
    signals = []
    columns = corr.columns
    
    for i in range(len(columns)):
        for j in range(i+1, len(columns)):
            col1 = columns[i]
            col2 = columns[j]
            
            # Smart Filter: We only care about Cross-Domain correlations
            # (e.g. Price vs Node Count). We don't care about Price vs Price.
            type1 = "PRICE" if "PRICE" in col1 else "PHYS"
            type2 = "PRICE" if "PRICE" in col2 else "PHYS"
            
            if type1 == type2: continue 
            
            # Check Asset Matching (Are we looking at DIMO vs DIMO? or DIMO vs FLUX?)
            asset1 = col1.split('_')[0]
            asset2 = col2.split('_')[0]
            
            score = corr.iloc[i, j]
            
            # Thresholds for "Interesting" Data
            if abs(score) > 0.5: 
                signal_type = "UNKNOWN"
                if score > 0.8: signal_type = "🔗 STRONG SYNC (Growth = Price)"
                elif score < -0.8: signal_type = "❌ INVERSE (Growth = Dump?)"
                elif asset1 == asset2: signal_type = "✅ ORGANIC ALIGNMENT"
                else: signal_type = "⚠️ SPURIOUS / SECTOR MOVE"

                signals.append({
                    "ASSET_A": col1,
                    "ASSET_B": col2,
                    "CORRELATION": round(score, 4),
                    "SIGNAL": signal_type
                })

    # 4. REPORT
    if not signals:
        print("No strong correlations found yet (Data might be too flat/stable).")
    else:
        final = pd.DataFrame(signals).sort_values(by='CORRELATION', key=abs, ascending=False)
        print("\n>>> KAIROS DEEP CORRELATION MATRIX <<<")
        print(tabulate(final.head(20), headers="keys", tablefmt='github', showindex=False))

if __name__ == "__main__":
    analyze()
