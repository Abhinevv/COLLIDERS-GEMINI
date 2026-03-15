"""
History Service for tracking collision analysis results over time
"""

from datetime import datetime, timedelta, timezone
from sqlalchemy import func, and_
from database.db_manager import get_db_manager
from database.models import AnalysisHistory, Satellite, DebrisObject
import logging
import csv
import io

logger = logging.getLogger(__name__)


class HistoryService:
    """Service for managing analysis history"""
    
    def __init__(self):
        self.db_manager = get_db_manager()
    
    def save_analysis(self, satellite_id, debris_id, probability, 
                     closest_distance_km=None, closest_approach_time=None,
                     duration_minutes=None, samples=None, visualization_url=None):
        """
        Save an analysis result to history
        
        Args:
            satellite_id: NORAD ID of satellite
            debris_id: ID of debris object
            probability: Collision probability
            closest_distance_km: Closest approach distance
            closest_approach_time: Time of closest approach
            duration_minutes: Analysis duration
            samples: Number of Monte Carlo samples
            visualization_url: URL to visualization
            
        Returns:
            Dictionary with analysis data
        """
        session = self.db_manager.get_session()
        try:
            # Determine risk level
            risk_level = self._calculate_risk_level(probability)
            
            analysis = AnalysisHistory(
                satellite_id=str(satellite_id),
                debris_id=str(debris_id),
                analysis_time=datetime.now(timezone.utc),
                probability=probability,
                closest_distance_km=closest_distance_km,
                closest_approach_time=closest_approach_time,
                duration_minutes=duration_minutes,
                samples=samples,
                visualization_url=visualization_url,
                risk_level=risk_level
            )
            
            session.add(analysis)
            session.commit()
            
            # Convert to dict before closing session
            result = analysis.to_dict()
            
            logger.info(f"Saved analysis: {satellite_id} vs {debris_id}, P={probability:.6f}")
            return result
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error saving analysis: {e}")
            raise
        finally:
            self.db_manager.close_session(session)
    
    def get_satellite_history(self, satellite_id, days=30, limit=100):
        """
        Get analysis history for a specific satellite
        
        Args:
            satellite_id: NORAD ID of satellite
            days: Number of days to look back
            limit: Maximum number of results
            
        Returns:
            List of AnalysisHistory objects
        """
        session = self.db_manager.get_session()
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            results = session.query(AnalysisHistory).filter(
                and_(
                    AnalysisHistory.satellite_id == str(satellite_id),
                    AnalysisHistory.analysis_time >= cutoff_date
                )
            ).order_by(
                AnalysisHistory.analysis_time.desc()
            ).limit(limit).all()
            
            return [r.to_dict() for r in results]
            
        finally:
            self.db_manager.close_session(session)
    
    def get_debris_history(self, debris_id, days=30, limit=100):
        """
        Get analysis history for a specific debris object
        
        Args:
            debris_id: ID of debris object
            days: Number of days to look back
            limit: Maximum number of results
            
        Returns:
            List of AnalysisHistory objects
        """
        session = self.db_manager.get_session()
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            results = session.query(AnalysisHistory).filter(
                and_(
                    AnalysisHistory.debris_id == str(debris_id),
                    AnalysisHistory.analysis_time >= cutoff_date
                )
            ).order_by(
                AnalysisHistory.analysis_time.desc()
            ).limit(limit).all()
            
            return [r.to_dict() for r in results]
            
        finally:
            self.db_manager.close_session(session)
    
    def get_trend_data(self, satellite_id, debris_id, days=30):
        """
        Get probability trend for a specific satellite-debris pair
        
        Args:
            satellite_id: NORAD ID of satellite
            debris_id: ID of debris object
            days: Number of days to look back
            
        Returns:
            List of {time, probability} dicts
        """
        session = self.db_manager.get_session()
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            results = session.query(
                AnalysisHistory.analysis_time,
                AnalysisHistory.probability
            ).filter(
                and_(
                    AnalysisHistory.satellite_id == str(satellite_id),
                    AnalysisHistory.debris_id == str(debris_id),
                    AnalysisHistory.analysis_time >= cutoff_date
                )
            ).order_by(
                AnalysisHistory.analysis_time.asc()
            ).all()
            
            return [
                {
                    'time': r.analysis_time.isoformat(),
                    'probability': r.probability
                }
                for r in results
            ]
            
        finally:
            self.db_manager.close_session(session)
    
    def get_statistics(self, days=30):
        """
        Get overall statistics
        
        Args:
            days: Number of days to look back
            
        Returns:
            Dictionary with statistics
        """
        session = self.db_manager.get_session()
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            # Total analyses
            total_analyses = session.query(func.count(AnalysisHistory.id)).filter(
                AnalysisHistory.analysis_time >= cutoff_date
            ).scalar()
            
            # Analyses by risk level
            risk_counts = session.query(
                AnalysisHistory.risk_level,
                func.count(AnalysisHistory.id)
            ).filter(
                AnalysisHistory.analysis_time >= cutoff_date
            ).group_by(
                AnalysisHistory.risk_level
            ).all()
            
            # Average probability
            avg_probability = session.query(
                func.avg(AnalysisHistory.probability)
            ).filter(
                AnalysisHistory.analysis_time >= cutoff_date
            ).scalar() or 0
            
            # Highest risk analysis
            highest_risk = session.query(AnalysisHistory).filter(
                AnalysisHistory.analysis_time >= cutoff_date
            ).order_by(
                AnalysisHistory.probability.desc()
            ).first()
            
            return {
                'total_analyses': total_analyses,
                'risk_distribution': {level: count for level, count in risk_counts},
                'average_probability': float(avg_probability),
                'highest_risk': highest_risk.to_dict() if highest_risk else None,
                'period_days': days
            }
            
        finally:
            self.db_manager.close_session(session)
    
    def export_to_csv(self, satellite_id=None, debris_id=None, days=30):
        """
        Export history to CSV format
        
        Args:
            satellite_id: Optional satellite filter
            debris_id: Optional debris filter
            days: Number of days to look back
            
        Returns:
            CSV string
        """
        session = self.db_manager.get_session()
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            query = session.query(AnalysisHistory).filter(
                AnalysisHistory.analysis_time >= cutoff_date
            )
            
            if satellite_id:
                query = query.filter(AnalysisHistory.satellite_id == str(satellite_id))
            if debris_id:
                query = query.filter(AnalysisHistory.debris_id == str(debris_id))
            
            results = query.order_by(AnalysisHistory.analysis_time.desc()).all()
            
            # Create CSV
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Header
            writer.writerow([
                'Analysis Time', 'Satellite ID', 'Debris ID', 'Probability',
                'Closest Distance (km)', 'Closest Approach Time', 'Risk Level',
                'Duration (min)', 'Samples'
            ])
            
            # Data
            for r in results:
                writer.writerow([
                    r.analysis_time.isoformat() if r.analysis_time else '',
                    r.satellite_id,
                    r.debris_id,
                    r.probability,
                    r.closest_distance_km or '',
                    r.closest_approach_time.isoformat() if r.closest_approach_time else '',
                    r.risk_level,
                    r.duration_minutes or '',
                    r.samples or ''
                ])
            
            return output.getvalue()
            
        finally:
            self.db_manager.close_session(session)
    
    def _calculate_risk_level(self, probability):
        """Calculate risk level from probability"""
        if probability == 0:
            return 'SAFE'
        elif probability < 0.001:
            return 'LOW'
        elif probability < 0.01:
            return 'MODERATE'
        elif probability < 0.1:
            return 'HIGH'
        else:
            return 'CRITICAL'
