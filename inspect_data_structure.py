import clickhouse_connect

client = clickhouse_connect.get_client(host='localhost', port=8123, username='default', password='kairos')

print("🧬 KAIROS DATA DNA INSPECTION")
print("--------------------------------------------------")

# 1. Check Table Columns
print("📋 TABLE SCHEMA (metrics):")
schema = client.query("DESCRIBE metrics").result_rows
for col in schema:
    print(f"   - {col[0]} ({col[1]})")

print("\n--------------------------------------------------")

# 2. Inspect the 'price_usd' Soup
print("🍲 TASTING THE SOUP (First 5 rows of 'price_usd'):")
# We select * to see ALL columns, including hidden tags/labels
data = client.query("SELECT * FROM metrics WHERE metric_name = 'price_usd' LIMIT 5").result_rows

if not data:
    print("❌ No rows found for 'price_usd'. Checking 'price'...")
    data = client.query("SELECT * FROM metrics WHERE metric_name = 'price' LIMIT 5").result_rows

if data:
    for row in data:
        print(f"   {row}")
else:
    print("❌ No data found in either 'price_usd' or 'price'.")

print("\n--------------------------------------------------")
print("❓ QUESTION FOR USER: Look at the rows above.")
print("   Which column contains the Ticker/Symbol (e.g., 'BTC', 'AAPL')?")
print("--------------------------------------------------")
