"""
Statistical Risk Modelling Framework
=====================================
This module implements core statistical risk analysis models including:
- Distribution analysis (moments: mean, variance, skewness, kurtosis)
- Correlation matrix generation
- Principal Component Analysis (PCA)
- Value at Risk (VaR) models
"""

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import warnings
warnings.filterwarnings('ignore')


class VaRMethod(Enum):
    """Enumeration of VaR calculation methods."""
    HISTORICAL = "historical"
    PARAMETRIC = "parametric"
    MONTE_CARLO = "monte_carlo"
    CORNISH_FISHER = "cornish_fisher"


@dataclass
class StatisticalMoments:
    """Container for statistical moments of a distribution."""
    mean: float
    variance: float
    std_dev: float
    skewness: float
    kurtosis: float
    excess_kurtosis: float
    
    def to_dict(self) -> Dict:
        return {
            'mean': self.mean,
            'variance': self.variance,
            'std_dev': self.std_dev,
            'skewness': self.skewness,
            'kurtosis': self.kurtosis,
            'excess_kurtosis': self.excess_kurtosis
        }


@dataclass
class VaRResult:
    """Container for VaR calculation results."""
    var_95: float
    var_99: float
    var_999: float
    cvar_95: float  # Conditional VaR (Expected Shortfall)
    cvar_99: float
    method: str
    confidence_level: float
    time_horizon: int
    
    def to_dict(self) -> Dict:
        return {
            'var_95': self.var_95,
            'var_99': self.var_99,
            'var_99_9': self.var_999,
            'cvar_95': self.cvar_95,
            'cvar_99': self.cvar_99,
            'method': self.method,
            'confidence_level': self.confidence_level,
            'time_horizon': self.time_horizon
        }


@dataclass
class PCAResult:
    """Container for PCA analysis results."""
    explained_variance_ratio: np.ndarray
    cumulative_variance_ratio: np.ndarray
    components: np.ndarray
    feature_names: List[str]
    loadings: pd.DataFrame
    
    @property
    def n_components(self) -> int:
        return len(self.explained_variance_ratio)
    
    def to_dict(self) -> Dict:
        return {
            'explained_variance_ratio': self.explained_variance_ratio.tolist(),
            'cumulative_variance_ratio': self.cumulative_variance_ratio.tolist(),
            'n_components': self.n_components,
            'loadings': self.loadings.to_dict()
        }


class StatisticalRiskAnalyzer:
    """
    Core class for statistical risk analysis.
    
    Implements various risk models and statistical techniques for
    analyzing financial market data within regulatory frameworks.
    """
    
    def __init__(self, returns_data: pd.DataFrame):
        """
        Initialize the analyzer with returns data.
        
        Args:
            returns_data: DataFrame with asset returns (columns = assets, rows = observations)
        """
        self.returns = returns_data
        self.assets = returns_data.columns.tolist()
        self.n_observations = len(returns_data)
        
    def calculate_moments(self, asset: Optional[str] = None) -> StatisticalMoments:
        """
        Calculate statistical moments for an asset or portfolio.
        
        Mathematical Foundation:
        ------------------------
        For a random variable X with probability distribution f(x):
        
        Mean (First Moment): μ = E[X] = ∫x·f(x)dx
        
        Variance (Second Central Moment): σ² = E[(X-μ)²] = ∫(x-μ)²·f(x)dx
        
        Skewness (Standardized Third Moment): 
        γ₁ = E[(X-μ)³]/σ³ = μ₃/σ³
        
        Kurtosis (Standardized Fourth Moment):
        γ₂ = E[(X-μ)⁴]/σ⁴ = μ₄/σ⁴
        
        Excess Kurtosis = γ₂ - 3 (normal distribution has kurtosis = 3)
        
        Regulatory Significance:
        - Skewness indicates asymmetry in returns (tail risk)
        - High kurtosis indicates fat tails (extreme events more likely)
        - Basel/EMIR require monitoring of tail risk characteristics
        
        Args:
            asset: Asset name. If None, calculates for equal-weighted portfolio
            
        Returns:
            StatisticalMoments object containing all calculated moments
        """
        if asset is None:
            # Equal-weighted portfolio
            weights = np.ones(len(self.assets)) / len(self.assets)
            data = self.returns.dot(weights)
        else:
            data = self.returns[asset]
            
        # Remove NaN values
        clean_data = data.dropna()
        
        mean = np.mean(clean_data)
        variance = np.var(clean_data, ddof=1)
        std_dev = np.sqrt(variance)
        
        # Skewness: measure of asymmetry
        # Positive skew: right tail is longer/fatter
        # Negative skew: left tail is longer/fatter (dangerous for long positions)
        skewness = stats.skew(clean_data, bias=False)
        
        # Kurtosis: measure of tail heaviness
        # Normal distribution has kurtosis = 3
        kurt = stats.kurtosis(clean_data, fisher=False, bias=False)
        excess_kurt = kurt - 3
        
        return StatisticalMoments(
            mean=mean,
            variance=variance,
            std_dev=std_dev,
            skewness=skewness,
            kurtosis=kurt,
            excess_kurtosis=excess_kurt
        )
    
    def calculate_correlation_matrix(self) -> pd.DataFrame:
        """
        Generate correlation matrix for all assets.
        
        Mathematical Foundation:
        ------------------------
        Pearson correlation coefficient between assets X and Y:
        
        ρ(X,Y) = Cov(X,Y) / (σₓ·σᵧ)
        
        where Cov(X,Y) = E[(X-μₓ)(Y-μᵧ)]
        
        Properties:
        - Range: -1 ≤ ρ ≤ 1
        - ρ = 1: perfect positive linear relationship
        - ρ = -1: perfect negative linear relationship
        - ρ = 0: no linear relationship
        
        Regulatory Significance:
        - Correlation breakdown during crises (systemic risk)
        - Diversification benefits assessment
        - Portfolio concentration risk under EMIR/UCITS
        
        Returns:
            DataFrame containing correlation matrix
        """
        return self.returns.corr()
    
    def calculate_covariance_matrix(self) -> pd.DataFrame:
        """
        Generate covariance matrix for all assets.
        
        Mathematical Foundation:
        ------------------------
        Covariance matrix Σ for assets X₁, X₂, ..., Xₙ:
        
        Σᵢⱼ = Cov(Xᵢ, Xⱼ) = E[(Xᵢ-μᵢ)(Xⱼ-μⱼ)]
        
        Properties:
        - Symmetric: Σ = Σᵀ
        - Positive semi-definite: wᵀΣw ≥ 0 for all w
        - Diagonal elements are variances: Σᵢᵢ = σᵢ²
        
        Returns:
            DataFrame containing covariance matrix
        """
        return self.returns.cov()
    
    def perform_pca(self, n_components: Optional[int] = None) -> PCAResult:
        """
        Perform Principal Component Analysis on returns data.
        
        Mathematical Foundation:
        ------------------------
        PCA transforms correlated variables into uncorrelated principal components
        through eigen-decomposition of the covariance matrix:
        
        Σ = VΛVᵀ
        
        where:
        - Λ = diagonal matrix of eigenvalues (λ₁ ≥ λ₂ ≥ ... ≥ λₙ)
        - V = matrix of eigenvectors (columns)
        
        Principal components: Z = Vᵀ(X - μ)
        
        Explained variance ratio: λᵢ / Σλⱼ
        
        Cumulative variance: Σₖ₌₁ⁱ λₖ / Σλⱼ
        
        Factor Interpretation:
        - PC1: Often represents "market factor" (parallel shifts)
        - PC2: Often represents "steepness/curve factor"
        - PC3: Often represents "curvature/butterfly factor"
        
        Regulatory Significance:
        - Factor risk attribution under FRTB
        - Dimensionality reduction for stress testing
        - Identifying dominant risk drivers
        
        Args:
            n_components: Number of components to retain. If None, keeps all.
            
        Returns:
            PCAResult object containing analysis results
        """
        # Standardize data (zero mean, unit variance)
        scaler = StandardScaler()
        scaled_data = scaler.fit_transform(self.returns.dropna())
        
        # Perform PCA
        if n_components is None:
            n_components = min(len(self.assets), len(self.returns))
            
        pca = PCA(n_components=n_components)
        pca.fit(scaled_data)
        
        # Calculate cumulative variance
        cumvar = np.cumsum(pca.explained_variance_ratio_)
        
        # Create loadings DataFrame
        loadings = pd.DataFrame(
            pca.components_.T,
            columns=[f'PC{i+1}' for i in range(n_components)],
            index=self.assets
        )
        
        return PCAResult(
            explained_variance_ratio=pca.explained_variance_ratio_,
            cumulative_variance_ratio=cumvar,
            components=pca.components_,
            feature_names=self.assets,
            loadings=loadings
        )
    
    def calculate_var(self, 
                     confidence_level: float = 0.99,
                     time_horizon: int = 1,
                     method: VaRMethod = VaRMethod.HISTORICAL,
                     weights: Optional[np.ndarray] = None,
                     n_simulations: int = 10000) -> VaRResult:
        """
        Calculate Value at Risk using specified method.
        
        Mathematical Foundation:
        ------------------------
        Value at Risk at confidence level α over time horizon T:
        
        VaRα,T = inf{l ∈ ℝ: P(L > l) ≤ 1-α}
        
        where L is the portfolio loss random variable.
        
        Methods:
        
        1. Historical Simulation:
           VaR = quantile(historical_returns, 1-α)
           
           - Non-parametric, uses actual historical data
           - Makes no distributional assumptions
           - Limited by data availability
        
        2. Parametric (Variance-Covariance):
           VaR = μ - zₐ·σ
           
           where zₐ is the quantile of standard normal (e.g., 2.33 for 99%)
           
           - Assumes normal distribution of returns
           - Computationally efficient
           - May underestimate tail risk if distribution is fat-tailed
        
        3. Monte Carlo Simulation:
           - Generate random scenarios from assumed distribution
           - Calculate portfolio value for each scenario
           - VaR = appropriate percentile of simulated P&L
           
        4. Cornish-Fisher Expansion:
           Modified quantile accounting for skewness and kurtosis:
           
           z̃ₐ = zₐ + (zₐ² - 1)·S/6 + (zₐ³ - 3zₐ)·K/24 - (2zₐ³ - 5zₐ)·S²/36
           
           where S = skewness, K = excess kurtosis
           
        Conditional VaR (Expected Shortfall):
        CVaR = E[L | L > VaR]
        
        Regulatory Context:
        - Basel III: 99% VaR, 10-day horizon for market risk
        - FRTB: Expected Shortfall (CVaR) at 97.5% confidence
        - UCITS: 99% VaR, 1-month horizon for global exposure
        
        Args:
            confidence_level: Confidence level (e.g., 0.99 for 99%)
            time_horizon: Time horizon in days
            method: VaR calculation method
            weights: Portfolio weights (None for equal weights)
            n_simulations: Number of simulations for Monte Carlo
            
        Returns:
            VaRResult object containing all VaR metrics
        """
        if weights is None:
            weights = np.ones(len(self.assets)) / len(self.assets)
            
        # Calculate portfolio returns
        portfolio_returns = self.returns.dot(weights)
        clean_returns = portfolio_returns.dropna()
        
        # Scaling factor for time horizon (square root of time rule)
        time_scale = np.sqrt(time_horizon)
        
        if method == VaRMethod.HISTORICAL:
            var_95, var_99, var_999, cvar_95, cvar_99 = self._var_historical(
                clean_returns, time_scale
            )
            
        elif method == VaRMethod.PARAMETRIC:
            var_95, var_99, var_999, cvar_95, cvar_99 = self._var_parametric(
                clean_returns, time_scale
            )
            
        elif method == VaRMethod.MONTE_CARLO:
            var_95, var_99, var_999, cvar_95, cvar_99 = self._var_monte_carlo(
                clean_returns, weights, time_scale, n_simulations
            )
            
        elif method == VaRMethod.CORNISH_FISHER:
            var_95, var_99, var_999, cvar_95, cvar_99 = self._var_cornish_fisher(
                clean_returns, time_scale
            )
        else:
            raise ValueError(f"Unknown VaR method: {method}")
        
        return VaRResult(
            var_95=var_95,
            var_99=var_99,
            var_999=var_999,
            cvar_95=cvar_95,
            cvar_99=cvar_99,
            method=method.value,
            confidence_level=confidence_level,
            time_horizon=time_horizon
        )
    
    def _var_historical(self, returns: pd.Series, time_scale: float) -> Tuple[float, ...]:
        """Historical simulation VaR."""
        var_95 = np.percentile(returns, 5) * time_scale
        var_99 = np.percentile(returns, 1) * time_scale
        var_999 = np.percentile(returns, 0.1) * time_scale
        
        # Conditional VaR (Expected Shortfall)
        cvar_95 = returns[returns <= np.percentile(returns, 5)].mean() * time_scale
        cvar_99 = returns[returns <= np.percentile(returns, 1)].mean() * time_scale
        
        return var_95, var_99, var_999, cvar_95, cvar_99
    
    def _var_parametric(self, returns: pd.Series, time_scale: float) -> Tuple[float, ...]:
        """Parametric (Variance-Covariance) VaR assuming normal distribution."""
        mu = returns.mean()
        sigma = returns.std()
        
        # Z-scores for different confidence levels
        z_95 = stats.norm.ppf(0.05)
        z_99 = stats.norm.ppf(0.01)
        z_999 = stats.norm.ppf(0.001)
        
        var_95 = (mu + z_95 * sigma) * time_scale
        var_99 = (mu + z_99 * sigma) * time_scale
        var_999 = (mu + z_999 * sigma) * time_scale
        
        # CVaR for normal distribution: CVaR = μ - σ·φ(z)/Φ(z)
        cvar_95 = (mu - sigma * stats.norm.pdf(z_95) / 0.05) * time_scale
        cvar_99 = (mu - sigma * stats.norm.pdf(z_99) / 0.01) * time_scale
        
        return var_95, var_99, var_999, cvar_95, cvar_99
    
    def _var_monte_carlo(self, returns: pd.Series, weights: np.ndarray,
                        time_scale: float, n_simulations: int) -> Tuple[float, ...]:
        """Monte Carlo simulation VaR."""
        mu = returns.mean()
        sigma = returns.std()
        
        # Generate random returns
        simulated_returns = np.random.normal(mu, sigma, n_simulations)
        
        var_95 = np.percentile(simulated_returns, 5) * time_scale
        var_99 = np.percentile(simulated_returns, 1) * time_scale
        var_999 = np.percentile(simulated_returns, 0.1) * time_scale
        
        cvar_95 = simulated_returns[simulated_returns <= var_95].mean() * time_scale
        cvar_99 = simulated_returns[simulated_returns <= var_99].mean() * time_scale
        
        return var_95, var_99, var_999, cvar_95, cvar_99
    
    def _var_cornish_fisher(self, returns: pd.Series, time_scale: float) -> Tuple[float, ...]:
        """Cornish-Fisher expansion VaR (accounts for skewness and kurtosis)."""
        mu = returns.mean()
        sigma = returns.std()
        skew = stats.skew(returns)
        kurt = stats.kurtosis(returns)  # excess kurtosis
        
        def cornish_fisher_z(alpha: float) -> float:
            z = stats.norm.ppf(alpha)
            # Cornish-Fisher expansion
            z_cf = z + (z**2 - 1) * skew / 6 + (z**3 - 3*z) * kurt / 24 - (2*z**3 - 5*z) * skew**2 / 36
            return z_cf
        
        var_95 = (mu + cornish_fisher_z(0.05) * sigma) * time_scale
        var_99 = (mu + cornish_fisher_z(0.01) * sigma) * time_scale
        var_999 = (mu + cornish_fisher_z(0.001) * sigma) * time_scale
        
        # Approximate CVaR using historical method on CF-adjusted distribution
        z_scores = [cornish_fisher_z(p/100) for p in range(1, 6)]
        cvar_95 = (mu + np.mean(z_scores) * sigma) * time_scale
        
        z_scores = [cornish_fisher_z(p/1000) for p in range(1, 11)]
        cvar_99 = (mu + np.mean(z_scores) * sigma) * time_scale
        
        return var_95, var_99, var_999, cvar_95, cvar_99
    
    def factor_analysis(self, factor_returns: pd.DataFrame) -> Dict:
        """
        Perform factor exposure analysis.
        
        Mathematical Foundation:
        ------------------------
        Multi-factor model:
        
        Rᵢ = αᵢ + Σⱼ βᵢⱼFⱼ + εᵢ
        
        where:
        - Rᵢ = return of asset i
        - Fⱼ = return of factor j
        - βᵢⱼ = sensitivity (exposure) of asset i to factor j
        - εᵢ = idiosyncratic return
        
        Using Ordinary Least Squares (OLS):
        β = (XᵀX)⁻¹Xᵀy
        
        R² = 1 - SSR/SST (proportion of variance explained by factors)
        
        Regulatory Significance:
        - Factor risk decomposition under FRTB
        - Attribution of P&L to risk factors
        - Model risk assessment
        
        Args:
            factor_returns: DataFrame of factor returns
            
        Returns:
            Dictionary containing factor exposures and statistics
        """
        results = {}
        
        for asset in self.assets:
            y = self.returns[asset]
            X = factor_returns.loc[y.index]
            
            # Add constant for intercept
            X_with_const = np.column_stack([np.ones(len(X)), X])
            
            # OLS regression
            try:
                beta = np.linalg.lstsq(X_with_const, y, rcond=None)[0]
                residuals = y - X_with_const @ beta
                
                # Calculate R-squared
                ss_res = np.sum(residuals**2)
                ss_tot = np.sum((y - y.mean())**2)
                r_squared = 1 - (ss_res / ss_tot)
                
                results[asset] = {
                    'alpha': beta[0],
                    'betas': dict(zip(factor_returns.columns, beta[1:])),
                    'r_squared': r_squared,
                    'residual_std': np.std(residuals)
                }
            except:
                results[asset] = {'error': 'Regression failed'}
                
        return results
    
    def clustering_analysis(self, n_clusters: int = 3) -> Dict:
        """
        Perform cluster analysis on assets based on return patterns.
        
        Uses K-means clustering on standardized returns.
        
        Regulatory Significance:
        - Portfolio diversification analysis
        - Identifying similar risk profiles
        - Concentration risk assessment
        
        Args:
            n_clusters: Number of clusters to form
            
        Returns:
            Dictionary containing cluster assignments
        """
        from sklearn.cluster import KMeans
        
        # Calculate correlation distance matrix
        corr_matrix = self.returns.corr()
        distance_matrix = np.sqrt(0.5 * (1 - corr_matrix))
        
        # Perform clustering
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        clusters = kmeans.fit_predict(distance_matrix)
        
        # Group assets by cluster
        cluster_groups = {}
        for i, asset in enumerate(self.assets):
            cluster_id = int(clusters[i])
            if cluster_id not in cluster_groups:
                cluster_groups[cluster_id] = []
            cluster_groups[cluster_id].append(asset)
        
        return {
            'n_clusters': n_clusters,
            'clusters': cluster_groups,
            'cluster_assignments': dict(zip(self.assets, clusters.tolist()))
        }
    
    def generate_risk_report(self) -> Dict:
        """
        Generate comprehensive risk analysis report.
        
        Returns:
            Dictionary containing all risk metrics
        """
        report = {
            'statistical_moments': {},
            'correlation_matrix': self.calculate_correlation_matrix().to_dict(),
            'covariance_matrix': self.calculate_covariance_matrix().to_dict(),
            'var_analysis': {},
            'pca_analysis': self.perform_pca().to_dict(),
            'cluster_analysis': self.clustering_analysis()
        }
        
        # Calculate moments for each asset
        for asset in self.assets:
            report['statistical_moments'][asset] = self.calculate_moments(asset).to_dict()
        
        # Calculate portfolio moments
        report['statistical_moments']['portfolio'] = self.calculate_moments(None).to_dict()
        
        # Calculate VaR using different methods
        for method in VaRMethod:
            try:
                var_result = self.calculate_var(method=method)
                report['var_analysis'][method.value] = var_result.to_dict()
            except Exception as e:
                report['var_analysis'][method.value] = {'error': str(e)}
        
        return report
