"""
Advanced Risk Models
====================
Enhanced risk modeling including GARCH, Expected Shortfall, Backtesting,
Stress Testing, and Portfolio Optimization.
"""

import numpy as np
import pandas as pd
from scipy import stats
from scipy.optimize import minimize
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from typing import Dict, List, Tuple, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Try to import arch for GARCH
# Try to import arch for GARCH
try:
    from arch import arch_model
    HAS_ARCH = True
except ImportError:
    HAS_ARCH = False


class BacktestResult(Enum):
    """Backtest result zones per Basel III."""
    GREEN = "green"      # 0-4 exceptions
    YELLOW = "yellow"    # 5-9 exceptions
    RED = "red"          # 10+ exceptions


@dataclass
class GARCHResult:
    """GARCH model results."""
    omega: float
    alpha: float
    beta: float
    persistence: float
    half_life: float
    annualized_volatility: float
    forecasted_volatility: np.ndarray
    conditional_volatility: np.ndarray
    standardized_residuals: np.ndarray
    aic: float
    bic: float
    
    def to_dict(self) -> Dict:
        return {
            'omega': self.omega,
            'alpha': self.alpha,
            'beta': self.beta,
            'persistence': self.persistence,
            'half_life': self.half_life,
            'annualized_volatility': self.annualized_volatility,
            'aic': self.aic,
            'bic': self.bic,
            'forecast_horizon': len(self.forecasted_volatility)
        }


@dataclass
class ExpectedShortfallResult:
    """Expected Shortfall (CVaR) detailed results."""
    es_95: float
    es_99: float
    es_999: float
    method: str
    confidence_level: float
    time_horizon: int
    tail_losses: np.ndarray = field(default_factory=lambda: np.array([]))
    
    def to_dict(self) -> Dict:
        return {
            'es_95': self.es_95,
            'es_99': self.es_99,
            'es_999': self.es_999,
            'method': self.method,
            'confidence_level': self.confidence_level,
            'time_horizon': self.time_horizon
        }


@dataclass
class BacktestMetrics:
    """VaR backtesting metrics."""
    n_observations: int
    n_exceptions: int
    exception_rate: float
    expected_exceptions: float
    zone: str
    traffic_light: str
    kupiec_statistic: float
    kupiec_pvalue: float
    christoffersen_statistic: float
    christoffersen_pvalue: float
    basel_multiplier: float
    
    def to_dict(self) -> Dict:
        return {
            'n_observations': self.n_observations,
            'n_exceptions': self.n_exceptions,
            'exception_rate': self.exception_rate,
            'expected_exceptions': self.expected_exceptions,
            'zone': self.zone,
            'traffic_light': self.traffic_light,
            'kupiec_pvalue': self.kupiec_pvalue,
            'christoffersen_pvalue': self.christoffersen_pvalue,
            'basel_multiplier': self.basel_multiplier
        }


@dataclass
class StressTestResult:
    """Stress test scenario result."""
    scenario_name: str
    scenario_type: str
    shock_magnitude: float
    portfolio_return: float
    var_breach: bool
    expected_shortfall: float
    max_drawdown: float
    recovery_days: int


@dataclass
class PortfolioMetrics:
    """Comprehensive portfolio metrics."""
    total_return: float
    annualized_return: float
    volatility: float
    annualized_volatility: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    calmar_ratio: float
    var_95: float
    var_99: float
    cvar_95: float
    cvar_99: float
    beta: Optional[float] = None
    alpha: Optional[float] = None
    information_ratio: Optional[float] = None
    treynor_ratio: Optional[float] = None
    
    def to_dict(self) -> Dict:
        return {
            'total_return': self.total_return,
            'annualized_return': self.annualized_return,
            'volatility': self.volatility,
            'sharpe_ratio': self.sharpe_ratio,
            'sortino_ratio': self.sortino_ratio,
            'max_drawdown': self.max_drawdown,
            'calmar_ratio': self.calmar_ratio,
            'var_95': self.var_95,
            'var_99': self.var_99,
            'cvar_95': self.cvar_95,
            'cvar_99': self.cvar_99
        }


class AdvancedRiskAnalyzer:
    """
    Advanced risk analysis with GARCH, ES, backtesting, and stress testing.
    """
    
    def __init__(self, returns_data: pd.DataFrame, market_data: Optional[pd.DataFrame] = None):
        """
        Initialize analyzer.
        
        Args:
            returns_data: DataFrame with asset returns
            market_data: Optional market benchmark (e.g., S&P 500)
        """
        self.returns = returns_data
        self.assets = returns_data.columns.tolist()
        self.n_observations = len(returns_data)
        self.market_data = market_data
        
    def fit_garch(self, asset: Optional[str] = None, 
                  p: int = 1, q: int = 1,
                  forecast_horizon: int = 10) -> Optional[GARCHResult]:
        """
        Fit GARCH(p,q) model for volatility forecasting.
        
        Mathematical Model:
        -------------------
        GARCH(1,1) model:
        
        Returns: r_t = σ_t · z_t,  z_t ~ N(0,1)
        
        Variance equation:
        σ_t² = ω + α·r_{t-1}² + β·σ_{t-1}²
        
        where:
        - ω = long-term average variance (omega)
        - α = reaction to shocks (alpha)
        - β = persistence (beta)
        - Persistence = α + β (should be < 1 for stationarity)
        - Half-life = ln(0.5) / ln(α + β)
        
        Args:
            asset: Asset name (None for portfolio)
            p: GARCH order
            q: ARCH order
            forecast_horizon: Days to forecast
            
        Returns:
            GARCHResult with model parameters and forecasts
        """
        if not HAS_ARCH:
            print("Warning: arch package not installed. Install with: pip install arch")
            return None
        
        # Get return series
        if asset is None:
            weights = np.ones(len(self.assets)) / len(self.assets)
            returns = self.returns.dot(weights).dropna() * 100  # Convert to %
        else:
            returns = self.returns[asset].dropna() * 100
        
        try:
            # Fit GARCH(1,1)
            model = arch_model(returns, vol='Garch', p=p, q=q, dist='normal')
            result = model.fit(disp='off')
            
            # Extract parameters
            omega = result.params.get('omega', 0)
            alpha = result.params.get('alpha[1]', 0)
            beta = result.params.get('beta[1]', 0)
            persistence = alpha + beta
            
            # Calculate half-life
            if persistence < 1:
                half_life = np.log(0.5) / np.log(persistence)
            else:
                half_life = np.inf
            
            # Forecast
            forecast = result.forecast(horizon=forecast_horizon)
            forecasted_var = forecast.variance.values[-1]
            forecasted_vol = np.sqrt(forecasted_var) / 100  # Convert back
            
            # Annualized volatility
            annualized_vol = result.conditional_volatility.mean() * np.sqrt(252) / 100
            
            return GARCHResult(
                omega=omega,
                alpha=alpha,
                beta=beta,
                persistence=persistence,
                half_life=half_life,
                annualized_volatility=annualized_vol,
                forecasted_volatility=forecasted_vol,
                conditional_volatility=result.conditional_volatility.values / 100,
                standardized_residuals=result.resid / result.conditional_volatility,
                aic=result.aic,
                bic=result.bic
            )
            
        except Exception as e:
            print(f"GARCH fitting failed: {e}")
            return None
    
    def calculate_expected_shortfall(self, confidence_level: float = 0.975,
                                     time_horizon: int = 10,
                                     method: str = "historical",
                                     weights: Optional[np.ndarray] = None) -> ExpectedShortfallResult:
        """
        Calculate Expected Shortfall (CVaR) - FRTB standard.
        
        Mathematical Definition:
        ------------------------
        ES_α = E[L | L > VaR_α] = 1/(1-α) ∫_α^1 VaR_u du
        
        For historical simulation:
        ES_α = average of losses exceeding VaR_α
        
        For parametric (normal):
        ES_α = μ - σ · φ(z_α)/(1-α)
        
        where φ is standard normal PDF.
        
        Regulatory Context:
        - FRTB: 97.5% ES, 10-day horizon replaces VaR
        - More sensitive to tail shape than VaR
        - Sub-additive (coherent risk measure)
        
        Args:
            confidence_level: ES confidence (FRTB uses 0.975)
            time_horizon: Horizon in days
            method: Calculation method
            weights: Portfolio weights
            
        Returns:
            ExpectedShortfallResult
        """
        if weights is None:
            weights = np.ones(len(self.assets)) / len(self.assets)
        
        portfolio_returns = self.returns.dot(weights).dropna()
        time_scale = np.sqrt(time_horizon)
        
        if method == "historical":
            # Historical ES
            var_95 = np.percentile(portfolio_returns, 5)
            var_99 = np.percentile(portfolio_returns, 1)
            var_999 = np.percentile(portfolio_returns, 0.1)
            
            tail_95 = portfolio_returns[portfolio_returns <= var_95]
            tail_99 = portfolio_returns[portfolio_returns <= var_99]
            tail_999 = portfolio_returns[portfolio_returns <= var_999]
            
            es_95 = tail_95.mean() * time_scale if len(tail_95) > 0 else var_95 * time_scale
            es_99 = tail_99.mean() * time_scale if len(tail_99) > 0 else var_99 * time_scale
            es_999 = tail_999.mean() * time_scale if len(tail_999) > 0 else var_999 * time_scale
            
        elif method == "parametric":
            # Parametric ES for normal distribution
            mu = portfolio_returns.mean()
            sigma = portfolio_returns.std()
            
            # ES formula for normal: ES = μ - σ * φ(z_α)/(1-α)
            z_95 = stats.norm.ppf(0.05)
            z_99 = stats.norm.ppf(0.01)
            z_999 = stats.norm.ppf(0.001)
            
            es_95 = (mu - sigma * stats.norm.pdf(z_95) / 0.05) * time_scale
            es_99 = (mu - sigma * stats.norm.pdf(z_99) / 0.01) * time_scale
            es_999 = (mu - sigma * stats.norm.pdf(z_999) / 0.001) * time_scale
            
        else:
            raise ValueError(f"Unknown ES method: {method}")
        
        return ExpectedShortfallResult(
            es_95=es_95,
            es_99=es_99,
            es_999=es_999,
            method=method,
            confidence_level=confidence_level,
            time_horizon=time_horizon,
            tail_losses=portfolio_returns[portfolio_returns <= np.percentile(portfolio_returns, (1-confidence_level)*100)]
        )
    
    def backtest_var(self, var_predictions: np.ndarray, 
                     actual_returns: np.ndarray,
                     confidence_level: float = 0.99) -> BacktestMetrics:
        """
        Backtest VaR model using Kupiec and Christoffersen tests.
        
        Mathematical Tests:
        ------------------
        Kupiec Test (Unconditional Coverage):
        Tests if exception frequency matches confidence level.
        
        LR_uc = -2·ln[(1-p)^(T-N) · p^N / (1-N/T)^(T-N) · (N/T)^N] ~ χ²(1)
        
        where p = 1-confidence_level, T = observations, N = exceptions
        
        Christoffersen Test (Conditional Coverage):
        Tests if exceptions are independently distributed.
        
        Basel III Traffic Light Zones:
        - Green: 0-4 exceptions (multiplier = 3.0)
        - Yellow: 5-9 exceptions (multiplier = 3.0-4.0)
        - Red: 10+ exceptions (multiplier = 4.0)
        
        Args:
            var_predictions: Array of VaR predictions
            actual_returns: Array of actual returns
            confidence_level: VaR confidence level
            
        Returns:
            BacktestMetrics
        """
        n = len(actual_returns)
        exceptions = actual_returns < var_predictions
        n_exceptions = exceptions.sum()
        exception_rate = n_exceptions / n
        
        p = 1 - confidence_level
        expected_exceptions = p * n
        
        # Kupiec test
        if n_exceptions == 0:
            kupiec_lr = -2 * n * np.log(1 - p)
        elif n_exceptions == n:
            kupiec_lr = -2 * n * np.log(p)
        else:
            kupiec_lr = -2 * (
                n_exceptions * np.log(p / (n_exceptions / n)) +
                (n - n_exceptions) * np.log((1 - p) / (1 - n_exceptions / n))
            )
        
        kupiec_pvalue = 1 - stats.chi2.cdf(kupiec_lr, 1)
        
        # Christoffersen test (simplified - independence only)
        n00 = sum(1 for i in range(1, n) if not exceptions[i-1] and not exceptions[i])
        n01 = sum(1 for i in range(1, n) if not exceptions[i-1] and exceptions[i])
        n10 = sum(1 for i in range(1, n) if exceptions[i-1] and not exceptions[i])
        n11 = sum(1 for i in range(1, n) if exceptions[i-1] and exceptions[i])
        
        if n00 + n01 > 0 and n10 + n11 > 0:
            pi0 = n01 / (n00 + n01) if (n00 + n01) > 0 else 0
            pi1 = n11 / (n10 + n11) if (n10 + n11) > 0 else 0
            pi = (n01 + n11) / (n00 + n01 + n10 + n11)
            
            if pi0 > 0 and pi1 > 0 and pi > 0:
                christoffersen_lr = -2 * (
                    (n00 + n10) * np.log(1 - pi) + (n01 + n11) * np.log(pi) -
                    n00 * np.log(1 - pi0) - n01 * np.log(pi0) -
                    n10 * np.log(1 - pi1) - n11 * np.log(pi1)
                )
                christoffersen_pvalue = 1 - stats.chi2.cdf(christoffersen_lr, 1)
            else:
                christoffersen_lr = 0
                christoffersen_pvalue = 1.0
        else:
            christoffersen_lr = 0
            christoffersen_pvalue = 1.0
        
        # Basel zone
        if n_exceptions <= 4:
            zone = "green"
            traffic_light = "🟢"
            basel_mult = 3.0
        elif n_exceptions <= 9:
            zone = "yellow"
            traffic_light = "🟡"
            basel_mult = 3.0 + (n_exceptions - 4) * 0.2
        else:
            zone = "red"
            traffic_light = "🔴"
            basel_mult = 4.0
        
        return BacktestMetrics(
            n_observations=n,
            n_exceptions=int(n_exceptions),
            exception_rate=exception_rate,
            expected_exceptions=expected_exceptions,
            zone=zone,
            traffic_light=traffic_light,
            kupiec_statistic=kupiec_lr,
            kupiec_pvalue=kupiec_pvalue,
            christoffersen_statistic=christoffersen_lr,
            christoffersen_pvalue=christoffersen_pvalue,
            basel_multiplier=basel_mult
        )
    
    def stress_test(self, scenarios: List[Dict]) -> List[StressTestResult]:
        """
        Run stress tests on predefined scenarios.
        
        Scenarios:
        - Market crash: -30% equity drop
        - Interest rate shock: +200bp
        - Credit spread widening: +100bp
        - Liquidity crisis: Correlation → 1
        """
        results = []
        
        weights = np.ones(len(self.assets)) / len(self.assets)
        portfolio_returns = self.returns.dot(weights)
        
        for scenario in scenarios:
            name = scenario.get('name', 'Unknown')
            shock = scenario.get('shock', 0)
            
            # Apply shock to returns
            shocked_returns = portfolio_returns * (1 + shock)
            
            # Calculate metrics under stress
            portfolio_return = shocked_returns.sum()
            var_99 = np.percentile(shocked_returns, 1)
            max_dd = self._calculate_max_drawdown(shocked_returns)
            
            result = StressTestResult(
                scenario_name=name,
                scenario_type=scenario.get('type', 'custom'),
                shock_magnitude=shock,
                portfolio_return=portfolio_return,
                var_breach=portfolio_return < var_99,
                expected_shortfall=shocked_returns[shocked_returns <= var_99].mean(),
                max_drawdown=max_dd,
                recovery_days=self._estimate_recovery(shocked_returns, max_dd)
            )
            results.append(result)
        
        return results
    
    def calculate_portfolio_metrics(self, weights: Optional[np.ndarray] = None,
                                   risk_free_rate: float = 0.02) -> PortfolioMetrics:
        """
        Calculate comprehensive portfolio performance metrics.
        
        Metrics:
        - Sharpe Ratio: (Rp - Rf) / σp
        - Sortino Ratio: (Rp - Rf) / σd (downside deviation)
        - Max Drawdown: Maximum peak-to-trough decline
        - Calmar Ratio: Return / Max Drawdown
        - Beta: Cov(Rp, Rm) / Var(Rm)
        - Alpha: Rp - [Rf + β(Rm - Rf)]
        """
        if weights is None:
            weights = np.ones(len(self.assets)) / len(self.assets)
        
        portfolio_returns = self.returns.dot(weights)
        
        # Basic metrics
        total_return = (1 + portfolio_returns).prod() - 1
        n_years = len(portfolio_returns) / 252
        annualized_return = (1 + total_return) ** (1/n_years) - 1
        volatility = portfolio_returns.std()
        annualized_vol = volatility * np.sqrt(252)
        
        # Sharpe Ratio
        excess_return = annualized_return - risk_free_rate
        sharpe = excess_return / annualized_vol if annualized_vol > 0 else 0
        
        # Sortino Ratio (downside deviation)
        downside_returns = portfolio_returns[portfolio_returns < 0]
        downside_std = downside_returns.std() * np.sqrt(252) if len(downside_returns) > 0 else 0
        sortino = excess_return / downside_std if downside_std > 0 else 0
        
        # Max Drawdown
        max_dd = self._calculate_max_drawdown(portfolio_returns)
        
        # Calmar Ratio
        calmar = annualized_return / abs(max_dd) if max_dd != 0 else 0
        
        # VaR and CVaR
        var_95 = np.percentile(portfolio_returns, 5)
        var_99 = np.percentile(portfolio_returns, 1)
        cvar_95 = portfolio_returns[portfolio_returns <= var_95].mean()
        cvar_99 = portfolio_returns[portfolio_returns <= var_99].mean()
        
        # Beta and Alpha (if market data available)
        beta = None
        alpha = None
        info_ratio = None
        treynor = None
        
        if self.market_data is not None:
            aligned_data = pd.concat([portfolio_returns, self.market_data], axis=1).dropna()
            if len(aligned_data) > 30:
                cov = np.cov(aligned_data.iloc[:, 0], aligned_data.iloc[:, 1])
                market_var = aligned_data.iloc[:, 1].var()
                beta = cov[0, 1] / market_var if market_var > 0 else 0
                
                market_return = aligned_data.iloc[:, 1].mean() * 252
                alpha = annualized_return - (risk_free_rate + beta * (market_return - risk_free_rate))
                
                # Information Ratio
                tracking_error = (aligned_data.iloc[:, 0] - aligned_data.iloc[:, 1]).std() * np.sqrt(252)
                info_ratio = (annualized_return - market_return) / tracking_error if tracking_error > 0 else 0
                
                # Treynor Ratio
                treynor = excess_return / beta if beta != 0 else 0
        
        return PortfolioMetrics(
            total_return=total_return,
            annualized_return=annualized_return,
            volatility=volatility,
            annualized_volatility=annualized_vol,
            sharpe_ratio=sharpe,
            sortino_ratio=sortino,
            max_drawdown=max_dd,
            calmar_ratio=calmar,
            var_95=var_95,
            var_99=var_99,
            cvar_95=cvar_95,
            cvar_99=cvar_99,
            beta=beta,
            alpha=alpha,
            information_ratio=info_ratio,
            treynor_ratio=treynor
        )
    
    def optimize_portfolio(self, target_return: Optional[float] = None,
                          risk_free_rate: float = 0.02,
                          constraints: Optional[Dict] = None) -> Dict:
        """
        Mean-variance portfolio optimization.
        
        Optimization:
        min  w'Σw  (portfolio variance)
        s.t. w'μ = target_return
             sum(w) = 1
             w >= 0 (optional long-only)
        """
        returns = self.returns.mean() * 252  # Annualized
        cov_matrix = self.returns.cov() * 252
        n_assets = len(self.assets)
        
        # Constraints
        if constraints is None:
            constraints = {}
        
        long_only = constraints.get('long_only', True)
        max_weight = constraints.get('max_weight', 1.0)
        min_weight = constraints.get('min_weight', 0.0)
        
        # Objective function (negative Sharpe for minimization)
        def negative_sharpe(weights):
            port_return = np.dot(weights, returns)
            port_std = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
            return -(port_return - risk_free_rate) / (port_std + 1e-8)
        
        # Constraints
        cons = [{'type': 'eq', 'fun': lambda x: np.sum(x) - 1}]  # Sum to 1
        
        if target_return is not None:
            cons.append({'type': 'eq', 'fun': lambda x: np.dot(x, returns) - target_return})
        
        # Bounds
        bounds = [(min_weight, max_weight) for _ in range(n_assets)]
        
        # Initial guess
        x0 = np.ones(n_assets) / n_assets
        
        # Optimize
        result = minimize(
            negative_sharpe,
            x0,
            method='SLSQP',
            bounds=bounds,
            constraints=cons,
            options={'ftol': 1e-9, 'disp': False}
        )
        
        optimal_weights = result.x
        opt_return = np.dot(optimal_weights, returns)
        opt_std = np.sqrt(np.dot(optimal_weights.T, np.dot(cov_matrix, optimal_weights)))
        opt_sharpe = (opt_return - risk_free_rate) / opt_std
        
        return {
            'weights': dict(zip(self.assets, optimal_weights)),
            'expected_return': opt_return,
            'expected_volatility': opt_std,
            'sharpe_ratio': opt_sharpe,
            'success': result.success
        }
    
    def _calculate_max_drawdown(self, returns: pd.Series) -> float:
        """Calculate maximum drawdown."""
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        return drawdown.min()
    
    def _estimate_recovery(self, returns: pd.Series, max_dd: float) -> int:
        """Estimate recovery time in days after max drawdown."""
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        
        min_dd_idx = drawdown.idxmin()
        recovery = drawdown.loc[min_dd_idx:]
        recovery_points = recovery[recovery >= -0.001]  # Within 0.1% of recovery
        
        if len(recovery_points) > 0:
            return (recovery_points.index[0] - min_dd_idx).days
        return -1  # Not recovered
