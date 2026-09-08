from flask import Blueprint, request, jsonify
from datetime import datetime, timezone
from database import SessionLocal, User
from services.audit_service import log_action

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

def get_db():
    return SessionLocal()

@auth_bp.route('/login', methods=['POST'])
def login():
    db = get_db()
    try:
        body = request.get_json() or {}
        email = body.get('email', '').strip().lower()
        password = body.get('password', '').strip()

        if not email or not password:
            return jsonify({'success': False, 'error': 'E-mail e senha são obrigatórios.'}), 400

        user = db.query(User).filter(User.email == email).first()
        if not user:
            return jsonify({'success': False, 'error': 'Credenciais incorretas. Verifique seu e-mail e senha.'}), 401

        if not user.is_active:
            return jsonify({'success': False, 'error': 'Acesso bloqueado: Este usuário foi desativado pelo administrador.'}), 403

        if not user.check_password(password):
            return jsonify({'success': False, 'error': 'Credenciais incorretas. Verifique seu e-mail e senha.'}), 401

        # Atualiza último login
        user.last_login_at = datetime.now(timezone.utc)
        
        # Log de auditoria
        log_action(
            db, user_id=user.id, user_name=user.name,
            action="LOGIN", entity_type="User", entity_id=user.id,
            description=f"Autenticação bem-sucedida do usuário {user.name} ({user.role.display_name if user.role else 'Perfil'})."
        )
        db.commit()

        user_dict = user.to_dict()
        return jsonify({
            'success': True,
            'user': user_dict,
            'token': f"session_{user.id}_{int(datetime.now().timestamp())}"
        })
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()

@auth_bp.route('/logout', methods=['POST'])
def logout():
    db = get_db()
    try:
        body = request.get_json() or {}
        user_id = body.get('user_id')
        user_name = body.get('user_name', 'Usuário')

        if user_id:
            log_action(
                db, user_id=user_id, user_name=user_name,
                action="LOGOUT", entity_type="User", entity_id=user_id,
                description=f"Encerramento de sessão do usuário {user_name}."
            )
            db.commit()

        return jsonify({'success': True, 'message': 'Sessão encerrada com sucesso.'})
    finally:
        db.close()

@auth_bp.route('/change-password', methods=['PUT'])
def change_password():
    db = get_db()
    try:
        body = request.get_json() or {}
        user_id = body.get('user_id')
        current_password = body.get('current_password', '')
        new_password = body.get('new_password', '')

        if not user_id or not current_password or not new_password:
            return jsonify({'success': False, 'error': 'Informe a senha atual e a nova senha.'}), 400

        if len(new_password) < 6:
            return jsonify({'success': False, 'error': 'A nova senha deve possuir no mínimo 6 caracteres.'}), 400

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return jsonify({'success': False, 'error': 'Usuário não encontrado.'}), 404

        if not user.check_password(current_password):
            return jsonify({'success': False, 'error': 'A senha atual informada está incorreta.'}), 400

        user.set_password(new_password)
        log_action(
            db, user_id=user.id, user_name=user.name,
            action="ALTERACAO_SENHA", entity_type="User", entity_id=user.id,
            description=f"O usuário {user.name} alterou sua própria senha de acesso."
        )
        db.commit()

        return jsonify({'success': True, 'message': 'Senha alterada com sucesso!'})
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()
