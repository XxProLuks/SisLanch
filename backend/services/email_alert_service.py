"""
LANCH - Email Alert Service
Send monitoring alerts via email for critical events
"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


class EmailAlertService:
    """Service for sending email alerts"""
    
    def __init__(
        self,
        smtp_host: str = None,
        smtp_port: int = None,
        smtp_user: str = None,
        smtp_password: str = None,
        from_email: str = None,
        alert_recipients: List[str] = None
    ):
        """
        Initialize email alert service
        
        Args:
            smtp_host: SMTP server hostname
            smtp_port: SMTP server port  
            smtp_user: SMTP username
            smtp_password: SMTP password
            from_email: From email address
            alert_recipients: List of email addresses to send alerts to
        """
        # Load from environment if not provided
        self.smtp_host = smtp_host or os.getenv('SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = smtp_port or int(os.getenv('SMTP_PORT', '587'))
        self.smtp_user = smtp_user or os.getenv('SMTP_USER', '')
        self.smtp_password = smtp_password or os.getenv('SMTP_PASSWORD', '')
        self.from_email = from_email or os.getenv('ALERT_FROM_EMAIL', self.smtp_user)
        
        # Parse recipients from environment if not provided
        if alert_recipients is None:
            recipients_str = os.getenv('ALERT_RECIPIENTS', '')
            self.alert_recipients = [r.strip() for r in recipients_str.split(',') if r.strip()]
        else:
            self.alert_recipients = alert_recipients
        
        self.enabled = self._check_configuration()
    
    def _check_configuration(self) -> bool:
        """Check if email alerts are properly configured"""
        if not all([self.smtp_host, self.smtp_user, self.smtp_password]):
            logger.warning("Email alerts not configured - missing SMTP credentials")
            return False
        
        if not self.alert_recipients:
            logger.warning("Email alerts not configured - no recipients defined")
            return False
        
        return True
    
    def send_alert(
        self,
        subject: str,
        message: str,
        severity: str = "INFO",
        html: bool = False
    ) -> dict:
        """
        Send an alert email
        
        Args:
            subject: Email subject
            message: Email body
            severity: Alert severity (INFO, WARNING, ERROR, CRITICAL)
            html: Whether message is HTML
            
        Returns:
            dict with success status and details
        """
        if not self.enabled:
            logger.warning(f"Email alerts disabled - would have sent: {subject}")
            return {"success": False, "error": "Email alerts not configured"}
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"[LANCH - {severity}] {subject}"
            msg['From'] = self.from_email
            msg['To'] = ', '.join(self.alert_recipients)
            msg['Date'] = datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')
            
            # Add body
            if html:
                msg.attach(MIMEText(message, 'html'))
            else:
                msg.attach(MIMEText(message, 'plain'))
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Alert email sent: {subject}")
            return {
                "success": True,
                "subject": subject,
                "recipients": self.alert_recipients
            }
            
        except Exception as e:
            logger.error(f"Failed to send alert email: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def send_backup_failure_alert(self, error_message: str):
        """Send alert for backup failure"""
        subject = "Database Backup Failed"
        message = f"""
        Database backup has failed!
        
        Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        Error: {error_message}
        
        Please check the system logs and ensure backups are working correctly.
        """
        
        return self.send_alert(subject, message, severity="ERROR")
    
    def send_disk_space_alert(self, available_mb: float, threshold_mb: float):
        """Send alert for low disk space"""
        subject = "Low Disk Space Warning"
        message = f"""
        The system is running low on disk space!
        
        Available: {available_mb:.0f} MB
        Threshold: {threshold_mb:.0f} MB
        
        Please free up disk space or expand storage capacity.
        """
        
        return self.send_alert(subject, message, severity="WARNING")
    
    def send_database_error_alert(self, error_message: str):
        """Send alert for database errors"""
        subject = "Database Error Detected"
        message = f"""
        A database error has occurred!
        
        Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        Error: {error_message}
        
        This may indicate database corruption or connectivity issues.
        Please investigate immediately.
        """
        
        return self.send_alert(subject, message, severity="CRITICAL")
    
    def send_health_check_failure(self, failed_checks: List[str]):
        """Send alert for failed health checks"""
        subject = "Health Check Failure"
        checks_list = '\n'.join([f"  - {check}" for check in failed_checks])
        message = f"""
        System health check has failed!
        
        Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        
        Failed checks:
{checks_list}
        
        Please review the system status and logs.
        """
        
        return self.send_alert(subject, message, severity="WARNING")
    
    def send_api_down_alert(self):
        """Send alert when API is not responding"""
        subject = "API Not Responding"
        message = f"""
        The LANCH API is not responding to health checks!
        
        Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        
        The service may be down or experiencing critical errors.
        Please check the service status immediately.
        """
        
        return self.send_alert(subject, message, severity="CRITICAL")
    
    def send_test_alert(self):
        """Send a test alert to verify configuration"""
        subject = "Test Alert"
        message = """
        This is a test alert from the LANCH monitoring system.
        
        If you receive this email, email alerts are configured correctly.
        """
        
        return self.send_alert(subject, message, severity="INFO")


# Singleton instance
_email_service = None


def get_email_alert_service() -> EmailAlertService:
    """Get or create email alert service instance"""
    global _email_service
    
    if _email_service is None:
        _email_service = EmailAlertService()
    
    return _email_service
