import duckdb
import pandas as pd
import numpy as np
import json
import os
from datetime import datetime
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import StandardScaler

# CONFIG
DB_PATH = "/mnt/volume_nyc3_01/kairos_analytics/kairos_memory.db"
OUTPUT_FILE = "/mnt/volume_nyc3_01/kairos_analytics/deep_correlations.json"

def analyze_matrix():
    print(f"🧬 IGNITING DEEP QUANT ENGINE (PCA)... {datetime.now()}")
    
    # FIX: Open in Read-Only mode to avoid lock conflict
    try:
        con = duckdb.connect(DB_PATH, read_only=True)
    except Exception as e:
        print(f"❌ DB Lock Error: {e}")
        return

    # 1. FETCH THE TAPE (Time-Series Data)
    print("⏳ Aggregating Time-Series from Memory...")
    try:
        query = """
            WITH top_assets AS (
                SELECT unique_id 
                FROM metrics_history 
                GROUP BY unique_id 
                ORDER BY COUNT(*) DESC 
                LIMIT 5000
            )
            SELECT 
                time_bucket(INTERVAL '15 minutes', timestamp) as t,
                unique_id,
                AVG(latest_value) as val
            FROM metrics_history
            WHERE unique_id IN (SELECT unique_id FROM top_assets)
            AND timestamp > now() - INTERVAL '7 DAYS'
            GROUP BY t, unique_id
            ORDER BY t
        """
        df = con.execute(query).fetchdf()
    except Exception as e:
        print(f"❌ Query Failed (Maybe table empty): {e}")
        return

    if df.empty:
        print("❌ Not enough data depth.")
        return

    # 2. PIVOT (The Matrix)
    print("🔄 Pivoting Signal Matrix...")
    matrix = df.pivot(index='t', columns='unique_id', values='val')
    matrix = matrix.pct_change().fillna(0) # Convert prices to Returns
    
    # 3. DIMENSIONALITY REDUCTION (SVD/PCA)
    print("🧮 Computing Eigenvectors...")
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(matrix)
    
    svd = TruncatedSVD(n_components=20, random_state=42)
    svd.fit(X_scaled)
    
    components = pd.DataFrame(svd.components_, columns=matrix.columns)
    
    # 4. FIND THE GHOST LINKS
    print("💎 Mining for Hidden Factors...")
    correlations = []
    
    for factor_idx in range(5): # Top 5 Factors
        factor_row = components.iloc[factor_idx]
        top_positive = factor_row.nlargest(3)
        top_negative = factor_row.nsmallest(3)
        
        correlations.append({
            "factor": f"Hidden_Factor_{factor_idx+1}",
            "explained_variance": f"{svd.explained_variance_ratio_[factor_idx]*100:.2f}%",
            "drivers": top_positive.index.tolist() + top_negative.index.tolist(),
            "insight": "Shared Latent Variable (Sector/Macro/Tech)"
        })

    # 5. SAVE
    with open(OUTPUT_FILE, "w") as f:
        json.dump({
            "timestamp": str(datetime.now()), 
            "total_assets_scanned": len(matrix.columns),
            "factors": correlations
        }, f, indent=2)
        
    print(f"✅ DEEP ANALYSIS COMPLETE. Mapped {len(matrix.columns)} assets.")

if __name__ == "__main__":
    analyze_matrix()
