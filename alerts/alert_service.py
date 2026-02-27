"""
Alert Service for managing collision alerts
"""

from datetime import datetime, timedelta, timezone
from sqlalchemy import and_, or_
from database.db_manager import get_db_manager
from database.models import Alert, AlertSubscription
import logging

logger = logging.getLogger(__name__)


class AlertService:
    """Service for managing collision alerts"""
    
    def __init__(self):
        self.db_manager = get_db_manager()
    
    def create_alert(self, satellite_id, debris_id, probability, 
                    closest_approach_time=None, closest_distance_km=None,
                    analysis_id=None):
        """
        Create a new collision alert
        
        Args:
            satellite_id: NORAD ID of satellite
            debris_id: ID of debris object
            probability: Collision probability
            closest_approach_time: Time of closest approach
            closest_distance_km: Distance at closest approach
            analysis_id: Reference to analysis history
            
        Returns:
            Alert dictionary
        """
        session = self.db_manager.get_session()
        try:
            # Determine risk level
            risk_level = self._calculate_risk_level(probability)
            
            # Check if alert already exists for this pair
            existing = session.query(Alert).filter(
                and_(
                    Alert.satellite_id == str(satellite_id),
                    Alert.debris_id == str(debris_id),
                    Alert.status == 'active'
                )
            ).first()
            
            if existing:
                # Update existing alert
                existing.probability = probability
                existing.closest_approach_time = closest_approach_time
                existing.closest_distance_km = closest_distance_km
                existing.risk_level = risk_level
                existing.updated_at = datetime.now(timezone.utc)
                existing.analysis_id = analysis_id
                session.commit()
                
                logger.info(f"Updated alert {existing.id}: {satellite_id} vs {debris_id}")
                return existing.to_dict()
            
            # Create new alert
            alert = Alert(
                satellite_id=str(satellite_id),
                debris_id=str(debris_id),
                probability=probability,
                closest_approach_time=closest_approach_time,
                closest_distance_km=closest_distance_km,
                risk_level=risk_level,
                status='active',
                analysis_id=analysis_id
            )
            
            session.add(alert)
            session.commit()
            
            result = alert.to_dict()
            
            logger.info(f"Created alert {result['id']}: {satellite_id} vs {debris_id}, Risk: {risk_level}")
            
            # Send notifications if needed
            self._send_notifications(result)
            
            return result
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating alert: {e}")
            raise
        finally:
            self.db_manager.close_session(session)
    
    def get_active_alerts(self, satellite_id=None, min_risk_level=None):
        """
        Get all active alerts
        
        Args:
            satellite_id: Optional filter by satellite
            min_risk_level: Minimum risk level (LOW, MODERATE, HIGH, CRITICAL)
            
        Returns:
            List of alert dictionaries
        """
        session = self.db_manager.get_session()
        try:
            query = session.query(Alert).filter(Alert.status == 'active')
            
            if satellite_id:
                query = query.filter(Alert.satellite_id == str(satellite_id))
            
            if min_risk_level:
                risk_order = {'LOW': 1, 'MODERATE': 2, 'HIGH': 3, 'CRITICAL': 4}
                min_level = risk_order.get(min_risk_level, 0)
                risk_levels = [k for k, v in risk_order.items() if v >= min_level]
                query = query.filter(Alert.risk_level.in_(risk_levels))
            
            alerts = query.order_by(Alert.created_at.desc()).all()
            return [a.to_dict() for a in alerts]
            
        finally:
            self.db_manager.close_session(session)
    
    def get_alert(self, alert_id):
        """
        Get a specific alert
        
        Args:
            alert_id: Alert ID
            
        Returns:
            Alert dictionary or None
        """
        session = self.db_manager.get_session()
        try:
            alert = session.query(Alert).filter(Alert.id == alert_id).first()
            return alert.to_dict() if alert else None
        finally:
            self.db_manager.close_session(session)
    
    def dismiss_alert(self, alert_id, notes=None):
        """
        Dismiss an alert
        
        Args:
            alert_id: Alert ID
            notes: Optional notes about dismissal
            
        Returns:
            bool: Success status
        """
        session = self.db_manager.get_session()
        try:
            alert = session.query(Alert).filter(Alert.id == alert_id).first()
            
            if not alert:
                return False
            
            alert.status = 'dismissed'
            alert.dismissed_at = datetime.now(timezone.utc)
            if notes:
                alert.notes = notes
            
            session.commit()
            
            logger.info(f"Dismissed alert {alert_id}")
            return True
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error dismissing alert: {e}")
            raise
        finally:
            self.db_manager.close_session(session)
    
    def resolve_alert(self, alert_id, notes=None):
        """
        Mark an alert as resolved
        
        Args:
            alert_id: Alert ID
            notes: Optional notes about resolution
            
        Returns:
            bool: Success status
        """
        session = self.db_manager.get_session()
        try:
            alert = session.query(Alert).filter(Alert.id == alert_id).first()
            
            if not alert:
                return False
            
            alert.status = 'resolved'
            alert.updated_at = datetime.now(timezone.utc)
            if notes:
                alert.notes = notes
            
            session.commit()
            
            logger.info(f"Resolved alert {alert_id}")
            return True
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error resolving alert: {e}")
            raise
        finally:
            self.db_manager.close_session(session)
    
    def get_alert_history(self, days=30, limit=100):
        """
        Get alert history
        
        Args:
            days: Number of days to look back
            limit: Maximum number of results
            
        Returns:
            List of alert dictionaries
        """
        session = self.db_manager.get_session()
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            alerts = session.query(Alert).filter(
                Alert.created_at >= cutoff_date
            ).order_by(
                Alert.created_at.desc()
            ).limit(limit).all()
            
            return [a.to_dict() for a in alerts]
            
        finally:
            self.db_manager.close_session(session)
    
    def subscribe_to_alerts(self, email=None, phone=None, satellite_ids=None, min_probability=0.001):
        """
        Subscribe to alert notifications
        
        Args:
            email: Email address
            phone: Phone number
            satellite_ids: List of satellite IDs to monitor
            min_probability: Minimum probability to trigger alert
            
        Returns:
            Subscription dictionary
        """
        session = self.db_manager.get_session()
        try:
            subscription = AlertSubscription(
                email=email,
                phone=phone,
                satellite_ids=satellite_ids or [],
                min_probability=min_probability,
                enabled=True
            )
            
            session.add(subscription)
            session.commit()
            
            result = subscription.to_dict()
            
            logger.info(f"Created subscription {result['id']}")
            return result
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating subscription: {e}")
            raise
        finally:
            self.db_manager.close_session(session)
    
    def get_subscriptions(self):
        """Get all alert subscriptions"""
        session = self.db_manager.get_session()
        try:
            subscriptions = session.query(AlertSubscription).filter(
                AlertSubscription.enabled == True
            ).all()
            return [s.to_dict() for s in subscriptions]
        finally:
            self.db_manager.close_session(session)
    
    def _calculate_risk_level(self, probability):
        """Calculate risk level from probability"""
        if probability < 0.001:
            return 'LOW'
        elif probability < 0.01:
            return 'MODERATE'
        elif probability < 0.1:
            return 'HIGH'
        else:
            return 'CRITICAL'
    
    def _send_notifications(self, alert):
        """
        Send notifications for an alert
        
        Args:
            alert: Alert dictionary
        """
        # Get subscriptions that match this alert
        session = self.db_manager.get_session()
        try:
            subscriptions = session.query(AlertSubscription).filter(
                and_(
                    AlertSubscription.enabled == True,
                    AlertSubscription.min_probability <= alert['probability']
                )
            ).all()
            
            for sub in subscriptions:
                # Check if this satellite is in the subscription
                if not sub.satellite_ids or alert['satellite_id'] in sub.satellite_ids:
                    # Send email if configured
                    if sub.email:
                        self._send_email_notification(sub.email, alert)
                    
                    # Send SMS if configured
                    if sub.phone:
                        self._send_sms_notification(sub.phone, alert)
        
        finally:
            self.db_manager.close_session(session)
    
    def _send_email_notification(self, email, alert):
        """Send email notification (placeholder)"""
        # TODO: Implement email sending with SendGrid
        logger.info(f"Would send email to {email} for alert {alert['id']}")
    
    def _send_sms_notification(self, phone, alert):
        """Send SMS notification (placeholder)"""
        # TODO: Implement SMS sending with Twilio
        logger.info(f"Would send SMS to {phone} for alert {alert['id']}")
