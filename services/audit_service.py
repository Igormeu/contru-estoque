from datetime import datetime, timezone
from database import AuditLog

def log_action(db, user_id, user_name, action, entity_type, entity_id, description, before_data=None, after_data=None):
    """Registra uma operação crítica no log de auditoria imutável."""
    try:
        log = AuditLog(
            user_id=user_id,
            user_name=user_name or "Sistema",
            action=action.upper(),
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id is not None else None,
            description=description,
            before_data=before_data,
            after_data=after_data,
            created_at=datetime.now(timezone.utc)
        )
        db.add(log)
        db.flush()
        return log
    except Exception as e:
        print(f"Erro ao registrar auditoria: {e}")
        return None

def get_audit_logs(db, limit=100, action=None, entity_type=None):
    """Retorna o histórico cronológico decrescente de auditoria."""
    query = db.query(AuditLog)
    if action:
        query = query.filter(AuditLog.action == action.upper())
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)
    
    logs = query.order_by(AuditLog.created_at.desc()).limit(limit).all()
    return [log.to_dict() for log in logs]
