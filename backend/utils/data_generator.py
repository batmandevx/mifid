"""
Dummy Financial Data Generator
==============================
Generates synthetic financial market data for testing and demonstration.
"""

import numpy as np
import pandas as pd
from typing import List, Tuple, Optional
from datetime import datetime, timedelta


class FinancialDataGenerator:
    """
    Generates realistic dummy financial data for risk analysis testing.
    
    Models used:
    - Geometric Brownian Motion for price simulation
    - GARCH-like volatility clustering
    - Correlated returns using Cholesky decomposition
    """
    
    # Asset class definitions with typical risk characteristics
    ASSET_CLASSES = {
        'equities': {
            'assets': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'JPM', 'BAC', 'XOM', 'JNJ', 'WMT'],
            'mean_return': 0.0008,  # Daily mean return (~20% annualized)
            'volatility': 0.02,     # Daily volatility (~32% annualized)
            'skewness': -0.5,       # Negative skew (left tail)
            'kurtosis': 4.0         # Fat tails
        },
        'bonds': {
            'assets': ['TLT', 'IEF', 'SHY', 'LQD', 'HYG', 'EMB'],
            'mean_return': 0.0002,  # Lower returns
            'volatility': 0.005,    # Lower volatility
            'skewness': 0.1,
            'kurtosis': 3.5
        },
        'commodities': {
            'assets': ['GLD', 'SLV', 'USO', 'DBA', 'UNG'],
            'mean_return': 0.0003,
            'volatility': 0.025,
            'skewness': 0.3,
            'kurtosis': 4.5
        },
        'fx': {
            'assets': ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD'],
            'mean_return': 0.0,
            'volatility': 0.006,
            'skewness': 0.0,
            'kurtosis': 3.8
        }
    }
    
    # Cross-asset correlations (simplified)
    CROSS_ASSET_CORR = {
        ('equities', 'bonds'): -0.2,
        ('equities', 'commodities'): 0.15,
        ('equities', 'fx'): 0.05,
        ('bonds', 'commodities'): 0.1,
        ('bonds', 'fx'): -0.05,
        ('commodities', 'fx'): 0.2
    }
    
    def __init__(self, seed: Optional[int] = 42):
        """
        Initialize generator.
        
        Args:
            seed: Random seed for reproducibility
        """
        self.seed = seed
        if seed:
            np.random.seed(seed)
    
    def generate_returns(self,
                        n_observations: int = 252*3,  # 3 years of daily data
                        asset_classes: List[str] = None,
                        start_date: Optional[str] = None,
                        include_stress_periods: bool = True) -> pd.DataFrame:
        """
        Generate correlated returns data for multiple asset classes.
        
        Mathematical Model:
        -------------------
        1. Generate uncorrelated returns using modified normal distribution
           with specified skewness and kurtosis (Johnson SU transformation)
        
        2. Apply Cholesky decomposition to introduce correlations:
           
           If Σ = LLᵀ (Cholesky decomposition)
           And Z ~ N(0, I) (independent standard normals)
           Then X = LZ ~ N(0, Σ) (correlated multivariate normal)
        
        3. Add volatility clustering (GARCH-like):
           σₜ² = ω + α·rₜ₋₁² + β·σₜ₋₁²
        
        4. Optionally inject stress periods (crisis simulation)
        
        Args:
            n_observations: Number of daily observations
            asset_classes: List of asset classes to include
            start_date: Start date for time series
            include_stress_periods: Whether to simulate crisis periods
            
        Returns:
            DataFrame with asset returns
        """
        if asset_classes is None:
            asset_classes = list(self.ASSET_CLASSES.keys())
        
        # Collect all assets
        all_assets = []
        asset_class_map = {}
        for ac in asset_classes:
            assets = self.ASSET_CLASSES[ac]['assets']
            all_assets.extend(assets)
            for asset in assets:
                asset_class_map[asset] = ac
        
        n_assets = len(all_assets)
        
        # Build correlation matrix
        corr_matrix = self._build_correlation_matrix(asset_class_map)
        
        # Generate uncorrelated returns with desired moments
        uncorrelated_returns = np.zeros((n_observations, n_assets))
        for i, asset in enumerate(all_assets):
            ac = asset_class_map[asset]
            params = self.ASSET_CLASSES[ac]
            uncorrelated_returns[:, i] = self._generate_skewed_returns(
                n_observations,
                mean=params['mean_return'],
                std=params['volatility'],
                skew=params['skewness'],
                kurt=params['kurtosis']
            )
        
        # Apply Cholesky decomposition for correlations
        L = np.linalg.cholesky(corr_matrix)
        correlated_returns = uncorrelated_returns @ L.T
        
        # Add volatility clustering
        returns_with_clustering = self._add_garch_effect(correlated_returns)
        
        # Inject stress periods if requested
        if include_stress_periods:
            returns_with_clustering = self._inject_stress_periods(
                returns_with_clustering, asset_class_map
            )
        
        # Create date index
        if start_date is None:
            start_date = datetime.now() - timedelta(days=n_observations)
        else:
            start_date = pd.to_datetime(start_date)
        
        dates = pd.date_range(start=start_date, periods=n_observations, freq='B')
        
        df = pd.DataFrame(returns_with_clustering, columns=all_assets, index=dates)
        
        return df
    
    def _generate_skewed_returns(self, n: int, mean: float, std: float, 
                                  skew: float, kurt: float) -> np.ndarray:
        """
        Generate returns with specified skewness and kurtosis.
        
        Uses the Cornish-Fisher transformation approximation:
        X = μ + σ · [z + (z²-1)·S/6 + (z³-3z)·K/24]
        
        where z ~ N(0,1), S = skewness, K = excess kurtosis
        """
        z = np.random.standard_normal(n)
        
        # Cornish-Fisher expansion for skewness and kurtosis
        x = z + (z**2 - 1) * skew / 6 + (z**3 - 3*z) * (kurt - 3) / 24
        
        # Scale to target mean and std
        returns = mean + std * x
        
        return returns
    
    def _build_correlation_matrix(self, asset_class_map: dict) -> np.ndarray:
        """
        Build correlation matrix based on asset classes.
        
        Within asset class: high correlation (~0.6-0.8)
        Across asset classes: defined by CROSS_ASSET_CORR
        """
        assets = list(asset_class_map.keys())
        n = len(assets)
        corr = np.eye(n)
        
        for i in range(n):
            for j in range(i+1, n):
                ac_i = asset_class_map[assets[i]]
                ac_j = asset_class_map[assets[j]]
                
                if ac_i == ac_j:
                    # Same asset class: high correlation
                    corr[i, j] = corr[j, i] = np.random.uniform(0.5, 0.85)
                else:
                    # Different asset classes
                    key = tuple(sorted([ac_i, ac_j]))
                    base_corr = self.CROSS_ASSET_CORR.get(key, 0.0)
                    # Add some noise
                    corr[i, j] = corr[j, i] = base_corr + np.random.uniform(-0.1, 0.1)
        
        # Ensure positive semi-definite
        eigenvalues = np.linalg.eigvalsh(corr)
        if np.min(eigenvalues) < 0:
            corr = corr + np.eye(n) * (abs(np.min(eigenvalues)) + 0.01)
            # Renormalize
            d = np.diag(corr)
            corr = corr / np.sqrt(np.outer(d, d))
        
        return corr
    
    def _add_garch_effect(self, returns: np.ndarray, 
                          omega: float = 0.000001,
                          alpha: float = 0.1,
                          beta: float = 0.85) -> np.ndarray:
        """
        Add GARCH(1,1) volatility clustering effect.
        
        GARCH(1,1) Model:
        σₜ² = ω + α·rₜ₋₁² + β·σₜ₋₁²
        
        where:
        - ω = long-term average variance
        - α = reaction to recent shocks
        - β = persistence of volatility
        """
        n, m = returns.shape
        modified_returns = np.zeros_like(returns)
        
        for j in range(m):
            variance = np.var(returns[:, j])
            modified_returns[0, j] = returns[0, j]
            
            for t in range(1, n):
                variance = omega + alpha * returns[t-1, j]**2 + beta * variance
                modified_returns[t, j] = returns[t, j] * np.sqrt(variance / np.var(returns[:, j]))
        
        return modified_returns
    
    def _inject_stress_periods(self, returns: np.ndarray, 
                               asset_class_map: dict) -> np.ndarray:
        """
        Inject realistic stress periods into the data.
        
        Simulates:
        1. Market crash (2008-style): equities down 30-50%, flight to bonds
        2. Flash crash: sharp sudden drop and recovery
        3. Volatility spike: VIX-style volatility surge
        """
        n, m = returns.shape
        modified_returns = returns.copy()
        
        assets = list(asset_class_map.keys())
        
        # Crisis 1: Market crash (period around 20-25% of data)
        crisis_start = int(n * 0.20)
        crisis_end = int(n * 0.25)
        
        for i, asset in enumerate(assets):
            ac = asset_class_map[asset]
            if ac == 'equities':
                # Sharp decline
                for t in range(crisis_start, crisis_end):
                    modified_returns[t, i] = np.random.normal(-0.03, 0.05)
            elif ac == 'bonds':
                # Flight to safety
                for t in range(crisis_start, crisis_end):
                    modified_returns[t, i] = np.random.normal(0.002, 0.008)
        
        # Crisis 2: Flash crash (period around 60% of data)
        flash_start = int(n * 0.60)
        flash_end = int(n * 0.605)
        
        for i, asset in enumerate(assets):
            ac = asset_class_map[asset]
            if ac == 'equities':
                modified_returns[flash_start:flash_end, i] = np.random.normal(-0.05, 0.02, flash_end-flash_start)
        
        # Crisis 3: Volatility spike (period around 80% of data)
        vol_start = int(n * 0.80)
        vol_end = int(n * 0.85)
        
        for i in range(m):
            modified_returns[vol_start:vol_end, i] *= 2.5  # Increase volatility
        
        return modified_returns
    
    def generate_market_data(self, returns_df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate price series from returns.
        
        Pₜ = Pₜ₋₁ × (1 + Rₜ)
        """
        prices = (1 + returns_df).cumprod()
        # Normalize to start at 100
        prices = prices / prices.iloc[0] * 100
        return prices
    
    def save_to_csv(self, returns_df: pd.DataFrame, prices_df: pd.DataFrame,
                   filepath_returns: str, filepath_prices: str):
        """Save generated data to CSV files."""
        returns_df.to_csv(filepath_returns)
        prices_df.to_csv(filepath_prices)
        print(f"Data saved to {filepath_returns} and {filepath_prices}")


def create_sample_dataset(output_dir: str = "./data") -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Create a comprehensive sample dataset for demonstration.
    
    Returns:
        Tuple of (returns_df, prices_df)
    """
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    generator = FinancialDataGenerator(seed=42)
    
    # Generate 5 years of daily data
    returns = generator.generate_returns(
        n_observations=252 * 5,
        asset_classes=['equities', 'bonds', 'commodities', 'fx'],
        start_date='2019-01-01',
        include_stress_periods=True
    )
    
    prices = generator.generate_market_data(returns)
    
    # Save to CSV
    generator.save_to_csv(
        returns, prices,
        f"{output_dir}/sample_returns.csv",
        f"{output_dir}/sample_prices.csv"
    )
    
    return returns, prices


if __name__ == "__main__":
    returns, prices = create_sample_dataset()
    print(f"\nGenerated dataset:")
    print(f"Returns shape: {returns.shape}")
    print(f"Date range: {returns.index[0]} to {returns.index[-1]}")
    print(f"\nSample statistics:")
    print(returns.describe())
