"""
Audit Middleware for automatic change tracking
"""
from functools import wraps
from datetime import datetime
from typing import Optional, Dict, Any
from fastapi import Request
from sqlalchemy.orm import Session

from models.audit import AuditLog
from models import Usuario


class AuditLogger:
    """Utility class for audit logging"""
    
    @staticmethod
    def get_client_ip(request: Request) -> str:
        """Extract client IP from request"""
        if "x-forwarded-for" in request.headers:
            return request.headers["x-forwarded-for"].split(",")[0]
        return request.client.host if request.client else "unknown"
    
    @staticmethod
    def get_user_agent(request: Request) -> str:
        """Extract user agent from request"""
        return request.headers.get("user-agent", "unknown")
    
    @staticmethod
    async def log(
        db: Session,
        action: str,
        user: Optional[Usuario] = None,
        table_name: Optional[str] = None,
        record_id: Optional[int] = None,
        old_value: Optional[Dict[str, Any]] = None,
        new_value: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None,
        description: Optional[str] = None,
        status: str = "SUCCESS"
    ):
        """Create audit log entry"""
        log_entry = AuditLog(
            timestamp=datetime.utcnow(),
            user_id=user.id if user else None,
            username=user.username if user else "system",
            action=action,
            table_name=table_name,
            record_id=record_id,
            old_value=old_value,
            new_value=new_value,
            ip_address=AuditLogger.get_client_ip(request) if request else None,
            user_agent=AuditLogger.get_user_agent(request) if request else None,
            endpoint=str(request.url.path) if request else None,
            description=description,
            status=status
        )
        
        db.add(log_entry)
        db.commit()
        return log_entry


def audit_action(action: str, table: str, get_record_id=None):
    """
    Decorator for automatic audit logging
    
    Usage:
        @audit_action("CREATE", "produtos")
        async def create_product(...):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Execute the function
            result = await func(*args, **kwargs)
            
            # Try to extract common parameters
            db = kwargs.get('db')
            current_user = kwargs.get('current_user')
            request = kwargs.get('request')
            
            if db and current_user:
                try:
                    record_id = get_record_id(result) if get_record_id else None
                    
                    await AuditLogger.log(
                        db=db,
                        action=action,
                        user=current_user,
                        table_name=table,
                        record_id=record_id,
                        new_value=result.dict() if hasattr(result, 'dict') else None,
                        request=request
                    )
                except Exception as e:
                    # Don't fail the request if audit logging fails
                    print(f"Audit logging failed: {e}")
            
            return result
        return wrapper
    return decorator
