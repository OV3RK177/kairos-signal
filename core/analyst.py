import pandas as pd
import clickhouse_connect
import psycopg2
import os
import time
from dotenv import load_dotenv
from tabulate import tabulate

load_dotenv()
CH_HOST = os.getenv('CLICKHOUSE_HOST', 'localhost')
CH_PASS = os.getenv('CLICKHOUSE_PASSWORD', 'kairos') 
PG_HOST = os.getenv('POSTGRES_HOST', 'localhost')
PG_PASS = os.getenv('POSTGRES_PASSWORD', 'kairos') 

# The Rosetta Stone: Linking ClickHouse Slugs to Postgres Slugs
LINK_MAP = {
    'dimo': 'dimo', 'flux': 'flux', 'mysterium': 'myst',
    'helium': 'helium', 'helium-iot': 'iot', 'helium-mobile': 'mobile',
    'render': 'render', 'grass': 'grass', 'hivemapper': 'honey'
}

def analyze():
    print("... Establishing Neural Link ...")
    
    # 1. PHYSICAL DATA (ClickHouse)
    try:
        client = clickhouse_connect.get_client(host=CH_HOST, port=8123, username='default', password=CH_PASS)
        # Get last 24h of node counts
        q_ch = """
        SELECT project_slug, metric_name, argMax(metric_value, timestamp) as val 
        FROM metrics 
        WHERE timestamp > now() - INTERVAL 24 HOUR 
        AND (metric_name LIKE '%node%' OR metric_name LIKE '%vehicle%' OR metric_name LIKE '%gateway%')
        GROUP BY project_slug, metric_name
        """
        df_phy = client.query_df(q_ch)
        df_phy['link_key'] = df_phy['project_slug'].map(LINK_MAP).fillna(df_phy['project_slug'])
    except Exception as e:
        print(f"Physical Layer Down: {e}")
        return

    # 2. FINANCIAL DATA (Postgres)
    try:
        conn = psycopg2.connect(host=PG_HOST, database="kairos_meta", user="doadmin", password=PG_PASS)
        # Get latest price
        q_pg = """
        SELECT DISTINCT ON (project) project, value as price 
        FROM live_metrics 
        WHERE metric = 'price_usd' AND time > NOW() - INTERVAL '24 hours'
        ORDER BY project, time DESC
        """
        df_fin = pd.read_sql(q_pg, conn)
    except Exception as e:
        print(f"Financial Layer Down: {e}")
        return

    # 3. MERGE & CALCULATE
    merged = pd.merge(df_phy, df_fin, left_on='link_key', right_on='project', how='left')
    
    report = []
    for _, row in merged.iterrows():
        status = "✅ ACTIVE"
        if pd.isna(row['price']):
            status = "📡 ORPHAN (No Price)"
            row['price'] = 0.0
        
        # Simple ratio for now (Nodes per Dollar) - Higher is better value
        value_ratio = 0
        if row['price'] > 0:
            value_ratio = row['val'] / row['price']

        report.append({
            "ASSET": row['link_key'].upper(),
            "HARDWARE": f"{int(row['val']):,}",
            "METRIC": row['metric_name'],
            "PRICE": f"${row['price']:.4f}",
            "VALUE_SCORE": int(value_ratio),
            "STATUS": status
        })

    final = pd.DataFrame(report).sort_values(by="VALUE_SCORE", ascending=False)
    print("\n>>> KAIROS INTELLIGENCE PRODUCT <<<")
    print(tabulate(final, headers="keys", tablefmt='github', showindex=False))

if __name__ == "__main__":
    analyze()
