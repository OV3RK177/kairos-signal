import yfinance as yf
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

class OmniSensorEngine:
    def __init__(self):
        # 1. THE EYES: Physical World Proxies
        # We use ETFs/Futures to "see" the physical world
        self.physical_tickers = {
            "Oil_Inventory_Proxy": "USO",     # United States Oil Fund
            "Global_Shipping": "BDRY",        # Breakwave Dry Bulk Shipping
            "Industrial_Metals": "CPER",      # Copper (Dr. Copper)
            "Agriculture": "DBA"              # Agriculture Fund
        }

        # 2. THE EARS: Macro & Liquidity
        self.macro_tickers = {
            "USD_Liquidity": "M2",            # M2 Money Supply (needs FRED API, using proxy here)
            "US_Dollar": "DX-Y.NYB",          # Dollar Index
            "10Y_Yield": "^TNX",              # 10-Year Treasury Yield
            "Inflation_Expectations": "RINF"  # ProShares Inflation Expectations
        }

        # 3. THE SKIN: Crypto & Risk Appetite
        self.crypto_tickers = {
            "Bitcoin": "BTC-USD",
            "Ethereum": "ETH-USD",
            "Tech_Growth": "QQQ"              # Nasdaq 100 (High Beta)
        }
        
        self.data_window = 365 # Look back 1 year for correlations
        self.master_df = pd.DataFrame()

    def activate_sensors(self):
        """Ingests data from all disparate sources."""
        print("--- [SENSORS HOT] Activating Global Inputs ---")
        
        all_tickers = list(self.physical_tickers.values()) + \
                      list(self.macro_tickers.values()) + \
                      list(self.crypto_tickers.values())
        
        # Batch download for speed
        print(f"Polling {len(all_tickers)} global sensors...")
        data = yf.download(all_tickers, period="1y", interval="1d", progress=False)['Adj Close']
        
        # Rename columns for clarity (Map Ticker -> Logical Name)
        inv_map = {v: k for d in [self.physical_tickers, self.macro_tickers, self.crypto_tickers] for k, v in d.items()}
        data.rename(columns=inv_map, inplace=True)
        
        # Fill missing data (sensors sometimes blink)
        self.master_df = data.ffill().dropna()
        print(f"Data ingested. {self.master_df.shape[0]} timestamps aligned.")

    def normalize_signals(self):
        """Converts raw prices to Z-Scores to compare Apples to Oranges."""
        # We care about volatility-adjusted momentum, not absolute price
        # Z-Score = (Current Price - Mean) / StdDev
        self.z_scores = (self.master_df - self.master_df.rolling(window=30).mean()) / self.master_df.rolling(window=30).std()
        print("Signals Normalized. System can now compare Oil vs Bitcoin.")

    def run_correlation_matrix(self):
        """THE BRAIN: Detects how assets are moving together RIGHT NOW."""
        # We look at a rolling correlation window (e.g., last 30 days) to see current regime
        corr_matrix = self.master_df.pct_change().tail(30).corr()
        
        print("\n--- [BRAIN] Live Correlation Matrix (Last 30 Days) ---")
        # Focus on Bitcoin's correlation to the physical world
        btc_corrs = corr_matrix['Bitcoin'].sort_values(ascending=False)
        print(btc_corrs)
        
        return corr_matrix

    def detect_regime(self):
        """Decides the Macro Regime based on correlations."""
        # Get latest Z-scores
        latest = self.z_scores.iloc[-1]
        
        # Logic 1: Inflation Check (Commodities + Shipping up?)
        inflation_score = (latest['Oil_Inventory_Proxy'] + latest['Industrial_Metals'] + latest['Global_Shipping']) / 3
        
        # Logic 2: Liquidity Check (Yields Down + Tech Up?)
        liquidity_score = (latest['Tech_Growth'] - latest['10Y_Yield']) 
        
        print("\n--- [DECISION ENGINE] Regime Detection ---")
        print(f"Physical Inflation Pressure: {inflation_score:.2f} (Z-Score)")
        print(f"Global Liquidity Impulse:    {liquidity_score:.2f} (Z-Score)")
        
        if inflation_score > 1.0 and liquidity_score < -0.5:
            print(">>> DETECTED: STAGFLATION (Risk Off).")
            print(">>> ACTION: Short Tech, Long Energy, Hedge Crypto.")
            
        elif inflation_score < 0.5 and liquidity_score > 1.0:
            print(">>> DETECTED: GOLDILOCKS / LIQUIDITY PUMP.")
            print(">>> ACTION: Max Long Crypto, Long Tech.")
            
        elif latest['US_Dollar'] > 1.5:
            print(">>> DETECTED: DOLLAR WRECKING BALL.")
            print(">>> ACTION: Cash is King. Short Everything.")
            
        else:
            print(">>> DETECTED: CHOP / NO CLEAR SIGNAL.")

    def visualize_brain(self, corr_matrix):
        """Outputs the Heatmap for your visual inspection."""
        plt.figure(figsize=(12, 10))
        sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', fmt=".2f")
        plt.title("Global Macro Asset Correlations (30D Rolling)")
        plt.show()

# --- EXECUTION ---
if __name__ == "__main__":
    system = OmniSensorEngine()
    system.activate_sensors()
    system.normalize_signals()
    matrix = system.run_correlation_matrix()
    system.detect_regime()
    
    # Uncomment to see the heatmap
    # system.visualize_brain(matrix)
