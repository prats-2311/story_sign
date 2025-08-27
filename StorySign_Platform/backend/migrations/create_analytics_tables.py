"""
Analytics Tables Migration
Creates tables for analytics event collection, user consent, and data anonymization
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import Column, String, Text, Boolean, DateTime, JSON, Integer, Float, Index
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.sql import func
from models.base import BaseModel, TimestampMixin
import uuid


class AnalyticsEvent(BaseModel, TimestampMixin):
    """Analytics event model for tracking user interactions and learning patterns"""
    __tablename__ = "analytics_events"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(CHAR(36), nullable=True, index=True)  # Nullable for anonymous events
    session_id = Column(String(255), nullable=False, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    module_name = Column(String(50), nullable=False, index=True)
    event_data = Column(JSON, nullable=False)
    occurred_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), index=True)
    
    # Privacy and consent tracking
    is_anonymous = Column(Boolean, default=False, index=True)
    consent_version = Column(String(20), nullable=True)
    
    # Performance metrics
    processing_time_ms = Column(Float, nullable=True)
    
    # Data retention
    expires_at = Column(DateTime(timezone=True), nullable=True, index=True)

    __table_args__ = (
        Index('idx_analytics_user_time', 'user_id', 'occurred_at'),
        Index('idx_analytics_module_type', 'module_name', 'event_type'),
        Index('idx_analytics_session_time', 'session_id', 'occurred_at'),
        Index('idx_analytics_anonymous', 'is_anonymous', 'occurred_at'),
    )


class UserConsent(BaseModel, TimestampMixin):
    """User consent management for analytics and research data collection"""
    __tablename__ = "user_consent"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(CHAR(36), nullable=False, index=True)
    consent_type = Column(String(50), nullable=False)  # 'analytics', 'research', 'marketing'
    consent_given = Column(Boolean, nullable=False)
    consent_version = Column(String(20), nullable=False)
    consent_text = Column(Text, nullable=True)
    granted_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    
    __table_args__ = (
        Index('idx_consent_user_type', 'user_id', 'consent_type'),
        Index('idx_consent_active', 'user_id', 'consent_given', 'revoked_at'),
    )


class AnalyticsAggregation(BaseModel, TimestampMixin):
    """Pre-computed analytics aggregations for performance"""
    __tablename__ = "analytics_aggregations"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    aggregation_type = Column(String(100), nullable=False, index=True)
    time_period = Column(String(20), nullable=False)  # 'hourly', 'daily', 'weekly', 'monthly'
    period_start = Column(DateTime(timezone=True), nullable=False, index=True)
    period_end = Column(DateTime(timezone=True), nullable=False)
    
    # Aggregated metrics
    total_events = Column(Integer, default=0)
    unique_users = Column(Integer, default=0)
    unique_sessions = Column(Integer, default=0)
    
    # Module-specific metrics
    module_name = Column(String(50), nullable=True, index=True)
    aggregated_data = Column(JSON, nullable=False)
    
    # Privacy compliance
    includes_anonymous = Column(Boolean, default=True)
    
    __table_args__ = (
        Index('idx_aggregation_type_period', 'aggregation_type', 'time_period', 'period_start'),
        Index('idx_aggregation_module', 'module_name', 'period_start'),
    )


class DataRetentionPolicy(BaseModel, TimestampMixin):
    """Data retention policies for different types of analytics data"""
    __tablename__ = "data_retention_policies"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    policy_name = Column(String(100), nullable=False, unique=True)
    data_type = Column(String(50), nullable=False)  # 'analytics_events', 'user_data', 'research_data'
    retention_days = Column(Integer, nullable=False)
    anonymize_after_days = Column(Integer, nullable=True)
    
    # Policy configuration
    policy_config = Column(JSON, nullable=False)
    is_active = Column(Boolean, default=True)
    
    # Compliance requirements
    compliance_framework = Column(String(50), nullable=True)  # 'GDPR', 'COPPA', 'FERPA'


# Migration functions
def create_analytics_tables(engine):
    """Create all analytics-related tables"""
    BaseModel.metadata.create_all(engine, tables=[
        AnalyticsEvent.__table__,
        UserConsent.__table__,
        AnalyticsAggregation.__table__,
        DataRetentionPolicy.__table__,
    ])


def drop_analytics_tables(engine):
    """Drop all analytics-related tables"""
    BaseModel.metadata.drop_all(engine, tables=[
        DataRetentionPolicy.__table__,
        AnalyticsAggregation.__table__,
        UserConsent.__table__,
        AnalyticsEvent.__table__,
    ])


if __name__ == "__main__":
    print("Analytics tables migration ready")
    print("Run this migration through the main migration system")
    print("Tables defined:")
    print("- analytics_events")
    print("- user_consent") 
    print("- analytics_aggregations")
    print("- data_retention_policies")
    print("- analytics_sessions")