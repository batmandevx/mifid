# RiskGuard Pro - Regulatory Risk Analysis System

<p align="center">
  <img src="https://img.shields.io/badge/version-2.0.0-blue.svg" alt="Version">
  <img src="https://img.shields.io/badge/python-3.11%2B-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-0.109%2B-green.svg" alt="FastAPI">
  <img src="https://img.shields.io/badge/license-Proprietary-red.svg" alt="License">
</p>

<p align="center">
  <b>Enterprise-grade automated regulatory risk analysis platform</b><br>
  Built for Basel III, FRTB, UCITS, EMIR, and MiFID II compliance
</p>

---

## 📋 Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Screenshots](#screenshots)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Usage Guide](#usage-guide)
- [API Documentation](#api-documentation)
- [Architecture](#architecture)
- [Mathematical Models](#mathematical-models)
- [Regulatory Compliance](#regulatory-compliance)
- [Deployment](#deployment)
- [Contributing](#contributing)
- [Support](#support)

---

## 🎯 Overview

**RiskGuard Pro** is a comprehensive, production-ready platform for automated regulatory risk analysis of financial portfolios. It implements industry-standard risk models and generates regulatory-compliant reports for major financial regulations including Basel III, FRTB, UCITS, EMIR, and MiFID II.

### Why RiskGuard Pro?

- **Comprehensive Risk Models**: VaR, ES, GARCH, Backtesting, Stress Testing
- **Regulatory Compliance**: Pre-configured for major financial regulations
- **Modern Architecture**: FastAPI backend with async database operations
- **Professional UI**: Responsive, intuitive interface with real-time visualizations
- **Enterprise Ready**: Authentication, audit trails, multi-format reports

---

## ✨ Key Features

### Risk Analysis Models

| Model | Description | Regulatory Use |
|-------|-------------|----------------|
| **Value at Risk (VaR)** | Historical, Parametric, Monte Carlo, Cornish-Fisher | Basel III, UCITS, EMIR |
| **Expected Shortfall** | 97.5% CVaR with tail analysis | FRTB standard |
| **GARCH(1,1)** | Volatility forecasting with persistence | Internal models |
| **Backtesting** | Kupiec & Christoffersen tests with Basel zones | Basel III validation |
| **Stress Testing** | Predefined & custom scenarios | All regulations |
| **Portfolio Optimization** | Mean-variance with constraints | Portfolio management |

### Statistical Analysis

- Distribution moments (mean, variance, skewness, kurtosis)
- Correlation and covariance matrices
- Principal Component Analysis (PCA)
- K-means cluster analysis
- Factor exposure modeling

### Performance Metrics

- Sharpe Ratio
- Sortino Ratio (downside risk-adjusted)
- Calmar Ratio
- Maximum Drawdown
- Beta and Alpha
- Information Ratio
- Treynor Ratio

### System Features

- **Authentication**: JWT-based with refresh tokens
- **Database**: PostgreSQL/SQLite with SQLAlchemy ORM
- **Reports**: Excel and PDF generation
- **Real-time**: WebSocket support for live updates
- **API**: RESTful with auto-generated documentation
- **UI**: Modern responsive design with interactive charts

---

## 📸 Screenshots

### Dashboard
![Dashboard](docs/screenshots/dashboard.png)
*Real-time risk metrics with performance charts*

### Risk Analysis
![Analysis](docs/screenshots/analysis.png)
*Comprehensive VaR analysis with multiple methodologies*

### Portfolio Optimization
![Portfolio](docs/screenshots/portfolio.png)
*Mean-variance optimization with efficient frontier*

### Report Generation
![Reports](docs/screenshots/reports.png)
*Professional Excel and PDF reports*

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- pip (Python package manager)
- Git

### One-Line Startup

```bash
git clone https://github.com/batmandevx/mifid.git
cd mifid/regulatory-risk-system
./start.sh
```

Then open:
- **Frontend**: http://localhost:8080
- **API Documentation**: http://localhost:8000/docs

---

## 📦 Installation

### Option 1: Local Development

```bash
# Clone repository
git clone https://github.com/batmandevx/mifid.git
cd mifid/regulatory-risk-system

# Run startup script
chmod +x start.sh
./start.sh
```

### Option 2: Docker Deployment

```bash
# Start with Docker Compose
./start.sh docker

# Or manually
cd docker
docker-compose up --build
```

### Option 3: Manual Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create directories
mkdir -p uploads reports data logs

# Start backend
cd backend/api
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Start frontend (new terminal)
cd frontend
python3 -m http.server 8080
```

---

## 📖 Usage Guide

### 1. Dashboard

The dashboard provides an at-a-glance view of your portfolio risk:

- **Portfolio Volatility**: Current volatility with trend indicator
- **99% VaR**: Daily Value at Risk
- **Annualized Return**: Performance vs benchmark
- **Sharpe Ratio**: Risk-adjusted returns

### 2. Data Management

#### Upload Your Data
1. Navigate to **Data Management**
2. Drag & drop CSV/Excel files or click to browse
3. Supported formats: CSV, XLSX, XLS
4. Required format: Date index column + return columns for each asset

#### Generate Sample Data
1. Select time period (3, 5, or 10 years)
2. Choose asset classes (Equities, Bonds, Commodities, FX)
3. Click "Generate Sample Data"
4. System creates realistic data with stress periods

### 3. Risk Analysis

#### Configure Analysis
1. Select dataset from dropdown
2. Enter analysis name
3. Choose analysis type:
   - **Full Analysis**: All models
   - **VaR Only**: Value at Risk focus
   - **PCA Only**: Factor decomposition
   - **GARCH**: Volatility forecasting
   - **Optimization**: Portfolio optimization

4. Set parameters:
   - Regulatory regime (Basel III, FRTB, etc.)
   - VaR method
   - Confidence level (95%, 99%, 99.9%)
   - Time horizon (1-252 days)

5. Click "Run Analysis"

#### View Results
Results are organized in tabs:
- **Moments**: Distribution statistics
- **VaR**: Method comparison with charts
- **PCA**: Explained variance and loadings
- **Correlation**: Asset correlation heatmap
- **GARCH**: Volatility forecasts

### 4. Portfolio

View comprehensive metrics:
- Performance ratios (Sharpe, Sortino, Calmar)
- Risk metrics (VaR, CVaR)
- Maximum drawdown analysis
- Asset allocation visualization

### 5. Reports

Generate professional reports:
1. Select completed analysis
2. Choose format (Excel or PDF)
3. Select regulatory regime
4. Download generated report

Report includes:
- Cover page with metadata
- Executive summary
- Statistical analysis
- VaR comparison tables
- PCA factor decomposition
- Regulatory interpretation
- Compliance notes

---

## 🔌 API Documentation

Interactive API documentation is available at `http://localhost:8000/docs`

### Authentication

```bash
# Login
POST /api/auth/login
{
  "username": "your_username",
  "password": "your_password"
}

# Response
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer"
}
```

### Key Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/datasets` | GET | List all datasets |
| `/api/datasets/upload` | POST | Upload CSV/Excel file |
| `/api/analyses` | POST | Create new analysis |
| `/api/analyses/{id}` | GET | Get analysis results |
| `/api/reports` | POST | Generate report |
| `/api/sample-data` | POST | Generate sample data |

### Example: Run Analysis

```python
import requests

# Set API base URL and token
API_URL = "http://localhost:8000"
headers = {"Authorization": f"Bearer {token}"}

# Upload dataset
with open("portfolio_returns.csv", "rb") as f:
    response = requests.post(
        f"{API_URL}/api/datasets/upload",
        files={"file": f},
        headers=headers
    )
dataset_id = response.json()["dataset_id"]

# Run analysis
response = requests.post(
    f"{API_URL}/api/analyses",
    headers=headers,
    json={
        "dataset_id": dataset_id,
        "name": "Basel III VaR Analysis",
        "analysis_type": "full",
        "regime": "basel_iii",
        "confidence_level": 0.99,
        "time_horizon": 10,
        "var_method": "historical"
    }
)
results = response.json()
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Web UI     │  │   Excel      │  │   API        │          │
│  │   (Browser)  │  │   Reports    │  │   Clients    │          │
│  └──────┬───────┘  └──────────────┘  └──────────────┘          │
└─────────┼───────────────────────────────────────────────────────┘
          │ HTTPS
┌─────────┼───────────────────────────────────────────────────────┐
│         ▼                                                        │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              API LAYER (FastAPI)                         │    │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐       │    │
│  │  │  Datasets   │ │  Analysis   │ │   Reports   │       │    │
│  │  └─────────────┘ └─────────────┘ └─────────────┘       │    │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐       │    │
│  │  │    Auth     │ │  WebSocket  │ │    Users    │       │    │
│  │  └─────────────┘ └─────────────┘ └─────────────┘       │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
          │
┌─────────┼───────────────────────────────────────────────────────┐
│         ▼                                                        │
│                    SERVICE LAYER                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              Statistical Risk Analyzer                   │    │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐       │    │
│  │  │     VaR     │ │    ES       │ │   GARCH     │       │    │
│  │  └─────────────┘ └─────────────┘ └─────────────┘       │    │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐       │    │
│  │  │Backtesting  │ │Stress Test  │ │Optimization │       │    │
│  │  └─────────────┘ └─────────────┘ └─────────────┘       │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              Report Generators                           │    │
│  │         (Excel + PDF with Regulatory Formatting)         │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
          │
┌─────────┼───────────────────────────────────────────────────────┐
│         ▼                                                        │
│                         DATA LAYER                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  PostgreSQL  │  │    Redis     │  │  File Store  │          │
│  │   (Primary)  │  │   (Cache)    │  │ (Uploads/    │          │
│  │              │  │              │  │  Reports)    │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

### Technology Stack

| Layer | Technologies |
|-------|--------------|
| **Frontend** | HTML5, CSS3, Bootstrap 5, Plotly.js, Chart.js |
| **Backend** | Python 3.11, FastAPI, Uvicorn |
| **Database** | PostgreSQL 15, SQLAlchemy 2.0, Alembic |
| **Cache** | Redis 7 |
| **Models** | NumPy, Pandas, SciPy, Scikit-learn |
| **Reports** | OpenPyXL, XlsxWriter, ReportLab |
| **Deployment** | Docker, Docker Compose, Nginx |

---

## 📐 Mathematical Models

### Value at Risk (VaR)

$$\text{VaR}_{\alpha,T} = \inf\{l \in \mathbb{R}: P(L > l) \leq 1 - \alpha\}$$

**Methods:**
- **Historical**: $\text{VaR}_{\alpha} = \text{Quantile}(\{R_t\}, 1-\alpha)$
- **Parametric**: $\text{VaR}_{\alpha} = \mu - z_{\alpha} \cdot \sigma$
- **Monte Carlo**: Simulation-based
- **Cornish-Fisher**: Adjusts for skewness and kurtosis

### Expected Shortfall (FRTB)

$$\text{ES}_{\alpha} = \frac{1}{1-\alpha} \int_{\alpha}^{1} \text{VaR}_u \, du$$

### GARCH(1,1)

$$\sigma_t^2 = \omega + \alpha \cdot r_{t-1}^2 + \beta \cdot \sigma_{t-1}^2$$

### Backtesting (Kupiec Test)

$$LR_{uc} = -2\ln\left(\frac{(1-p)^{T-N}p^N}{(1-N/T)^{T-N}(N/T)^N}\right) \sim \chi^2(1)$$

See [docs/MATHEMATICAL_FOUNDATIONS.md](docs/MATHEMATICAL_FOUNDATIONS.md) for complete documentation.

---

## 📜 Regulatory Compliance

### Basel III

| Requirement | Implementation |
|-------------|----------------|
| 99% VaR, 10-day | ✓ Historical, Parametric, Monte Carlo |
| Stressed VaR | ✓ Stress period calibration |
| Backtesting | ✓ Traffic light approach |
| Multiplier | ✓ 3.0-4.0x based on exceptions |

### FRTB (Fundamental Review of Trading Book)

| Requirement | Implementation |
|-------------|----------------|
| 97.5% Expected Shortfall | ✓ ES calculation |
| 10-day horizon | ✓ Configurable horizons |
| NMRF identification | ✓ PCA factor analysis |
| Liquidity horizons | ✓ Stress period modeling |

### UCITS

| Requirement | Implementation |
|-------------|----------------|
| 99% VaR, monthly | ✓ VaR with time scaling |
| Leverage limit (2x) | ✓ Portfolio constraints |
| Diversification | ✓ Correlation analysis |

### EMIR & MiFID II

- Daily risk calculations
- Model validation framework
- Audit trail compliance
- Product governance support

---

## 🚀 Deployment

### Docker (Recommended)

```bash
# Production deployment
cd docker
docker-compose -f docker-compose.yml up -d

# View logs
docker-compose logs -f api

# Scale API instances
docker-compose up -d --scale api=3
```

### Cloud Deployment

#### AWS
```bash
# Using ECS
aws ecs create-service \
  --cluster riskguard-cluster \
  --service-name riskguard-api \
  --task-definition riskguard:1 \
  --desired-count 2
```

#### Azure
```bash
# Using Container Instances
az container create \
  --resource-group myResourceGroup \
  --name riskguard-api \
  --image riskguard:latest \
  --cpu 2 --memory 4
```

### Environment Variables

```env
# Application
DEBUG=false
ENVIRONMENT=production
SECRET_KEY=your-secure-secret-key

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/risk_system

# Redis
REDIS_URL=redis://localhost:6379/0

# Email
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

---

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
pytest backend/tests/ -v --cov=backend

# Run linting
flake8 backend/
black backend/

# Type checking
mypy backend/
```

---

## 📞 Support

### Documentation
- [API Documentation](http://localhost:8000/docs) (when running locally)
- [Mathematical Foundations](docs/MATHEMATICAL_FOUNDATIONS.md)
- [Architecture Guide](docs/ARCHITECTURE.md)

### Contact
- **Email**: support@riskguard.com
- **Issues**: [GitHub Issues](https://github.com/batmandevx/mifid/issues)
- **Discussions**: [GitHub Discussions](https://github.com/batmandevx/mifid/discussions)

---

## 📄 License

This software is proprietary and confidential. Unauthorized copying, distribution, or use is strictly prohibited.

Copyright © 2026 RiskGuard Pro. All rights reserved.

---

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) for the amazing web framework
- [Plotly](https://plotly.com/) for interactive visualizations
- [SQLAlchemy](https://www.sqlalchemy.org/) for database ORM
- [scikit-learn](https://scikit-learn.org/) for machine learning utilities

---

<p align="center">
  <b>Built with ❤️ for the financial risk management community</b>
</p>

<p align="center">
  <a href="https://github.com/batmandevx/mifid">GitHub</a> •
  <a href="#documentation">Documentation</a> •
  <a href="#support">Support</a>
</p>
