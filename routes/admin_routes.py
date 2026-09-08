from flask import Blueprint, request, jsonify
from datetime import datetime, timezone
import time
from database import SessionLocal, User, Role, CompanySetting, Product, StockMovement, Inventory, AuditLog, PriceHistory
from services.audit_service import log_action

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

def get_db():
    return SessionLocal()

# ---------------------------------------------------------------------------
# GESTÃO DE USUÁRIOS
# ---------------------------------------------------------------------------
@admin_bp.route('/users', methods=['GET'])
def list_admin_users():
    db = get_db()
    try:
        users = db.query(User).order_by(User.name.asc()).all()
        return jsonify({'success': True, 'users': [u.to_dict() for u in users]})
    finally:
        db.close()

@admin_bp.route('/users', methods=['POST'])
def create_admin_user():
    db = get_db()
    try:
        body = request.get_json() or {}
        name = body.get('name', '').strip()
        email = body.get('email', '').strip().lower()
        password = body.get('password', '').strip()
        role_id = body.get('role_id')
        avatar = body.get('avatar') or 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=100&auto=format&fit=crop&q=80'

        if not name or not email or not password or not role_id:
            return jsonify({'success': False, 'error': 'Nome, e-mail, senha e perfil são campos obrigatórios.'}), 400

        existing = db.query(User).filter(User.email == email).first()
        if existing:
            return jsonify({'success': False, 'error': f'Já existe um usuário com o e-mail {email}.'}), 400

        user = User(
            name=name,
            email=email,
            role_id=int(role_id),
            avatar=avatar,
            is_active=True
        )
        user.set_password(password)
        db.add(user)
        db.flush()

        admin_user_id = body.get('admin_user_id')
        admin_user_name = body.get('admin_user_name', 'Administrador')

        log_action(
            db, user_id=admin_user_id, user_name=admin_user_name,
            action="CADASTRO_USUARIO", entity_type="User", entity_id=user.id,
            description=f"Novo colaborador cadastrado: {user.name} ({user.email}) com perfil {user.role.display_name if user.role else 'Perfil'}."
        )
        db.commit()

        return jsonify({'success': True, 'user': user.to_dict()}), 201
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        db.close()

@admin_bp.route('/users/<int:user_id>', methods=['PUT'])
def update_admin_user(user_id):
    db = get_db()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return jsonify({'success': False, 'error': 'Usuário não encontrado.'}), 404

        body = request.get_json() or {}
        before_data = user.to_dict()

        if 'name' in body and body['name']:
            user.name = body['name'].strip()
        if 'role_id' in body and body['role_id']:
            user.role_id = int(body['role_id'])
        if 'avatar' in body:
            user.avatar = body['avatar']
        if 'is_active' in body:
            user.is_active = bool(body['is_active'])

        admin_user_id = body.get('admin_user_id')
        admin_user_name = body.get('admin_user_name', 'Administrador')

        log_action(
            db, user_id=admin_user_id, user_name=admin_user_name,
            action="EDICAO_USUARIO", entity_type="User", entity_id=user.id,
            description=f"Dados do usuário {user.name} atualizados pelo administrador.",
            before_data=before_data, after_data=user.to_dict()
        )
        db.commit()

        return jsonify({'success': True, 'user': user.to_dict()})
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        db.close()

@admin_bp.route('/users/<int:user_id>/reset-password', methods=['POST'])
def reset_user_password(user_id):
    db = get_db()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return jsonify({'success': False, 'error': 'Usuário não encontrado.'}), 404

        body = request.get_json() or {}
        new_password = body.get('new_password', '').strip()

        if not new_password or len(new_password) < 6:
            return jsonify({'success': False, 'error': 'A nova senha deve possuir no mínimo 6 caracteres.'}), 400

        user.set_password(new_password)

        admin_user_id = body.get('admin_user_id')
        admin_user_name = body.get('admin_user_name', 'Administrador')

        log_action(
            db, user_id=admin_user_id, user_name=admin_user_name,
            action="REDEFINICAO_SENHA_ADMIN", entity_type="User", entity_id=user.id,
            description=f"Senha do usuário {user.name} foi redefinida pelo administrador."
        )
        db.commit()

        return jsonify({'success': True, 'message': f'Senha do usuário {user.name} redefinida com sucesso!'})
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        db.close()

@admin_bp.route('/users/<int:user_id>/toggle-status', methods=['POST'])
def toggle_user_status(user_id):
    db = get_db()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return jsonify({'success': False, 'error': 'Usuário não encontrado.'}), 404

        user.is_active = not user.is_active
        action_name = "DESBLOQUEIO_USUARIO" if user.is_active else "BLOQUEIO_USUARIO"

        body = request.get_json() or {}
        admin_user_id = body.get('admin_user_id')
        admin_user_name = body.get('admin_user_name', 'Administrador')

        log_action(
            db, user_id=admin_user_id, user_name=admin_user_name,
            action=action_name, entity_type="User", entity_id=user.id,
            description=f"Acesso do usuário {user.name} foi {'ativado' if user.is_active else 'bloqueado'} pelo administrador."
        )
        db.commit()

        return jsonify({'success': True, 'user': user.to_dict()})
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        db.close()

# ---------------------------------------------------------------------------
# PARÂMETROS DA EMPRESA & POLÍTICAS
# ---------------------------------------------------------------------------
@admin_bp.route('/settings', methods=['GET', 'PUT'])
def handle_settings():
    db = get_db()
    try:
        setting = db.query(CompanySetting).first()
        if not setting:
            setting = CompanySetting()
            db.add(setting)
            db.commit()

        if request.method == 'PUT':
            body = request.get_json() or {}
            before_state = setting.to_dict()

            if 'company_name' in body: setting.company_name = body['company_name']
            if 'trade_name' in body: setting.trade_name = body['trade_name']
            if 'cnpj' in body: setting.cnpj = body['cnpj']
            if 'state_reg' in body: setting.state_reg = body['state_reg']
            if 'email' in body: setting.email = body['email']
            if 'phone' in body: setting.phone = body['phone']
            if 'address' in body: setting.address = body['address']
            if 'allow_negative_stock' in body: setting.allow_negative_stock = bool(body['allow_negative_stock'])
            if 'default_margin_percent' in body: setting.default_margin_percent = float(body['default_margin_percent'])
            if 'inventory_interval_days' in body: setting.inventory_interval_days = int(body['inventory_interval_days'])
            
            setting.updated_at = datetime.now(timezone.utc)

            admin_user_id = body.get('admin_user_id')
            admin_user_name = body.get('admin_user_name', 'Administrador')

            log_action(
                db, user_id=admin_user_id, user_name=admin_user_name,
                action="ALTERACAO_CONFIGURACOES", entity_type="CompanySetting", entity_id=setting.id,
                description="Parâmetros corporativos e políticas da empresa foram atualizados.",
                before_data=before_state, after_data=setting.to_dict()
            )
            db.commit()

        return jsonify({'success': True, 'settings': setting.to_dict()})
    finally:
        db.close()

# ---------------------------------------------------------------------------
# DIAGNÓSTICO DO BANCO DE DADOS (SUPABASE / POSTGRES / LOCAL)
# ---------------------------------------------------------------------------
@admin_bp.route('/db-diagnostic', methods=['GET'])
def db_diagnostic():
    import os
    db = get_db()
    try:
        start_t = time.time()
        products_count = db.query(Product).count()
        users_count = db.query(User).count()
        movements_count = db.query(StockMovement).count()
        inventories_count = db.query(Inventory).count()
        audit_count = db.query(AuditLog).count()
        prices_count = db.query(PriceHistory).count()
        latency_ms = round((time.time() - start_t) * 1000, 2)

        database_url = os.getenv("DATABASE_URL", "").strip()
        is_cloud = bool(database_url and ("postgres" in database_url or "supabase" in database_url))

        return jsonify({
            'success': True,
            'diagnostic': {
                'provider': 'Supabase (PostgreSQL)' if is_cloud else 'SQLite Local (Fallback)',
                'is_cloud': is_cloud,
                'connection_status': 'ONLINE',
                'latency_ms': latency_ms,
                'database_engine': str(db.get_bind().name).upper(),
                'tables_stats': {
                    'products': products_count,
                    'users': users_count,
                    'movements': movements_count,
                    'inventories': inventories_count,
                    'audit_logs': audit_count,
                    'price_history': prices_count
                }
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()
