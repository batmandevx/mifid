#!/usr/bin/env python3
"""
Advanced Risk Analysis Demo
===========================
Demonstrates the enhanced features of Risk Analysis System v2.0
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

import numpy as np
import pandas as pd
from datetime import datetime

from utils.data_generator import FinancialDataGenerator
from models.statistical_models import StatisticalRiskAnalyzer
from models.statistical_models import VaRMethod
from models.advanced_risk_models import (
    AdvancedRiskAnalyzer, BacktestResult, StressTestResult
)


def print_header(title):
    print("\n" + "="*75)
    print(f"  {title}")
    print("="*75)


def print_metric(name, value, unit=""):
    print(f"  {name:.<45} {value:>15} {unit}")


def main():
    print("""
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║     REGULATORY RISK ANALYSIS SYSTEM v2.0                                  ║
║     Advanced Features Demonstration                                       ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝
    """)
    
    # Generate comprehensive dataset
    print_header("STEP 1: GENERATING COMPREHENSIVE DATASET")
    
    generator = FinancialDataGenerator(seed=42)
    returns = generator.generate_returns(
        n_observations=252*5,  # 5 years
        asset_classes=['equities', 'bonds', 'commodities', 'fx'],
        start_date='2019-01-01',
        include_stress_periods=True
    )
    
    print(f"\n  ✓ Generated multi-asset dataset:")
    print(f"    • Total observations: {len(returns):,}")
    print(f"    • Number of assets: {len(returns.columns)}")
    print(f"    • Asset classes: Equities, Bonds, Commodities, FX")
    print(f"    • Date range: {returns.index[0].date()} to {returns.index[-1].date()}")
    print(f"    • Assets: {', '.join(returns.columns[:8])}, ...")
    
    # Initialize analyzers
    basic_analyzer = StatisticalRiskAnalyzer(returns)
    advanced_analyzer = AdvancedRiskAnalyzer(returns)
    
    # =========================================================================
    # PORTFOLIO METRICS
    # =========================================================================
    print_header("STEP 2: COMPREHENSIVE PORTFOLIO METRICS")
    
    metrics = advanced_analyzer.calculate_portfolio_metrics()
    
    print("\n  Performance Metrics:")
    print_metric("Total Return", f"{metrics.total_return*100:.2f}", "%")
    print_metric("Annualized Return", f"{metrics.annualized_return*100:.2f}", "%")
    print_metric("Annualized Volatility", f"{metrics.annualized_volatility*100:.2f}", "%")
    print_metric("Sharpe Ratio", f"{metrics.sharpe_ratio:.3f}", "")
    print_metric("Sortino Ratio", f"{metrics.sortino_ratio:.3f}", "")
    print_metric("Maximum Drawdown", f"{metrics.max_drawdown*100:.2f}", "%")
    print_metric("Calmar Ratio", f"{metrics.calmar_ratio:.3f}", "")
    
    print("\n  Risk Metrics:")
    print_metric("Daily VaR (95%)", f"{metrics.var_95*100:.2f}", "%")
    print_metric("Daily VaR (99%)", f"{metrics.var_99*100:.2f}", "%")
    print_metric("Daily CVaR (95%)", f"{metrics.cvar_95*100:.2f}", "%")
    print_metric("Daily CVaR (99%)", f"{metrics.cvar_99*100:.2f}", "%")
    
    # Assessment
    print("\n  Portfolio Assessment:")
    if metrics.sharpe_ratio > 1:
        print("    ✓ Excellent risk-adjusted returns (Sharpe > 1)")
    elif metrics.sharpe_ratio > 0.5:
        print("    ⚠ Moderate risk-adjusted returns")
    else:
        print("    ⚠ Poor risk-adjusted returns")
    
    if abs(metrics.max_drawdown) > 0.2:
        print("    ⚠ High drawdown risk (>20%)")
    else:
        print("    ✓ Manageable drawdown risk")
    
    # =========================================================================
    # VaR ANALYSIS
    # =========================================================================
    print_header("STEP 3: VALUE AT RISK (VaR) ANALYSIS")
    
    print("\n  99% VaR Comparison (10-day horizon):")
    print("  " + "-"*70)
    print(f"  {'Method':<20} {'VaR':>12} {'CVaR (ES)':>14} {'Assessment'}")
    print("  " + "-"*70)
    
    for method in VaRMethod:
        try:
            var_result = basic_analyzer.calculate_var(
                confidence_level=0.99,
                time_horizon=10,
                method=method
            )
            var_pct = var_result.var_99 * 100
            cvar_pct = var_result.cvar_99 * 100
            
            if var_pct < -5:
                assessment = "🔴 High Risk"
            elif var_pct < -3:
                assessment = "🟡 Moderate Risk"
            else:
                assessment = "🟢 Lower Risk"
            
            print(f"  {method.value.upper():<20} {var_pct:>10.2f}% {cvar_pct:>12.2f}%  {assessment}")
        except Exception as e:
            print(f"  {method.value.upper():<20} {'Error':>12} {'':>14}  {e}")
    
    print("  " + "-"*70)
    
    print("\n  Methodology Notes:")
    print("    • Historical: Non-parametric, uses actual data")
    print("    • Parametric: Assumes normal distribution")
    print("    • Monte Carlo: Simulation-based, flexible")
    print("    • Cornish-Fisher: Adjusts for skewness/kurtosis")
    
    # =========================================================================
    # EXPECTED SHORTFALL (FRTB)
    # =========================================================================
    print_header("STEP 4: EXPECTED SHORTFALL (FRTB Standard)")
    
    es_result = advanced_analyzer.calculate_expected_shortfall(
        confidence_level=0.975,
        time_horizon=10
    )
    
    print("\n  FRTB Expected Shortfall (97.5% confidence, 10-day):")
    print_metric("ES at 95%", f"{es_result.es_95*100:.2f}", "%")
    print_metric("ES at 99%", f"{es_result.es_99*100:.2f}", "%")
    print_metric("ES at 99.9%", f"{es_result.es_999*100:.2f}", "%")
    
    print("\n  FRTB Compliance:")
    print("    → ES more sensitive to tail risk than VaR")
    print("    → Sub-additive: coherent risk measure")
    print("    → Required for trading book capital calculations")
    
    # =========================================================================
    # GARCH VOLATILITY
    # =========================================================================
    print_header("STEP 5: GARCH VOLATILITY FORECASTING")
    
    garch_result = advanced_analyzer.fit_garch(forecast_horizon=10)
    
    if garch_result:
        print("\n  GARCH(1,1) Model Parameters:")
        print_metric("Omega (ω)", f"{garch_result.omega:.6f}", "")
        print_metric("Alpha (α)", f"{garch_result.alpha:.4f}", "")
        print_metric("Beta (β)", f"{garch_result.beta:.4f}", "")
        print_metric("Persistence (α+β)", f"{garch_result.persistence:.4f}", "")
        print_metric("Half-life", f"{garch_result.half_life:.1f}", "days")
        print_metric("Annualized Volatility", f"{garch_result.annualized_volatility*100:.2f}", "%")
        
        print("\n  Model Diagnostics:")
        print_metric("AIC", f"{garch_result.aic:.2f}", "")
        print_metric("BIC", f"{garch_result.bic:.2f}", "")
        
        print("\n  Interpretation:")
        if garch_result.persistence > 0.95:
            print("    ⚠ High persistence: Volatility shocks decay slowly")
        else:
            print("    ✓ Moderate persistence: Volatility mean-reverts")
        
        print("    • Alpha captures reaction to market shocks")
        print("    • Beta captures volatility clustering")
    else:
        print("\n  ⚠ GARCH modeling requires 'arch' package")
        print("    Install with: pip install arch")
    
    # =========================================================================
    # BACKTESTING
    # =========================================================================
    print_header("STEP 6: VaR BACKTESTING (Basel III)")
    
    # Calculate VaR predictions for backtesting
    portfolio_returns = returns.mean(axis=1)  # Equal-weighted portfolio
    var_99_predictions = np.full(len(portfolio_returns), np.percentile(portfolio_returns, 1))
    
    backtest = advanced_analyzer.backtest_var(
        var_predictions=var_99_predictions,
        actual_returns=portfolio_returns.values,
        confidence_level=0.99
    )
    
    print("\n  Backtest Results:")
    print_metric("Observations", f"{backtest.n_observations:,}", "")
    print_metric("Exceptions", f"{backtest.n_exceptions}", "")
    print_metric("Exception Rate", f"{backtest.exception_rate*100:.2f}", "%")
    print_metric("Expected Rate", f"{backtest.expected_exceptions/backtest.n_observations*100:.2f}", "%")
    
    print("\n  Statistical Tests:")
    print_metric("Kupiec p-value", f"{backtest.kupiec_pvalue:.4f}", "")
    print_metric("Christoffersen p-value", f"{backtest.christoffersen_pvalue:.4f}", "")
    
    print(f"\n  Basel III Zone: {backtest.traffic_light.upper()} ZONE")
    print(f"  Basel Multiplier: {backtest.basel_multiplier:.2f}x")
    
    if backtest.zone == "green":
        print("    ✓ Model is performing adequately")
    elif backtest.zone == "yellow":
        print("    ⚠ Model requires attention")
    else:
        print("    🔴 Model is inadequate - capital penalty applies")
    
    # =========================================================================
    # STRESS TESTING
    # =========================================================================
    print_header("STEP 7: STRESS TESTING")
    
    scenarios = [
        {"name": "Market Crash 2008", "type": "historical", "shock": -0.30},
        {"name": "Flash Crash", "type": "liquidity", "shock": -0.10},
        {"name": "Interest Rate Shock", "type": "rate", "shock": -0.05},
        {"name": "Credit Crisis", "type": "credit", "shock": -0.15}
    ]
    
    stress_results = advanced_analyzer.stress_test(scenarios)
    
    print("\n  Scenario Analysis:")
    print("  " + "-"*70)
    print(f"  {'Scenario':<25} {'Shock':>10} {'Portfolio Loss':>16} {'Max DD'}")
    print("  " + "-"*70)
    
    for result in stress_results:
        print(f"  {result.scenario_name:<25} {result.shock_magnitude*100:>8.1f}% {result.portfolio_return*100:>14.2f}% {result.max_drawdown*100:>8.1f}%")
    
    print("  " + "-"*70)
    
    print("\n  Stress Test Interpretation:")
    print("    → Scenarios test portfolio resilience")
    print("    → Recovery days indicate liquidity risk")
    print("    → Basel III requires stress testing for capital")
    
    # =========================================================================
    # PORTFOLIO OPTIMIZATION
    # =========================================================================
    print_header("STEP 8: PORTFOLIO OPTIMIZATION")
    
    opt_result = advanced_analyzer.optimize_portfolio(
        risk_free_rate=0.02,
        constraints={"long_only": True, "max_weight": 0.20}
    )
    
    print("\n  Optimal Portfolio (Max Sharpe Ratio):")
    print_metric("Expected Return", f"{opt_result['expected_return']*100:.2f}", "%")
    print_metric("Expected Volatility", f"{opt_result['expected_volatility']*100:.2f}", "%")
    print_metric("Sharpe Ratio", f"{opt_result['sharpe_ratio']:.3f}", "")
    
    print("\n  Optimal Weights (Top 10):")
    weights = opt_result['weights']
    sorted_weights = sorted(weights.items(), key=lambda x: x[1], reverse=True)[:10]
    for asset, weight in sorted_weights:
        print(f"    {asset:<10} {weight*100:>8.2f}%")
    
    # =========================================================================
    # SUMMARY
    # =========================================================================
    print_header("DEMONSTRATION COMPLETE")
    
    print("""
  Risk Analysis System v2.0 provides:

  ✓ Advanced VaR methodologies (4 methods)
  ✓ Expected Shortfall (FRTB compliant)
  ✓ GARCH volatility forecasting
  ✓ Backtesting with Basel III zones
  ✓ Stress testing scenarios
  ✓ Portfolio optimization
  ✓ Comprehensive performance metrics
  ✓ Database persistence
  ✓ User authentication
  ✓ Excel & PDF reports
  ✓ RESTful API
  ✓ Modern web interface

  To start the full system:
    $ ./start.sh

  Access the application:
    • Frontend: http://localhost:8080
    • API:      http://localhost:8000
    • Docs:     http://localhost:8000/docs
    """)
    
    print("="*75)
    print(f"  Demo completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*75 + "\n")


if __name__ == "__main__":
    main()
