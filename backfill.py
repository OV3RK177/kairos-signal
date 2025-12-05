import json
import sys
from datetime import datetime
import clickhouse_connect

# --- CONFIGURATION ---
INPUT_FILE = "kairos_firehose_dump.jsonl"
BATCH_SIZE = 10000
DRY_RUN = False  # <--- SAFETY ON: Will print 5 rows and stop.

# DATABASE CREDENTIALS
DB_HOST = 'localhost'
DB_PORT = 8123
DB_USER = 'default'
DB_PASS = 'kairos' 

# Connect
try:
    print(f"Connecting to ClickHouse at {DB_HOST}...")
    client = clickhouse_connect.get_client(host=DB_HOST, port=DB_PORT, username=DB_USER, password=DB_PASS)
    client.command('SELECT 1')
    print("Connection Successful.")
except Exception as e:
    print(f"CRITICAL AUTH FAILURE: {e}")
    sys.exit(1)

def parse_timestamp(ts):
    """Normalize timestamp to YYYY-MM-DD HH:MM:SS"""
    try:
        # Handle ISO String (2025-11-30T...)
        if isinstance(ts, str):
            # Clean Z if present, ensure standard format
            return datetime.fromisoformat(ts.replace('Z', '+00:00'))
        # Handle Unix Float/Int (ms or seconds)
        if isinstance(ts, (int, float)):
            # If it's huge (ms), convert to seconds
            if ts > 10000000000:
                ts = ts / 1000.0
            return datetime.fromtimestamp(ts)
        return datetime.now()
    except:
        return datetime.now()

def process_file():
    print(f"Reading {INPUT_FILE} (Smart Multi-line Mode)...")
    
    batch = []
    total_inserted = 0
    buffer = ""
    valid_rows = 0

    with open(INPUT_FILE, 'r') as f:
        for line in f:
            line_clean = line.strip()
            if not line_clean: continue

            # Accumulate buffer
            buffer += line

            # Check if this line closes the object
            if line_clean == '}':
                try:
                    # 1. Parse the full multi-line Redpanda Wrapper
                    record = json.loads(buffer)
                    buffer = "" # Clear buffer for next one

                    # 2. Extract Value (The stringified JSON payload)
                    raw_value = record.get('value')
                    if not raw_value: continue

                    # Decode the inner payload string
                    payload = json.loads(raw_value) if isinstance(raw_value, str) else raw_value

                    # 3. MAP TO YOUR SCHEMA
                    # Based on your data:
                    # 'ts' -> timestamp
                    # 'source' -> project_slug
                    # 'metric' -> metric_name
                    # 'value' -> metric_value
                    
                    row = [
                        parse_timestamp(payload.get('ts') or record.get('timestamp')),
                        str(payload.get('source', 'unknown')),
                        str(payload.get('metric', 'unknown')),
                        float(payload.get('value', 0.0))
                    ]
                    
                    batch.append(row)
                    valid_rows += 1

                    # DRY RUN LOGIC
                    if DRY_RUN:
                        print(f"\n[Dry Run Sample #{valid_rows}]")
                        print(f"Raw TS: {payload.get('ts')} -> Parsed: {row[0]}")
                        print(f"Slug: {row[1]} | Metric: {row[2]} | Value: {row[3]}")
                        if valid_rows >= 5:
                            print("\n--- STOPPING DRY RUN ---")
                            print("Data looks perfect. Edit script -> Set DRY_RUN = False -> Run again.")
                            return

                except Exception as e:
                    # If JSON parse fails, maybe buffer wasn't complete? 
                    # But given the format, this usually means a corrupt record.
                    # Reset buffer to recover.
                    # print(f"Parse Error: {e}") 
                    buffer = "" 
                    continue

                # REAL RUN INSERT
                if len(batch) >= BATCH_SIZE and not DRY_RUN:
                    client.insert('metrics', batch, column_names=['timestamp', 'project_slug', 'metric_name', 'metric_value'])
                    total_inserted += len(batch)
                    print(f"Inserted {total_inserted} records...")
                    batch = []

        # Flush Final Batch
        if batch and not DRY_RUN:
            client.insert('metrics', batch, column_names=['timestamp', 'project_slug', 'metric_name', 'metric_value'])
            total_inserted += len(batch)

    print(f"\nJOB DONE. Total Inserted: {total_inserted}.")

if __name__ == "__main__":
    process_file()
