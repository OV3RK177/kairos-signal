import os
import clickhouse_connect
from dotenv import load_dotenv
from tabulate import tabulate

load_dotenv()
CH_HOST = os.getenv('CLICKHOUSE_HOST', 'localhost')
CH_PASS = os.getenv('CLICKHOUSE_PASSWORD', 'kairos')

def inspect_schema_and_data():
    try:
        client = clickhouse_connect.get_client(host=CH_HOST, port=8123, username='default', password=CH_PASS)
        print(f"🔍 INSPECTING SCHEMA @ {CH_HOST}\n")

        # 1. METRICS TABLE RECON
        print("📋 SCHEMA: metrics")
        try:
            schema = client.query("DESCRIBE metrics")
            print(tabulate(schema.result_rows, headers=["Column", "Type", "Default_Type", "Default_Expression", "Comment", "Codec_Expression", "TTL_Expression"], tablefmt="simple"))
        except Exception as e:
            print(f"⚠️ Schema Error: {e}")

        print("\n" + "="*60 + "\n")

        # 2. DATA PEEK (Blind Select)
        print("🐝 LATEST SWARM DATA (SELECT * LIMIT 5)")
        try:
            # We use SELECT * to avoid guessing column names
            data = client.query("SELECT * FROM metrics ORDER BY timestamp DESC LIMIT 5")
            # We can't guarantee column order, but tabulate handles it
            print(tabulate(data.result_rows, headers=data.column_names, tablefmt="psql"))
        except Exception as e:
            print(f"⚠️ Read Error: {e}")

        print("\n" + "="*60 + "\n")

        # 3. SOLANA RECHECK
        print("🔥 LATEST SOLANA DATA")
        try:
            data = client.query("SELECT * FROM solana_firehose ORDER BY timestamp DESC LIMIT 5")
            print(tabulate(data.result_rows, headers=data.column_names, tablefmt="psql"))
        except Exception as e:
             print(f"⚠️ Read Error: {e}")

    except Exception as e:
        print(f"💥 CONNECTION ERROR: {e}")

if __name__ == "__main__":
    inspect_schema_and_data()
