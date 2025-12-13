import numpy as np
from scipy.stats import entropy, linregress

class KairosFieldEquations:
    """
    THE QUANT BIBLE v6.0: 6-DIMENSIONAL MARKET PHYSICS
    
    1. Gravity (G): Mean Reversion Force
    2. Velocity (V): Speed of Price
    3. Entropy (H): Chaos/Noise Level
    4. Pressure (P): Buying/Selling Force (Money Flow)
    5. Supply Z (Sz): Volume Anomaly (Supply Shock)
    6. Volatility Z (σz): Regime State (Compression vs Expansion)
    """
    def __init__(self, prices, volumes, window=20):
        # Ensure we have enough data, else pad or truncate logic handled in caller
        self.prices = np.array(prices, dtype=np.float64)
        self.volumes = np.array(volumes, dtype=np.float64)
        self.window = window
        self.epsilon = 1e-10

    def gravity(self):
        """Z-Score of Price vs VWAP. G > 2.0 = Overextended."""
        if len(self.prices) < self.window: return 0.0
        # Simple VWAP approx
        vwap = np.average(self.prices[-self.window:], weights=self.volumes[-self.window:])
        std = np.std(self.prices[-self.window:])
        return 0.0 if std == 0 else (self.prices[-1] - vwap) / std

    def velocity(self):
        """1st Derivative of Price (Momentum) in Basis Points."""
        if len(self.prices) < 5: return 0.0
        # Linear regression slope of last 5 points
        slope, _, _, _, _ = linregress(np.arange(5), self.prices[-5:])
        if self.prices[-1] == 0: return 0.0
        return (slope / self.prices[-1]) * 10000 

    def entropy(self):
        """Shannon Entropy. H -> 0 (Trend), H -> 1 (Chaos)."""
        if len(self.prices) < self.window: return 1.0
        # Log returns
        with np.errstate(divide='ignore', invalid='ignore'):
            log_ret = np.diff(np.log(self.prices))
        
        # Clean NaNs/Infs
        log_ret = np.nan_to_num(log_ret)
        if len(log_ret) == 0: return 1.0

        hist, _ = np.histogram(log_ret, bins=10, density=True)
        # Normalize by log(bins)
        return entropy(hist + self.epsilon) / np.log(10)

    def pressure(self):
        """Force Index Approximation. [-1.0 to 1.0]"""
        if len(self.prices) < 2: return 0.0
        delta = self.prices[-1] - self.prices[-2]
        force = delta * self.volumes[-1]
        
        # Normalize against recent avg volume * avg price change
        avg_force = np.mean(np.abs(np.diff(self.prices[-self.window:]) * self.volumes[-self.window:-1]))
        if avg_force == 0: return 0.0
        return max(-1.0, min(1.0, force / avg_force))

    def supply_z(self):
        """Volume Anomaly Z-Score."""
        if len(self.volumes) < self.window: return 0.0
        mean_vol = np.mean(self.volumes[:-1]) # Exclude current candle to see shock
        std_vol = np.std(self.volumes[:-1])
        if std_vol == 0: return 0.0
        return (self.volumes[-1] - mean_vol) / std_vol

    def kairos_score(self):
        """
        Aggregate Psi (Ψ) Score: 0-100.
        High Score = High Velocity + Low Entropy + Positive Pressure.
        """
        G = self.gravity()
        V = self.velocity()
        H = self.entropy()
        P = self.pressure()
        Sz = self.supply_z()
        
        # Base Score (50 neutral)
        psi = 50.0
        
        # 1. Velocity adds directly (capped)
        psi += max(-20, min(20, V / 5.0)) 
        
        # 2. Entropy Penalty (Chaos kills confidence)
        if H > 0.8: psi *= 0.8
        if H < 0.4: psi *= 1.2
        
        # 3. Pressure Confirmation
        if P > 0.5: psi += 10
        if P < -0.5: psi -= 10
        
        # 4. Gravity Dampener (Mean Reversion Risk)
        if abs(G) > 2.5: psi -= 15 # Too extended
        
        # 5. Supply Shock Bonus
        if Sz > 3.0: psi += 5 # Massive interest

        final_psi = max(0.0, min(100.0, psi))
        
        vectors = {
            "G": round(G, 2),
            "V": round(V, 2),
            "H": round(H, 2),
            "P": round(P, 2),
            "Sz": round(Sz, 2)
        }
        return final_psi, vectors
