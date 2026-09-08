from flask import Blueprint, request, jsonify
from database import SessionLocal
from services import pdv_service

pdv_bp = Blueprint('pdv', __name__, url_prefix='/api/pdv')

def get_db():
    return SessionLocal()

@pdv_bp.route('/status', methods=['GET'])
def pdv_status():
    db = get_db()
    try:
        status_data = pdv_service.get_pdv_status_summary(db)
        return jsonify({'success': True, 'data': status_data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()

@pdv_bp.route('/products', methods=['GET'])
def pdv_products():
    """Endpoint padronizado para o sistema de PDV consumir o catálogo e preços atuais."""
    db = get_db()
    try:
        catalog = pdv_service.get_catalog_for_pdv(db)
        return jsonify({
            'success': True,
            'source': 'CONTRU_ESTOQUE_API_V2',
            'total_items': len(catalog),
            'products': catalog
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()

@pdv_bp.route('/sale', methods=['POST'])
def pdv_receive_sale():
    """Recebe um cupom/venda emitido no PDV e dá baixa imediata no estoque do CONTRU ESTOQUE."""
    db = get_db()
    try:
        payload = request.get_json() or {}
        user_id = payload.get('user_id')
        user_name = payload.get('user_name', 'Frente de Caixa PDV')
        
        result = pdv_service.process_pdv_sale(db, payload, user_id=user_id, user_name=user_name)
        return jsonify(result), 200
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        db.close()

@pdv_bp.route('/sync', methods=['POST'])
def pdv_sync():
    """Endpoint para forçar sincronização manual da fila."""
    db = get_db()
    try:
        pdv = pdv_service.get_or_create_pdv_config(db)
        from datetime import datetime, timezone
        pdv.last_sync_at = datetime.now(timezone.utc)
        pdv.status = 'CONECTADO_ATIVO'
        db.commit()
        return jsonify({
            'success': True,
            'message': 'Sincronização com o PDV executada com sucesso.',
            'synced_at': pdv.last_sync_at.isoformat()
        })
    finally:
        db.close()
