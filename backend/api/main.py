"""
Enhanced FastAPI Application
============================
Production-ready API with authentication, WebSocket support,
database integration, and comprehensive risk analysis endpoints.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from contextlib import asynccontextmanager
import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import logging
import uuid
import asyncio

# Core imports
from core.config import settings
from core.database import init_db, close_db, get_db

# Model imports
from models.database_models import (
    User, Dataset, Analysis, Report, RiskLimit, AuditLog,
    generate_uuid
)
from models.statistical_models import StatisticalRiskAnalyzer, VaRMethod
from models.advanced_risk_models import AdvancedRiskAnalyzer

# Service imports
from services import ReportGenerator, PDFReportGenerator

from services.email_service import EmailService
from utils.data_generator import FinancialDataGenerator

# Auth imports
from api.auth import (
    create_access_token, verify_token, get_current_user,
    authenticate_user, create_user
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting up...")
    await init_db()
    yield
    # Shutdown
    logger.info("Shutting down...")
    await close_db()

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="""
    Enhanced Automated Regulatory Risk Analysis System
    
    ## Features
    
    * **Authentication**: JWT-based secure access
    * **Risk Analysis**: VaR, ES, GARCH, Backtesting, Stress Testing
    * **Portfolio Optimization**: Mean-variance optimization
    * **Regulatory Compliance**: Basel III, FRTB, UCITS, EMIR, MiFID II
    * **Real-time**: WebSocket support for live updates
    * **Reports**: Excel, PDF, and HTML report generation
    """,
    version=settings.APP_VERSION,
    lifespan=lifespan
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Security
security = HTTPBearer()

# WebSocket connections manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_json(message)

manager = ConnectionManager()


# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@app.post("/api/auth/register")
async def register(
    email: str,
    username: str,
    password: str,
    full_name: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Register a new user."""
    user = await create_user(db, email, username, password, full_name)
    return {
        "success": True,
        "user_id": user.id,
        "message": "User registered successfully"
    }


@app.post("/api/auth/login")
async def login(
    username: str,
    password: str,
    db: AsyncSession = Depends(get_db)
):
    """Login and get access token."""
    user = await authenticate_user(db, username, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    access_token = create_access_token(
        data={"sub": user.id, "username": user.username}
    )
    
    # Update last login
    user.last_login = datetime.now()
    await db.commit()
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "username": user.username
    }


@app.get("/api/auth/me")
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user info."""
    return {
        "user_id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "created_at": current_user.created_at
    }


# ============================================================================
# DATASET ENDPOINTS
# ============================================================================

@app.post("/api/datasets/upload")
async def upload_dataset(
    file: UploadFile = File(...),
    asset_classes: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload a financial dataset."""
    try:
        # Validate file
        file_ext = file.filename.split('.')[-1].lower()
        if file_ext not in ['csv', 'xlsx', 'xls']:
            raise HTTPException(400, "Only CSV and Excel files supported")
        
        # Generate file ID and save
        file_id = generate_uuid()
        file_path = os.path.join(settings.UPLOAD_DIR, f"{file_id}.{file_ext}")
        
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Load and validate
        if file_ext == 'csv':
            df = pd.read_csv(file_path, index_col=0, parse_dates=True)
        else:
            df = pd.read_excel(file_path, index_col=0, parse_dates=True)
        
        if df.empty:
            raise HTTPException(400, "File is empty")
        
        # Create dataset record
        dataset = Dataset(
            id=file_id,
            user_id=current_user.id,
            filename=file.filename,
            original_filename=file.filename,
            file_path=file_path,
            file_size=os.path.getsize(file_path),
            file_type=file_ext,
            asset_classes=json.loads(asset_classes) if asset_classes else [],
            assets=df.columns.tolist(),
            n_assets=len(df.columns),
            n_observations=len(df),
            date_range_start=df.index[0],
            date_range_end=df.index[-1],
            is_processed=True
        )
        
        db.add(dataset)
        await db.commit()
        
        # Audit log
        audit = AuditLog(
            user_id=current_user.id,
            action="upload_dataset",
            entity_type="dataset",
            entity_id=file_id,
            details={"filename": file.filename, "n_assets": len(df.columns)}
        )
        db.add(audit)
        await db.commit()
        
        return {
            "success": True,
            "dataset_id": file_id,
            "filename": file.filename,
            "assets": df.columns.tolist(),
            "observations": len(df),
            "preview": df.head(5).to_dict()
        }
        
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(500, str(e))


@app.get("/api/datasets")
async def list_datasets(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List user's datasets."""
    result = await db.execute(
        select(Dataset)
        .where(Dataset.user_id == current_user.id)
        .order_by(desc(Dataset.created_at))
    )
    datasets = result.scalars().all()
    
    return [
        {
            "id": d.id,
            "filename": d.filename,
            "n_assets": d.n_assets,
            "n_observations": d.n_observations,
            "created_at": d.created_at,
            "asset_classes": d.asset_classes
        }
        for d in datasets
    ]


@app.get("/api/datasets/{dataset_id}")
async def get_dataset(
    dataset_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get dataset details."""
    result = await db.execute(
        select(Dataset).where(
            Dataset.id == dataset_id,
            Dataset.user_id == current_user.id
        )
    )
    dataset = result.scalar_one_or_none()
    
    if not dataset:
        raise HTTPException(404, "Dataset not found")
    
    return {
        "id": dataset.id,
        "filename": dataset.filename,
        "assets": dataset.assets,
        "n_assets": dataset.n_assets,
        "n_observations": dataset.n_observations,
        "date_range": [dataset.date_range_start, dataset.date_range_end],
        "created_at": dataset.created_at
    }


# ============================================================================
# ANALYSIS ENDPOINTS
# ============================================================================

@app.post("/api/analyses")
async def create_analysis(
    dataset_id: str,
    name: str,
    analysis_type: str = "full",
    regime: str = "basel_iii",
    confidence_level: float = 0.99,
    time_horizon: int = 1,
    var_method: str = "historical",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create and run a new analysis."""
    try:
        # Get dataset
        result = await db.execute(
            select(Dataset).where(
                Dataset.id == dataset_id,
                Dataset.user_id == current_user.id
            )
        )
        dataset = result.scalar_one_or_none()
        
        if not dataset:
            raise HTTPException(404, "Dataset not found")
        
        # Load data
        if dataset.file_path.endswith('.csv'):
            df = pd.read_csv(dataset.file_path, index_col=0, parse_dates=True)
        else:
            df = pd.read_excel(dataset.file_path, index_col=0, parse_dates=True)
        
        # Create analysis record
        analysis_id = generate_uuid()
        analysis = Analysis(
            id=analysis_id,
            user_id=current_user.id,
            dataset_id=dataset_id,
            name=name,
            analysis_type=analysis_type,
            regime=regime,
            confidence_level=confidence_level,
            time_horizon=time_horizon,
            var_method=var_method,
            status="running",
            started_at=datetime.now()
        )
        db.add(analysis)
        await db.commit()
        
        # Run analysis
        start_time = datetime.now()
        
        # Basic risk analyzer
        basic_analyzer = StatisticalRiskAnalyzer(df)
        
        # Advanced risk analyzer
        advanced_analyzer = AdvancedRiskAnalyzer(df)
        
        results = {}
        
        # Statistical moments
        if analysis_type in ["full", "moments"]:
            results['statistical_moments'] = {}
            for asset in basic_analyzer.assets:
                results['statistical_moments'][asset] = basic_analyzer.calculate_moments(asset).to_dict()
            results['statistical_moments']['portfolio'] = basic_analyzer.calculate_moments(None).to_dict()
        
        # Correlation
        if analysis_type in ["full", "correlation"]:
            results['correlation_matrix'] = basic_analyzer.calculate_correlation_matrix().to_dict()
            results['covariance_matrix'] = basic_analyzer.calculate_covariance_matrix().to_dict()
        
        # VaR
        if analysis_type in ["full", "var"]:
            results['var_analysis'] = {}
            for method in VaRMethod:
                try:
                    var_result = basic_analyzer.calculate_var(
                        confidence_level=confidence_level,
                        time_horizon=time_horizon,
                        method=method
                    )
                    results['var_analysis'][method.value] = var_result.to_dict()
                except Exception as e:
                    results['var_analysis'][method.value] = {'error': str(e)}
        
        # Expected Shortfall (FRTB)
        if analysis_type in ["full", "expected_shortfall"]:
            es_result = advanced_analyzer.calculate_expected_shortfall(
                confidence_level=0.975,  # FRTB standard
                time_horizon=10
            )
            results['expected_shortfall'] = es_result.to_dict()
        
        # GARCH
        if analysis_type in ["full", "garch"]:
            garch_result = advanced_analyzer.fit_garch(forecast_horizon=10)
            if garch_result:
                results['garch'] = garch_result.to_dict()
        
        # PCA
        if analysis_type in ["full", "pca"]:
            pca_result = basic_analyzer.perform_pca()
            results['pca_analysis'] = pca_result.to_dict()
        
        # Portfolio metrics
        if analysis_type == "full":
            metrics = advanced_analyzer.calculate_portfolio_metrics()
            results['portfolio_metrics'] = metrics.to_dict()
        
        # Clustering
        if analysis_type in ["full", "clustering"]:
            cluster_result = basic_analyzer.clustering_analysis()
            results['cluster_analysis'] = cluster_result
        
        # Optimization
        if analysis_type in ["full", "optimization"]:
            opt_result = advanced_analyzer.optimize_portfolio()
            results['optimization'] = opt_result
        
        # Calculate duration
        duration = (datetime.now() - start_time).total_seconds()
        
        # Update analysis record
        analysis.status = "completed"
        analysis.results = results
        analysis.summary_metrics = {
            "portfolio_var_99": results.get('var_analysis', {}).get('historical', {}).get('var_99'),
            "portfolio_volatility": results.get('statistical_moments', {}).get('portfolio', {}).get('std_dev'),
            "sharpe_ratio": results.get('portfolio_metrics', {}).get('sharpe_ratio')
        }
        analysis.completed_at = datetime.now()
        analysis.duration_seconds = duration
        await db.commit()
        
        return {
            "success": True,
            "analysis_id": analysis_id,
            "status": "completed",
            "duration_seconds": duration,
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        # Update status to failed
        if 'analysis' in locals():
            analysis.status = "failed"
            analysis.error_message = str(e)
            await db.commit()
        raise HTTPException(500, str(e))


@app.get("/api/analyses")
async def list_analyses(
    dataset_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List user's analyses."""
    query = select(Analysis).where(Analysis.user_id == current_user.id)
    
    if dataset_id:
        query = query.where(Analysis.dataset_id == dataset_id)
    
    query = query.order_by(desc(Analysis.created_at))
    result = await db.execute(query)
    analyses = result.scalars().all()
    
    return [
        {
            "id": a.id,
            "name": a.name,
            "dataset_id": a.dataset_id,
            "analysis_type": a.analysis_type,
            "regime": a.regime,
            "status": a.status,
            "created_at": a.created_at,
            "duration_seconds": a.duration_seconds,
            "summary": a.summary_metrics
        }
        for a in analyses
    ]


@app.get("/api/analyses/{analysis_id}")
async def get_analysis(
    analysis_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get analysis results."""
    result = await db.execute(
        select(Analysis).where(
            Analysis.id == analysis_id,
            Analysis.user_id == current_user.id
        )
    )
    analysis = result.scalar_one_or_none()
    
    if not analysis:
        raise HTTPException(404, "Analysis not found")
    
    return {
        "id": analysis.id,
        "name": analysis.name,
        "analysis_type": analysis.analysis_type,
        "regime": analysis.regime,
        "status": analysis.status,
        "results": analysis.results,
        "summary": analysis.summary_metrics,
        "created_at": analysis.created_at,
        "completed_at": analysis.completed_at
    }


# ============================================================================
# REPORT GENERATION ENDPOINTS
# ============================================================================

@app.post("/api/reports")
async def generate_report(
    analysis_id: str,
    report_type: str = "excel",
    regime: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate a report from analysis."""
    try:
        # Get analysis
        result = await db.execute(
            select(Analysis).where(
                Analysis.id == analysis_id,
                Analysis.user_id == current_user.id
            )
        )
        analysis = result.scalar_one_or_none()
        
        if not analysis:
            raise HTTPException(404, "Analysis not found")
        
        if analysis.status != "completed":
            raise HTTPException(400, "Analysis not completed yet")
        
        regime = regime or analysis.regime or "basel_iii"
        
        # Generate report
        report_id = generate_uuid()
        
        if report_type == "excel":
            report_gen = ReportGenerator(analysis.results, regime=regime)
            file_path = os.path.join(settings.REPORT_DIR, f"report_{report_id}.xlsx")
            report_gen.generate_excel_report(file_path)
        elif report_type == "pdf":
            pdf_gen = PDFReportGenerator(analysis.results, regime=regime)
            file_path = os.path.join(settings.REPORT_DIR, f"report_{report_id}.pdf")
            pdf_gen.generate_pdf_report(file_path)
        else:
            raise HTTPException(400, "Unsupported report type")
        
        # Save report record
        report = Report(
            id=report_id,
            user_id=current_user.id,
            analysis_id=analysis_id,
            report_type=report_type,
            regime=regime,
            file_path=file_path,
            file_size=os.path.getsize(file_path),
            is_generated=True,
            summary=analysis.summary_metrics
        )
        db.add(report)
        await db.commit()
        
        return {
            "success": True,
            "report_id": report_id,
            "report_type": report_type,
            "file_size": os.path.getsize(file_path),
            "download_url": f"/api/reports/{report_id}/download"
        }
        
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        raise HTTPException(500, str(e))


@app.get("/api/reports/{report_id}/download")
async def download_report(
    report_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Download a generated report."""
    result = await db.execute(
        select(Report).where(
            Report.id == report_id,
            Report.user_id == current_user.id
        )
    )
    report = result.scalar_one_or_none()
    
    if not report:
        raise HTTPException(404, "Report not found")
    
    if not os.path.exists(report.file_path):
        raise HTTPException(404, "Report file not found")
    
    # Update download stats
    report.download_count += 1
    report.last_downloaded_at = datetime.now()
    await db.commit()
    
    media_type = {
        "excel": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "pdf": "application/pdf"
    }.get(report.report_type, "application/octet-stream")
    
    return FileResponse(
        report.file_path,
        media_type=media_type,
        filename=f"risk_report_{report_id}.{report.report_type}"
    )


# ============================================================================
# SAMPLE DATA ENDPOINTS
# ============================================================================

@app.post("/api/sample-data")
async def generate_sample_data(
    n_years: int = 5,
    asset_classes: List[str] = None,
    include_stress: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate sample financial data."""
    try:
        if asset_classes is None:
            asset_classes = ['equities', 'bonds', 'commodities', 'fx']
        
        file_id = generate_uuid()
        
        generator = FinancialDataGenerator(seed=42)
        returns = generator.generate_returns(
            n_observations=252 * n_years,
            asset_classes=asset_classes,
            start_date='2019-01-01',
            include_stress_periods=include_stress
        )
        prices = generator.generate_market_data(returns)
        
        # Save files
        returns_path = os.path.join(settings.DATA_DIR, f"sample_returns_{file_id}.csv")
        prices_path = os.path.join(settings.DATA_DIR, f"sample_prices_{file_id}.csv")
        
        returns.to_csv(returns_path)
        prices.to_csv(prices_path)
        
        # Create dataset record
        dataset = Dataset(
            id=file_id,
            user_id=current_user.id,
            filename=f"sample_data_{file_id}.csv",
            original_filename=f"sample_data_{n_years}years.csv",
            file_path=returns_path,
            file_size=os.path.getsize(returns_path),
            file_type="csv",
            asset_classes=asset_classes,
            assets=returns.columns.tolist(),
            n_assets=len(returns.columns),
            n_observations=len(returns),
            date_range_start=returns.index[0],
            date_range_end=returns.index[-1],
            is_processed=True
        )
        db.add(dataset)
        await db.commit()
        
        return {
            "success": True,
            "dataset_id": file_id,
            "message": f"Generated {n_years} years of sample data",
            "assets": returns.columns.tolist(),
            "observations": len(returns),
            "asset_classes": asset_classes
        }
        
    except Exception as e:
        logger.error(f"Sample data generation failed: {e}")
        raise HTTPException(500, str(e))


# ============================================================================
# UTILITY ENDPOINTS
# ============================================================================

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/regulatory-regimes")
async def get_regulatory_regimes():
    """Get supported regulatory regimes."""
    return {
        "regimes": [
            {"id": "basel_iii", "name": "Basel III", "var_confidence": 0.99, "horizon": 10},
            {"id": "frtb", "name": "FRTB", "es_confidence": 0.975, "horizon": 10},
            {"id": "ucits", "name": "UCITS", "var_confidence": 0.99, "horizon": 20},
            {"id": "emir", "name": "EMIR", "var_confidence": 0.99, "horizon": 1},
            {"id": "mifid_ii", "name": "MiFID II", "var_confidence": 0.95, "horizon": 1},
        ]
    }


@app.get("/api/methods")
async def get_analysis_methods():
    """Get available analysis methods."""
    return {
        "var_methods": ["historical", "parametric", "monte_carlo", "cornish_fisher"],
        "analysis_types": [
            "full", "moments", "correlation", "var", "pca", 
            "garch", "expected_shortfall", "optimization", "clustering"
        ],
        "report_types": ["excel", "pdf"]
    }


# ============================================================================
# WEBSOCKET ENDPOINTS
# ============================================================================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time updates."""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            if message.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
            elif message.get("type") == "subscribe_analysis":
                # Subscribe to analysis updates
                analysis_id = message.get("analysis_id")
                await websocket.send_json({
                    "type": "subscribed",
                    "analysis_id": analysis_id
                })
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# ============================================================================
# STATIC FILES
# ============================================================================

# Mount static files for frontend (if serving from backend)
if os.path.exists("../frontend/dist"):
    app.mount("/", StaticFiles(directory="../frontend/dist", html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        workers=settings.WORKERS if not settings.DEBUG else 1
    )
