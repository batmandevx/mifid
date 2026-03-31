"""
Database Models
===============
SQLAlchemy models for persistence.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, JSON, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, Dict, Any
import uuid

from core.database import Base


def generate_uuid() -> str:
    """Generate a unique identifier."""
    return str(uuid.uuid4())


class User(Base):
    """User model for authentication."""
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    last_login = Column(DateTime)
    
    # Relationships
    datasets = relationship("Dataset", back_populates="user", cascade="all, delete-orphan")
    analyses = relationship("Analysis", back_populates="user", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="user", cascade="all, delete-orphan")


class Dataset(Base):
    """Uploaded dataset model."""
    __tablename__ = "datasets"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer)
    file_type = Column(String(50))  # csv, xlsx, etc.
    
    # Data metadata
    asset_classes = Column(JSON)  # ['equities', 'bonds', etc.]
    assets = Column(JSON)  # List of asset names
    n_assets = Column(Integer)
    n_observations = Column(Integer)
    date_range_start = Column(DateTime)
    date_range_end = Column(DateTime)
    
    # Status
    is_processed = Column(Boolean, default=False)
    processing_error = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="datasets")
    analyses = relationship("Analysis", back_populates="dataset", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_dataset_user', 'user_id'),
        Index('idx_dataset_created', 'created_at'),
    )


class Analysis(Base):
    """Risk analysis model."""
    __tablename__ = "analyses"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    dataset_id = Column(String(36), ForeignKey("datasets.id"), nullable=False)
    
    # Analysis configuration
    name = Column(String(255))
    description = Column(Text)
    analysis_type = Column(String(50))  # full, var, pca, correlation, etc.
    
    # Parameters
    regime = Column(String(50))  # basel_iii, frtb, etc.
    confidence_level = Column(Float)
    time_horizon = Column(Integer)
    var_method = Column(String(50))
    portfolio_weights = Column(JSON)
    
    # Results storage
    results = Column(JSON)  # Store full results as JSON
    summary_metrics = Column(JSON)  # Key metrics for quick access
    
    # Status
    status = Column(String(50), default="pending")  # pending, running, completed, failed
    error_message = Column(Text)
    
    # Performance metrics
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    duration_seconds = Column(Float)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="analyses")
    dataset = relationship("Dataset", back_populates="analyses")
    reports = relationship("Report", back_populates="analysis", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_analysis_user', 'user_id'),
        Index('idx_analysis_dataset', 'dataset_id'),
        Index('idx_analysis_status', 'status'),
        Index('idx_analysis_created', 'created_at'),
    )


class Report(Base):
    """Generated report model."""
    __tablename__ = "reports"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    analysis_id = Column(String(36), ForeignKey("analyses.id"), nullable=False)
    
    # Report metadata
    report_type = Column(String(50))  # excel, pdf, html
    regime = Column(String(50))
    file_path = Column(String(500))
    file_size = Column(Integer)
    
    # Content summary
    summary = Column(JSON)
    key_findings = Column(JSON)
    regulatory_flags = Column(JSON)
    
    # Status
    is_generated = Column(Boolean, default=False)
    generation_error = Column(Text)
    
    # Download tracking
    download_count = Column(Integer, default=0)
    last_downloaded_at = Column(DateTime)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="reports")
    analysis = relationship("Analysis", back_populates="reports")
    
    # Indexes
    __table_args__ = (
        Index('idx_report_user', 'user_id'),
        Index('idx_report_analysis', 'analysis_id'),
        Index('idx_report_created', 'created_at'),
    )


class RiskLimit(Base):
    """Risk limit configuration and breaches."""
    __tablename__ = "risk_limits"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    
    # Limit configuration
    name = Column(String(255), nullable=False)
    limit_type = Column(String(50))  # var_limit, exposure_limit, concentration_limit
    metric = Column(String(100))  # var_99, portfolio_weight, etc.
    threshold = Column(Float)
    warning_level = Column(Float)  # e.g., 80% of threshold
    
    # Scope
    assets = Column(JSON)  # Apply to specific assets or all
    asset_classes = Column(JSON)
    
    # Breach tracking
    is_active = Column(Boolean, default=True)
    last_breach_at = Column(DateTime)
    breach_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class AuditLog(Base):
    """Audit log for compliance."""
    __tablename__ = "audit_logs"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"))
    
    action = Column(String(100), nullable=False)  # upload, analyze, generate_report, etc.
    entity_type = Column(String(50))  # dataset, analysis, report
    entity_id = Column(String(36))
    
    details = Column(JSON)
    ip_address = Column(String(50))
    user_agent = Column(String(500))
    
    created_at = Column(DateTime, default=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_audit_user', 'user_id'),
        Index('idx_audit_action', 'action'),
        Index('idx_audit_created', 'created_at'),
    )


class MarketData(Base):
    """Cached market data."""
    __tablename__ = "market_data"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    symbol = Column(String(50), nullable=False, index=True)
    asset_class = Column(String(50))
    
    data = Column(JSON)  # OHLCV data
    frequency = Column(String(20))  # daily, hourly, etc.
    date_range_start = Column(DateTime)
    date_range_end = Column(DateTime)
    
    source = Column(String(100))  # bloomberg, yahoo, etc.
    last_updated = Column(DateTime, default=func.now())
    
    created_at = Column(DateTime, default=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_market_symbol', 'symbol'),
        Index('idx_market_class', 'asset_class'),
    )
