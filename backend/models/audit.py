"""
Audit Log Model for LANCH System
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship

from database import Base


class AuditLog(Base):
    """Audit log for tracking all system changes"""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # User information
    user_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    username = Column(String, nullable=True)
    
    # Action details
    action = Column(String, nullable=False, index=True)  # CREATE, UPDATE, DELETE, LOGIN, LOGOUT
    table_name = Column(String, nullable=True, index=True)
    record_id = Column(Integer, nullable=True)
    
    # Change tracking
    old_value = Column(JSON, nullable=True)
    new_value = Column(JSON, nullable=True)
    
    # Request metadata
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    endpoint = Column(String, nullable=True)
    
    # Additional context
    description = Column(String, nullable=True)
    status = Column(String, nullable=True)  # SUCCESS, FAILED
    
    # Relationships
    user = relationship("Usuario", backref="audit_logs", foreign_keys=[user_id])

    def __repr__(self):
        return f"<AuditLog(id={self.id}, action={self.action}, user={self.username}, timestamp={self.timestamp})>"
