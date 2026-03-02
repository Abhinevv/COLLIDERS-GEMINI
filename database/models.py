"""
SQLAlchemy models for AstroCleanAI database
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class AnalysisHistory(Base):
    """Store historical collision analysis results"""
    __tablename__ = 'analysis_history'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    satellite_id = Column(String(50), nullable=False, index=True)
    debris_id = Column(String(50), nullable=False, index=True)
    analysis_time = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    probability = Column(Float, nullable=False)
    closest_distance_km = Column(Float)
    closest_approach_time = Column(DateTime)
    duration_minutes = Column(Integer)
    samples = Column(Integer)
    visualization_url = Column(String(500))
    risk_level = Column(String(20))  # SAFE, LOW, MODERATE, HIGH, CRITICAL
    
    def to_dict(self):
        return {
            'id': self.id,
            'satellite_id': self.satellite_id,
            'debris_id': self.debris_id,
            'analysis_time': self.analysis_time.isoformat() if self.analysis_time else None,
            'probability': self.probability,
            'closest_distance_km': self.closest_distance_km,
            'closest_approach_time': self.closest_approach_time.isoformat() if self.closest_approach_time else None,
            'duration_minutes': self.duration_minutes,
            'samples': self.samples,
            'visualization_url': self.visualization_url,
            'risk_level': self.risk_level
        }


class Satellite(Base):
    """Store tracked satellite information"""
    __tablename__ = 'satellites'
    
    norad_id = Column(String(50), primary_key=True)
    name = Column(String(200), nullable=False)
    type = Column(String(100))
    description = Column(Text)
    operator = Column(String(200))
    launch_date = Column(DateTime)
    added_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    active = Column(Boolean, default=True)
    tle_line1 = Column(String(200))
    tle_line2 = Column(String(200))
    tle_epoch = Column(DateTime)
    
    def to_dict(self):
        return {
            'norad_id': self.norad_id,
            'name': self.name,
            'type': self.type,
            'description': self.description,
            'operator': self.operator,
            'launch_date': self.launch_date.isoformat() if self.launch_date else None,
            'added_at': self.added_at.isoformat() if self.added_at else None,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'active': self.active,
            'tle_epoch': self.tle_epoch.isoformat() if self.tle_epoch else None
        }


class DebrisObject(Base):
    """Store debris object information"""
    __tablename__ = 'debris_objects'
    
    norad_id = Column(String(50), primary_key=True)
    name = Column(String(200))
    type = Column(String(100))  # DEBRIS, ROCKET BODY, PAYLOAD, etc.
    rcs_size = Column(String(20))  # SMALL, MEDIUM, LARGE
    country = Column(String(100))
    launch_date = Column(DateTime)
    decay_date = Column(DateTime)
    apogee_km = Column(Float)
    perigee_km = Column(Float)
    inclination_deg = Column(Float)
    period_minutes = Column(Float)
    tle_line1 = Column(String(200))  # TLE Line 1 for position calculations
    tle_line2 = Column(String(200))  # TLE Line 2 for position calculations
    tle_epoch = Column(DateTime)  # TLE epoch time
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'norad_id': self.norad_id,
            'name': self.name,
            'type': self.type,
            'rcs_size': self.rcs_size,
            'country': self.country,
            'launch_date': self.launch_date.isoformat() if self.launch_date else None,
            'decay_date': self.decay_date.isoformat() if self.decay_date else None,
            'apogee_km': self.apogee_km,
            'perigee_km': self.perigee_km,
            'inclination_deg': self.inclination_deg,
            'period_minutes': self.period_minutes,
            'tle_epoch': self.tle_epoch.isoformat() if self.tle_epoch else None,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }


class Alert(Base):
    """Store collision alerts"""
    __tablename__ = 'alerts'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    satellite_id = Column(String(50), nullable=False, index=True)
    debris_id = Column(String(50), nullable=False, index=True)
    probability = Column(Float, nullable=False)
    closest_approach_time = Column(DateTime, index=True)
    closest_distance_km = Column(Float)
    risk_level = Column(String(20), nullable=False)  # LOW, MODERATE, HIGH, CRITICAL
    status = Column(String(20), default='active', nullable=False)  # active, resolved, dismissed
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    dismissed_at = Column(DateTime)
    notes = Column(Text)
    analysis_id = Column(Integer)  # Reference to AnalysisHistory
    
    def to_dict(self):
        return {
            'id': self.id,
            'satellite_id': self.satellite_id,
            'debris_id': self.debris_id,
            'probability': self.probability,
            'closest_approach_time': self.closest_approach_time.isoformat() if self.closest_approach_time else None,
            'closest_distance_km': self.closest_distance_km,
            'risk_level': self.risk_level,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'dismissed_at': self.dismissed_at.isoformat() if self.dismissed_at else None,
            'notes': self.notes,
            'analysis_id': self.analysis_id
        }


class AlertSubscription(Base):
    """Store user alert subscriptions"""
    __tablename__ = 'alert_subscriptions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(200))
    phone = Column(String(50))
    satellite_ids = Column(JSON)  # List of satellite IDs to monitor
    min_probability = Column(Float, default=0.001)  # Minimum probability to trigger alert
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'phone': self.phone,
            'satellite_ids': self.satellite_ids,
            'min_probability': self.min_probability,
            'enabled': self.enabled,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
