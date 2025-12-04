import pandas as pd
import subprocess
import os
from datetime import datetime

# CONFIG
MATRIX_FILE = "/mnt/volume_nyc3_01/kairos_analytics/kairos_3000_matrix.csv"
OUTPUT_FILE = "/mnt/volume_nyc3_01/kairos_analytics/daily_briefing.md"

def generate_report():
    print("📝 GENERATING INTELLIGENCE REPORT...")
    
    if not os.path.exists(MATRIX_FILE):
        print("❌ Matrix file not found.")
        return
        
    df = pd.read_csv(MATRIX_FILE)
    
    # DETECT COLUMNS (Fix for "KeyError")
    vol_col = 'Volatility_Risk'
    if 'Volatility_Std' in df.columns: vol_col = 'Volatility_Std'
    elif 'volatility' in df.columns: vol_col = 'volatility'
    
    liq_col = 'Liquidity_Count'
    if 'count' in df.columns: liq_col = 'count'
    
    print(f"🔍 Using Columns: Risk='{vol_col}', Vol='{liq_col}'")

    # Filter Data
    top_risk = df.sort_values(by=vol_col, ascending=False).head(20)
    top_volume = df.sort_values(by=liq_col, ascending=False).head(10)
    
    # Construct Prompt
    prompt = f"""
    You are Kairos AI, a quantitative analyst.
    Analyze this real-time market snapshot ({datetime.now()}):

    TOP 20 HIGHEST RISK ASSETS ({vol_col}):
    {top_risk.to_string(index=False)}

    TOP 10 HIGHEST VOLUME ASSETS ({liq_col}):
    {top_volume.to_string(index=False)}

    OUTPUT FORMAT:
    1. EXECUTIVE SUMMARY (1 sentence).
    2. TOP ANOMALY: (Asset Name & Why).
    3. TRADE RECOMMENDATION: (Long/Short & Logic).
    4. RISK WARNING: (What could go wrong).
    """
    
    try:
        cmd = ["ollama", "run", "kimi-k2-thinking:cloud", prompt]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ Ollama Error: {result.stderr}")
            return

        report = result.stdout
        
        with open(OUTPUT_FILE, "w") as f:
            f.write(f"# KAIROS INTELLIGENCE BRIEF\n**Time:** {datetime.now()}\n\n{report}")
            
        print(f"✅ REPORT SAVED: {OUTPUT_FILE}")
        print("-" * 40)
        print(report)
        print("-" * 40)
        
    except Exception as e:
        print(f"❌ Execution Failed: {e}")

if __name__ == "__main__":
    generate_report()
