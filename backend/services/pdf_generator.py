"""
PDF Report Generator
====================
Generate professional PDF reports with charts and regulatory interpretations.
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.piecharts import Pie
from datetime import datetime
from typing import Dict, Any, Optional
import matplotlib.pyplot as plt
import numpy as np
import io
import os


class PDFReportGenerator:
    """Generate professional PDF risk reports."""
    
    def __init__(self, risk_results: Dict[str, Any], regime: str = 'basel_iii'):
        self.risk_results = risk_results
        self.regime = regime
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles."""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            fontSize=24,
            leading=28,
            alignment=TA_CENTER,
            spaceAfter=30,
            textColor=colors.HexColor('#1a472a')
        ))
        
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            fontSize=16,
            leading=20,
            spaceAfter=12,
            textColor=colors.HexColor('#2c5282'),
            fontName='Helvetica-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name='SubHeader',
            fontSize=12,
            leading=14,
            spaceAfter=6,
            textColor=colors.HexColor('#4a5568'),
            fontName='Helvetica-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name='BodyText',
            fontSize=10,
            leading=12,
            spaceAfter=6
        ))
        
        self.styles.add(ParagraphStyle(
            name='Warning',
            fontSize=10,
            leading=12,
            textColor=colors.HexColor('#c53030'),
            spaceAfter=6
        ))
        
        self.styles.add(ParagraphStyle(
            name='Success',
            fontSize=10,
            leading=12,
            textColor=colors.HexColor('#276749'),
            spaceAfter=6
        ))
    
    def generate_pdf_report(self, output_path: str) -> str:
        """Generate PDF report."""
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        story = []
        
        # Cover page
        story.extend(self._create_cover_page())
        story.append(PageBreak())
        
        # Executive summary
        story.extend(self._create_executive_summary())
        story.append(PageBreak())
        
        # Risk metrics
        story.extend(self._create_risk_metrics())
        story.append(PageBreak())
        
        # VaR analysis
        story.extend(self._create_var_analysis())
        story.append(PageBreak())
        
        # Statistical analysis
        story.extend(self._create_statistical_analysis())
        story.append(PageBreak())
        
        # PCA analysis
        story.extend(self._create_pca_analysis())
        story.append(PageBreak())
        
        # Regulatory interpretation
        story.extend(self._create_regulatory_section())
        
        doc.build(story)
        return output_path
    
    def _create_cover_page(self):
        """Create cover page."""
        story = []
        
        story.append(Spacer(1, 2*inch))
        story.append(Paragraph("Regulatory Risk Analysis Report", self.styles['CustomTitle']))
        story.append(Spacer(1, 0.5*inch))
        
        story.append(Paragraph(f"Regime: {self.regime.upper()}", self.styles['SectionHeader']))
        story.append(Spacer(1, 0.3*inch))
        
        story.append(Paragraph(
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            self.styles['BodyText']
        ))
        story.append(Paragraph(
            f"Version: 2.0",
            self.styles['BodyText']
        ))
        
        story.append(Spacer(1, 2*inch))
        
        # Disclaimer
        story.append(Paragraph(
            "CONFIDENTIAL - For internal use only. This report contains risk analysis "
            "metrics intended for regulatory compliance and risk management purposes.",
            self.styles['BodyText']
        ))
        
        return story
    
    def _create_executive_summary(self):
        """Create executive summary section."""
        story = []
        story.append(Paragraph("Executive Summary", self.styles['SectionHeader']))
        story.append(Spacer(1, 0.2*inch))
        
        portfolio = self.risk_results.get('statistical_moments', {}).get('portfolio', {})
        var_results = self.risk_results.get('var_analysis', {}).get('historical', {})
        metrics = self.risk_results.get('portfolio_metrics', {})
        
        # Key metrics table
        data = [
            ['Metric', 'Value', 'Assessment'],
            ['Portfolio Volatility', f"{portfolio.get('std_dev', 0)*100:.2f}%", ''],
            ['99% VaR (Daily)', f"{var_results.get('var_99', 0)*100:.2f}%", ''],
            ['99% CVaR', f"{var_results.get('cvar_99', 0)*100:.2f}%", ''],
            ['Sharpe Ratio', f"{metrics.get('sharpe_ratio', 0):.2f}", ''],
            ['Max Drawdown', f"{metrics.get('max_drawdown', 0)*100:.2f}%", ''],
        ]
        
        table = Table(data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5282')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ]))
        
        story.append(table)
        story.append(Spacer(1, 0.3*inch))
        
        # Risk indicators
        story.append(Paragraph("Key Risk Indicators:", self.styles['SubHeader']))
        
        skewness = portfolio.get('skewness', 0)
        kurtosis = portfolio.get('excess_kurtosis', 0)
        
        if skewness < -0.5:
            story.append(Paragraph(
                f"⚠️ Negative Skewness ({skewness:.2f}): Left tail risk detected",
                self.styles['Warning']
            ))
        
        if kurtosis > 1:
            story.append(Paragraph(
                f"⚠️ High Kurtosis ({kurtosis:.2f}): Fat tails indicate extreme event risk",
                self.styles['Warning']
            ))
        
        story.append(Spacer(1, 0.2*inch))
        
        # Regulatory compliance note
        story.append(Paragraph("Regulatory Compliance:", self.styles['SubHeader']))
        story.append(Paragraph(
            f"This analysis follows {self.regime.upper()} guidelines for risk measurement "
            f"and regulatory capital calculation.",
            self.styles['BodyText']
        ))
        
        return story
    
    def _create_risk_metrics(self):
        """Create risk metrics section."""
        story = []
        story.append(Paragraph("Risk Metrics", self.styles['SectionHeader']))
        story.append(Spacer(1, 0.2*inch))
        
        metrics = self.risk_results.get('portfolio_metrics', {})
        
        data = [
            ['Performance Metrics', 'Value'],
            ['Total Return', f"{metrics.get('total_return', 0)*100:.2f}%"],
            ['Annualized Return', f"{metrics.get('annualized_return', 0)*100:.2f}%"],
            ['Annualized Volatility', f"{metrics.get('annualized_volatility', 0)*100:.2f}%"],
            ['Sharpe Ratio', f"{metrics.get('sharpe_ratio', 0):.2f}"],
            ['Sortino Ratio', f"{metrics.get('sortino_ratio', 0):.2f}"],
            ['Calmar Ratio', f"{metrics.get('calmar_ratio', 0):.2f}"],
            ['Maximum Drawdown', f"{metrics.get('max_drawdown', 0)*100:.2f}%"],
        ]
        
        table = Table(data, colWidths=[2.5*inch, 2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5282')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ]))
        
        story.append(table)
        
        return story
    
    def _create_var_analysis(self):
        """Create VaR analysis section."""
        story = []
        story.append(Paragraph("Value at Risk Analysis", self.styles['SectionHeader']))
        story.append(Spacer(1, 0.2*inch))
        
        var_analysis = self.risk_results.get('var_analysis', {})
        
        data = [['Method', 'VaR 95%', 'VaR 99%', 'CVaR 99%']]
        
        for method, results in var_analysis.items():
            if isinstance(results, dict) and 'error' not in results:
                data.append([
                    method.replace('_', ' ').title(),
                    f"{results.get('var_95', 0)*100:.2f}%",
                    f"{results.get('var_99', 0)*100:.2f}%",
                    f"{results.get('cvar_99', 0)*100:.2f}%"
                ])
        
        table = Table(data, colWidths=[1.75*inch, 1.25*inch, 1.25*inch, 1.25*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5282')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        story.append(table)
        story.append(Spacer(1, 0.2*inch))
        
        # Method explanations
        story.append(Paragraph("Methodology Notes:", self.styles['SubHeader']))
        
        explanations = {
            'historical': 'Uses empirical quantiles from historical returns. Non-parametric.',
            'parametric': 'Assumes normal distribution. Fast but may underestimate tail risk.',
            'monte_carlo': 'Simulates thousands of scenarios. Flexible but computationally intensive.',
            'cornish_fisher': 'Adjusts for skewness and kurtosis. Better tail risk estimation.'
        }
        
        for method, explanation in explanations.items():
            if method in var_analysis:
                story.append(Paragraph(
                    f"• <b>{method.title()}:</b> {explanation}",
                    self.styles['BodyText']
                ))
        
        return story
    
    def _create_statistical_analysis(self):
        """Create statistical analysis section."""
        story = []
        story.append(Paragraph("Statistical Analysis", self.styles['SectionHeader']))
        story.append(Spacer(1, 0.2*inch))
        
        moments = self.risk_results.get('statistical_moments', {})
        portfolio = moments.get('portfolio', {})
        
        story.append(Paragraph("Portfolio Distribution Moments:", self.styles['SubHeader']))
        
        data = [
            ['Moment', 'Value', 'Interpretation'],
            ['Mean', f"{portfolio.get('mean', 0):.6f}", 'Average return'],
            ['Variance', f"{portfolio.get('variance', 0):.6f}", 'Return dispersion'],
            ['Std Deviation', f"{portfolio.get('std_dev', 0):.4f}", 'Volatility'],
            ['Skewness', f"{portfolio.get('skewness', 0):.4f}", 'Asymmetry'],
            ['Excess Kurtosis', f"{portfolio.get('excess_kurtosis', 0):.4f}", 'Tail heaviness'],
        ]
        
        table = Table(data, colWidths=[1.75*inch, 1.25*inch, 2.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5282')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        story.append(table)
        
        # Interpretation
        story.append(Spacer(1, 0.2*inch))
        story.append(Paragraph("Distribution Analysis:", self.styles['SubHeader']))
        
        skew = portfolio.get('skewness', 0)
        kurt = portfolio.get('excess_kurtosis', 0)
        
        if abs(skew) < 0.5:
            story.append(Paragraph(
                "• Skewness is near zero, indicating approximately symmetric distribution.",
                self.styles['BodyText']
            ))
        elif skew < 0:
            story.append(Paragraph(
                "• Negative skewness indicates left tail risk. Extreme losses more likely than gains.",
                self.styles['Warning']
            ))
        else:
            story.append(Paragraph(
                "• Positive skewness indicates right tail risk. Extreme gains more likely.",
                self.styles['BodyText']
            ))
        
        if kurt > 1:
            story.append(Paragraph(
                f"• High excess kurtosis ({kurt:.2f}) indicates fat tails. "
                "Normal distribution assumptions may be invalid.",
                self.styles['Warning']
            ))
        
        return story
    
    def _create_pca_analysis(self):
        """Create PCA analysis section."""
        story = []
        story.append(Paragraph("Principal Component Analysis", self.styles['SectionHeader']))
        story.append(Spacer(1, 0.2*inch))
        
        pca = self.risk_results.get('pca_analysis', {})
        evr = pca.get('explained_variance_ratio', [])
        
        if evr:
            story.append(Paragraph("Explained Variance by Component:", self.styles['SubHeader']))
            
            data = [['Component', 'Explained Variance', 'Cumulative']]
            cumsum = 0
            for i, var in enumerate(evr[:5]):
                cumsum += var
                data.append([f'PC{i+1}', f"{var*100:.2f}%", f"{cumsum*100:.2f}%"])
            
            table = Table(data, colWidths=[1.5*inch, 1.75*inch, 1.75*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5282')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            
            story.append(table)
            
            story.append(Spacer(1, 0.2*inch))
            story.append(Paragraph("Factor Interpretation:", self.styles['SubHeader']))
            story.append(Paragraph(
                f"• PC1 explains {evr[0]*100:.1f}% of total variance, representing the market/systematic factor.",
                self.styles['BodyText']
            ))
            if len(evr) > 1:
                story.append(Paragraph(
                    f"• PC2 explains {evr[1]*100:.1f}% of variance, typically representing sector or curve factors.",
                    self.styles['BodyText']
                ))
        
        return story
    
    def _create_regulatory_section(self):
        """Create regulatory compliance section."""
        story = []
        story.append(Paragraph("Regulatory Compliance", self.styles['SectionHeader']))
        story.append(Spacer(1, 0.2*inch))
        
        # Regime-specific content
        regime_info = {
            'basel_iii': {
                'name': 'Basel III Market Risk',
                'requirements': [
                    '99% VaR, 10-day holding period',
                    'Stressed VaR for market risk capital',
                    'Backtesting with traffic light approach',
                    'Multiplier 3-4 based on backtest results'
                ]
            },
            'frtb': {
                'name': 'FRTB (Fundamental Review of Trading Book)',
                'requirements': [
                    '97.5% Expected Shortfall (ES)',
                    '10-day horizon, liquidity adjustments',
                    'Non-modellable risk factor (NMRF) identification',
                    'Factor sensitivity approach'
                ]
            },
            'ucits': {
                'name': 'UCITS Global Exposure',
                'requirements': [
                    '99% VaR, monthly horizon',
                    'Leverage limit: 2x (Commitment Approach)',
                    'Diversification requirements',
                    'Risk management process documentation'
                ]
            }
        }
        
        info = regime_info.get(self.regime, regime_info['basel_iii'])
        
        story.append(Paragraph(f"Regime: {info['name']}", self.styles['SubHeader']))
        story.append(Paragraph("Key Requirements:", self.styles['BodyText']))
        
        for req in info['requirements']:
            story.append(Paragraph(f"• {req}", self.styles['BodyText']))
        
        story.append(Spacer(1, 0.3*inch))
        
        # Compliance notes
        story.append(Paragraph("Compliance Notes:", self.styles['SubHeader']))
        story.append(Paragraph(
            "This report provides indicative risk metrics based on historical data analysis. "
            "Formal regulatory submissions require additional model validation, documentation, "
            "and governance processes as specified by the relevant regulatory framework.",
            self.styles['BodyText']
        ))
        
        story.append(Spacer(1, 0.3*inch))
        
        # Disclaimer
        story.append(Paragraph("Disclaimer", self.styles['SubHeader']))
        story.append(Paragraph(
            "The risk metrics presented in this report are based on statistical models and "
            "historical data. Past performance is not indicative of future results. "
            "Extreme market events may cause losses exceeding VaR estimates. "
            "This report should be used as part of a comprehensive risk management framework.",
            self.styles['BodyText']
        ))
        
        return story
