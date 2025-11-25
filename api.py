
import os, json, psycopg2
import google.generativeai as genai
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from psycopg2 import pool
from dotenv import load_dotenv

load_dotenv("/root/kairos-sprint/.env")
# FORCE LOCALHOST
DB_URL = "postgresql://postgres:kairos@localhost:5432/kairos_db"
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

model = None
if GEMINI_KEY:
    try:
        genai.configure(api_key=GEMINI_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
    except: pass

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
templates = Jinja2Templates(directory="/root/kairos-sprint/templates")

try: db_pool = pool.ThreadedConnectionPool(5, 20, dsn=DB_URL)
except: db_pool = None
def get_conn(): return db_pool.getconn()

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request): return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/matrix")
async def get_matrix(page: int = 1):
    # Infinite Scroll Endpoint
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            offset = (page - 1) * 50
            cur.execute(f"SELECT DISTINCT ON (project) project, value, raw_data FROM live_metrics WHERE metric='price_usd' AND time > NOW() - INTERVAL '60 minutes' ORDER BY project, time DESC")
            rows = []
            for r in cur.fetchall():
                try:
                    meta = json.loads(r[2]) if isinstance(r[2], str) else r[2]
                    vol = float(meta.get('vol', 0) or meta.get('volume_24h', 0) or 0)
                    chg = float(meta.get('chg', 0) or meta.get('change_24h', 0) or 0)
                    rows.append({"id": r[0].replace('tradfi_', '').upper(), "price": r[1], "change": chg, "volume": vol})
                except: pass
            rows.sort(key=lambda x: x['volume'], reverse=True)
            return rows[offset:offset+50]
    finally: db_pool.putconn(conn)

@app.get("/api/chart")
async def get_chart(ids: str):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            datasets = []
            labels = []
            colors = ['#10b981', '#3b82f6', '#f97316']
            for i, tid in enumerate(ids.split(',')):
                db_id = f"tradfi_{tid.lower()}" if "NVDA" in tid else tid.lower().replace('btc','bitcoin')
                # Limit history scan to 48h
                cur.execute(f"SELECT time, value FROM live_metrics WHERE (project='{db_id}' OR project='{tid}') AND metric='price_usd' AND time > NOW() - INTERVAL '48 hours' ORDER BY time ASC")
                rows = cur.fetchall()
                if len(rows) > 100: rows = rows[::len(rows)//100]
                if rows:
                    start = rows[0][1]
                    data = [((x[1]-start)/start)*100 for x in rows]
                    if not labels: labels = [x[0].strftime("%d %H:%M") for x in rows]
                    datasets.append({"label": tid.upper(), "data": data, "borderColor": colors[i%3], "borderWidth": 2, "pointRadius": 0})
            return {"labels": labels, "datasets": datasets}
    finally: db_pool.putconn(conn)

@app.get("/api/frame/{type}")
async def get_frame(type: str):
    # Frame Handler
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            if type == 'macro':
                q = "SELECT DISTINCT ON (project) project, value, raw_data FROM live_metrics WHERE project IN ('tradfi_spy','tradfi_qqq','tradfi_btc_usd') ORDER BY project, time DESC"
            elif type == 'compute':
                q = "SELECT DISTINCT ON (project) project, value, raw_data FROM live_metrics WHERE project IN ('render-token','flux','io-net','akash-network') ORDER BY project, time DESC"
            elif type == 'gainers':
                 # Only look at recent price rows which contain change data
                q = "SELECT DISTINCT ON (project) project, value, raw_data FROM live_metrics WHERE metric='price_usd' AND time > NOW() - INTERVAL '60 minutes' ORDER BY project, time DESC"
            else: return []

            cur.execute(q)
            rows = []
            for r in cur.fetchall():
                try:
                    meta = json.loads(r[2]) if isinstance(r[2], str) else r[2]
                    chg = float(meta.get('chg', 0) or meta.get('change_24h', 0) or 0)
                    if type == 'gainers' and abs(chg) < 3: continue
                    rows.append({"id": r[0].replace('tradfi_', '').upper(), "price": r[1], "change": chg})
                except: pass
            
            if type == 'gainers': rows.sort(key=lambda x: x['change'], reverse=True)
            return rows[:20]
    finally: db_pool.putconn(conn)

@app.get("/api/stats")
async def get_stats():
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT project, MAX(value) FROM live_metrics WHERE project IN ('flux_node', 'mysterium_node', 'dimo', 'io-net') GROUP BY project")
            infra = {r[0].upper().replace('_NODE',''): int(r[1]) for r in cur.fetchall()}
            return {"infra": infra}
    finally: db_pool.putconn(conn)

@app.post("/api/ask")
async def ask_ai(payload: dict):
    if not model: return {"response": "AI Offline"}
    try:
        res = model.generate_content(f"Context: {payload.get('context')}. Q: {payload.get('query')}")
        return {"response": res.text}
    except: return {"response": "Error"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
