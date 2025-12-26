"""
Audit Log Router
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta

from database import get_db
from models import Usuario
from models.audit import AuditLog
from routers.auth import require_admin
from utils.pagination import paginate, PaginatedResponse


router = APIRouter(prefix="/audit", tags=["Auditoria"])


@router.get("/logs", response_model=PaginatedResponse)
async def get_audit_logs(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    action: Optional[str] = None,
    table_name: Optional[str] = None,
    username: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """
    Get audit logs with filtering and pagination
    Requires admin role
    """
    query = db.query(AuditLog)
    
    # Apply filters
    if action:
        query = query.filter(AuditLog.action == action)
    
    if table_name:
        query = query.filter(AuditLog.table_name == table_name)
    
    if username:
        query = query.filter(AuditLog.username.ilike(f"%{username}%"))
    
    if start_date:
        query = query.filter(AuditLog.timestamp >= start_date)
    
    if end_date:
        query = query.filter(AuditLog.timestamp <= end_date)
    
    # Order by most recent first
    query = query.order_by(AuditLog.timestamp.desc())
    
    # Paginate results
    return paginate(query, page, limit)


@router.get("/stats")
async def get_audit_stats(
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """
    Get audit statistics for the last N days
    """
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Total actions
    total_actions = db.query(AuditLog).filter(
        AuditLog.timestamp >= start_date
    ).count()
    
    # Actions by type
    actions_by_type = db.query(
        AuditLog.action,
        db.func.count(AuditLog.id)
    ).filter(
        AuditLog.timestamp >= start_date
    ).group_by(AuditLog.action).all()
    
    # Most active users
    most_active_users = db.query(
        AuditLog.username,
        db.func.count(AuditLog.id).label('count')
    ).filter(
        AuditLog.timestamp >= start_date,
        AuditLog.username.isnot(None)
    ).group_by(AuditLog.username).order_by(
        db.func.count(AuditLog.id).desc()
    ).limit(10).all()
    
    # Most modified tables
    most_modified_tables = db.query(
        AuditLog.table_name,
        db.func.count(AuditLog.id).label('count')
    ).filter(
        AuditLog.timestamp >= start_date,
        AuditLog.table_name.isnot(None)
    ).group_by(AuditLog.table_name).order_by(
        db.func.count(AuditLog.id).desc()
    ).limit(10).all()
    
    return {
        "period_days": days,
        "start_date": start_date,
        "total_actions": total_actions,
        "actions_by_type": {action: count for action, count in actions_by_type},
        "most_active_users": [
            {"username": username, "actions": count}
            for username, count in most_active_users
        ],
        "most_modified_tables": [
            {"table": table, "modifications": count}
            for table, count in most_modified_tables
        ]
    }


@router.get("/logs/{log_id}")
async def get_audit_log_detail(
    log_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """Get detailed information about a specific audit log entry"""
    log = db.query(AuditLog).filter(AuditLog.id == log_id).first()
    
    if not log:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Log de auditoria não encontrado"
        )
    
    return log
