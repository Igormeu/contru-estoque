from flask import Blueprint, request, jsonify, Response
from database import SessionLocal, Product, Category, Location, Unit, User, Role, StockMovement, PriceHistory, Price
from services import stock_service, price_service, inventory_service, audit_service, report_service
import csv
import io

api_bp = Blueprint('api', __name__, url_prefix='/api')

def get_db():
    return SessionLocal()

# ---------------------------------------------------------------------------
# DASHBOARD
# ---------------------------------------------------------------------------
@api_bp.route('/dashboard', methods=['GET'])
def get_dashboard():
    db = get_db()
    try:
        data = report_service.get_dashboard_data(db)
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()

# ---------------------------------------------------------------------------
# PRODUTOS / ITENS
# ---------------------------------------------------------------------------
@api_bp.route('/products', methods=['GET'])
def list_products():
    db = get_db()
    try:
        search = request.args.get('search', '').strip().lower()
        category_id = request.args.get('category_id')
        status = request.args.get('status')
        stock_status = request.args.get('stock_status')
        location_id = request.args.get('location_id')

        query = db.query(Product)
        if status == 'active':
            query = query.filter(Product.is_active == True)
        elif status == 'inactive':
            query = query.filter(Product.is_active == False)

        if category_id:
            query = query.filter(Product.category_id == int(category_id))
        if location_id:
            query = query.filter(Product.location_id == int(location_id))

        products = query.order_by(Product.name.asc()).all()

        results = []
        for p in products:
            p_dict = p.to_dict()
            if search:
                match_code = search in p.code.lower()
                match_name = search in p.name.lower()
                match_desc = p.description and search in p.description.lower()
                match_cat = p.category and search in p.category.name.lower()
                if not (match_code or match_name or match_desc or match_cat):
                    continue

            if stock_status and p_dict['stock_status'] != stock_status:
                continue

            results.append(p_dict)

        return jsonify({'success': True, 'data': results, 'total': len(results)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()

@api_bp.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    db = get_db()
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return jsonify({'success': False, 'error': 'Material não encontrado'}), 404
        
        data = product.to_dict()
        data['recent_movements'] = [m.to_dict() for m in product.movements[:10]]
        data['price_history'] = [ph.to_dict() for ph in product.price_histories[:10]]
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()

@api_bp.route('/products', methods=['POST'])
def create_product():
    db = get_db()
    try:
        body = request.get_json() or {}
        code = body.get('code', '').strip().upper()
        name = body.get('name', '').strip()
        if not code or not name:
            return jsonify({'success': False, 'error': 'Código e Nome são obrigatórios.'}), 400

        existing = db.query(Product).filter(Product.code == code).first()
        if existing:
            return jsonify({'success': False, 'error': f'Já existe um material cadastrado com o código {code}.'}), 400

        unit_id = body.get('unit_id')
        if not unit_id:
            u_default = db.query(Unit).first()
            unit_id = u_default.id if u_default else 1

        cat_id = body.get('category_id')
        if not cat_id:
            c_default = db.query(Category).first()
            cat_id = c_default.id if c_default else 1

        product = Product(
            code=code,
            name=name,
            description=body.get('description', ''),
            category_id=int(cat_id),
            subcategory=body.get('subcategory', ''),
            unit_id=int(unit_id),
            location_id=body.get('location_id'),
            min_stock=float(body.get('min_stock', 10.0)),
            max_stock=float(body.get('max_stock', 100.0)),
            image_url=body.get('image_url') or 'https://images.unsplash.com/photo-1581094288338-2314dddb7ece?w=400&auto=format&fit=crop&q=80',
            pdv_code=body.get('pdv_code') or code,
            is_active=True
        )
        db.add(product)
        db.flush()

        initial_stock = float(body.get('initial_stock', 0.0))
        cost_price = float(body.get('cost_price', 0.0))
        sale_price = float(body.get('sale_price', 0.0))

        stock = stock_service.ensure_stock_record(db, product.id)
        stock.quantity = 0.0

        price_rec = Price(product_id=product.id, cost_price=cost_price, sale_price=sale_price)
        db.add(price_rec)
        db.flush()

        if initial_stock > 0:
            stock_service.register_entry(
                db, product_id=product.id, quantity=initial_stock,
                user_id=body.get('user_id'), user_name=body.get('user_name'),
                origin_destination='Estoque Inicial', document_ref='CADASTRO_INICIAL',
                unit_price=cost_price, reason_notes='Saldo inicial informado no cadastro do item.'
            )
        else:
            db.commit()

        audit_service.log_action(
            db, user_id=body.get('user_id'), user_name=body.get('user_name'),
            action='CADASTRO', entity_type='Product', entity_id=product.id,
            description=f'Cadastro do material {product.code} - {product.name}',
            after_data=product.to_dict()
        )
        db.commit()

        return jsonify({'success': True, 'data': product.to_dict()}), 201
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        db.close()

@api_bp.route('/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    db = get_db()
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return jsonify({'success': False, 'error': 'Material não encontrado'}), 404

        body = request.get_json() or {}
        before_state = product.to_dict()

        if 'name' in body and body['name']:
            product.name = body['name'].strip()
        if 'description' in body:
            product.description = body['description']
        if 'category_id' in body and body['category_id']:
            product.category_id = int(body['category_id'])
        if 'subcategory' in body:
            product.subcategory = body['subcategory']
        if 'unit_id' in body and body['unit_id']:
            product.unit_id = int(body['unit_id'])
        if 'location_id' in body:
            product.location_id = int(body['location_id']) if body['location_id'] else None
        if 'min_stock' in body:
            product.min_stock = float(body['min_stock'])
        if 'max_stock' in body:
            product.max_stock = float(body['max_stock'])
        if 'image_url' in body:
            product.image_url = body['image_url']
        if 'pdv_code' in body:
            product.pdv_code = body['pdv_code']
        if 'is_active' in body:
            product.is_active = bool(body['is_active'])

        audit_service.log_action(
            db, user_id=body.get('user_id'), user_name=body.get('user_name'),
            action='EDICAO', entity_type='Product', entity_id=product.id,
            description=f'Atualização cadastral do material {product.code}',
            before_data=before_state, after_data=product.to_dict()
        )

        db.commit()
        return jsonify({'success': True, 'data': product.to_dict()})
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        db.close()

@api_bp.route('/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    db = get_db()
    try:
        user_id = request.args.get('user_id')
        user_name = request.args.get('user_name')
        res = stock_service.delete_or_inactivate_product(db, product_id, user_id, user_name)
        return jsonify({'success': True, 'result': res})
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        db.close()

# ---------------------------------------------------------------------------
# OPERAÇÕES DE ESTOQUE (Entradas, Saídas, Ajustes, Reposição)
# ---------------------------------------------------------------------------
@api_bp.route('/stock/entry', methods=['POST'])
def stock_entry():
    db = get_db()
    try:
        body = request.get_json() or {}
        product_id = body.get('product_id')
        quantity = float(body.get('quantity', 0))
        user_id = body.get('user_id')
        user_name = body.get('user_name')
        origin = body.get('origin_destination', 'Fornecedor')
        doc = body.get('document_ref')
        unit_price = float(body.get('unit_price', 0.0))
        notes = body.get('reason_notes')

        mov = stock_service.register_entry(
            db, product_id=product_id, quantity=quantity,
            user_id=user_id, user_name=user_name,
            origin_destination=origin, document_ref=doc,
            unit_price=unit_price, reason_notes=notes
        )
        return jsonify({'success': True, 'data': mov}), 201
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        db.close()

@api_bp.route('/stock/exit', methods=['POST'])
def stock_exit():
    db = get_db()
    try:
        body = request.get_json() or {}
        product_id = body.get('product_id')
        quantity = float(body.get('quantity', 0))
        user_id = body.get('user_id')
        user_name = body.get('user_name')
        dest = body.get('origin_destination', 'Consumo / Obra')
        notes = body.get('reason_notes')

        mov = stock_service.register_exit(
            db, product_id=product_id, quantity=quantity,
            user_id=user_id, user_name=user_name,
            origin_destination=dest, reason_notes=notes
        )
        return jsonify({'success': True, 'data': mov}), 201
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        db.close()

@api_bp.route('/stock/adjust', methods=['POST'])
def stock_adjust():
    db = get_db()
    try:
        body = request.get_json() or {}
        product_id = body.get('product_id')
        new_quantity = float(body.get('new_quantity', 0))
        justification = body.get('justification', '')
        user_id = body.get('user_id')
        user_name = body.get('user_name')

        mov = stock_service.register_adjustment(
            db, product_id=product_id, new_quantity=new_quantity,
            justification=justification, user_id=user_id, user_name=user_name
        )
        return jsonify({'success': True, 'data': mov}), 201
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        db.close()

@api_bp.route('/stock/movements', methods=['GET'])
def list_movements():
    db = get_db()
    try:
        product_id = request.args.get('product_id')
        movement_type = request.args.get('movement_type')
        category_id = request.args.get('category_id')
        limit = int(request.args.get('limit', 150))

        movements = stock_service.get_movements_history(
            db, product_id=int(product_id) if product_id else None,
            movement_type=movement_type,
            category_id=int(category_id) if category_id else None,
            limit=limit
        )
        return jsonify({'success': True, 'data': movements, 'total': len(movements)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()

@api_bp.route('/stock/replenishment', methods=['GET'])
def get_replenishment():
    db = get_db()
    try:
        items = stock_service.get_replenishment_items(db)
        total_estimated_cost = sum(it.get('estimated_replenishment_cost', 0) for it in items)
        return jsonify({
            'success': True, 
            'data': items, 
            'total_items_needing_restock': len(items),
            'total_estimated_cost': round(total_estimated_cost, 2)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()

# ---------------------------------------------------------------------------
# GESTÃO DE PREÇOS
# ---------------------------------------------------------------------------
@api_bp.route('/prices/update', methods=['POST'])
def update_price():
    db = get_db()
    try:
        body = request.get_json() or {}
        product_id = body.get('product_id')
        new_cost = body.get('cost_price')
        new_sale = body.get('sale_price')
        reason = body.get('reason')
        user_id = body.get('user_id')
        user_name = body.get('user_name')

        hist = price_service.update_product_price(
            db, product_id=product_id,
            new_cost_price=new_cost, new_sale_price=new_sale,
            reason=reason, user_id=user_id, user_name=user_name
        )
        return jsonify({'success': True, 'data': hist})
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        db.close()

@api_bp.route('/prices/history/<int:product_id>', methods=['GET'])
def get_price_history(product_id):
    db = get_db()
    try:
        history = price_service.get_product_price_history(db, product_id)
        return jsonify({'success': True, 'data': history})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()

@api_bp.route('/prices/recent', methods=['GET'])
def get_recent_prices():
    db = get_db()
    try:
        history = price_service.get_all_recent_price_changes(db, limit=30)
        return jsonify({'success': True, 'data': history})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()

# ---------------------------------------------------------------------------
# INVENTÁRIO
# ---------------------------------------------------------------------------
@api_bp.route('/inventories', methods=['GET'])
def list_inventories():
    db = get_db()
    try:
        inventories = inventory_service.get_all_inventories(db)
        return jsonify({'success': True, 'data': inventories})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()

@api_bp.route('/inventories', methods=['POST'])
def create_inventory():
    db = get_db()
    try:
        body = request.get_json() or {}
        title = body.get('title')
        inv_type = body.get('type', 'COMPLETO')
        cat_id = body.get('category_id')
        loc_id = body.get('location_id')
        notes = body.get('notes')
        user_id = body.get('user_id')
        user_name = body.get('user_name')

        inv = inventory_service.create_inventory(
            db, title=title, inventory_type=inv_type,
            category_id=int(cat_id) if cat_id else None,
            location_id=int(loc_id) if loc_id else None,
            notes=notes, user_id=user_id, user_name=user_name
        )
        return jsonify({'success': True, 'data': inv}), 201
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        db.close()

@api_bp.route('/inventories/<int:inv_id>', methods=['GET'])
def get_inventory(inv_id):
    db = get_db()
    try:
        inv = inventory_service.get_inventory_details(db, inv_id)
        if not inv:
            return jsonify({'success': False, 'error': 'Inventário não encontrado'}), 404
        return jsonify({'success': True, 'data': inv})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()

@api_bp.route('/inventories/<int:inv_id>/count', methods=['POST'])
def update_inventory_counts(inv_id):
    db = get_db()
    try:
        body = request.get_json() or {}
        counts = body.get('counts', [])
        inv = inventory_service.update_inventory_counts(db, inv_id, counts)
        return jsonify({'success': True, 'data': inv})
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        db.close()

@api_bp.route('/inventories/<int:inv_id>/finalize', methods=['POST'])
def finalize_inventory(inv_id):
    db = get_db()
    try:
        body = request.get_json() or {}
        user_id = body.get('user_id')
        user_name = body.get('user_name')
        inv = inventory_service.finalize_inventory(db, inv_id, user_id, user_name)
        return jsonify({'success': True, 'data': inv})
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        db.close()

# ---------------------------------------------------------------------------
# ESTRUTURAS AUXILIARES & AUDITORIA
# ---------------------------------------------------------------------------
@api_bp.route('/categories', methods=['GET', 'POST'])
def handle_categories():
    db = get_db()
    try:
        if request.method == 'POST':
            body = request.get_json() or {}
            name = body.get('name', '').strip()
            if not name:
                return jsonify({'success': False, 'error': 'Nome é obrigatório'}), 400
            cat = Category(name=name, description=body.get('description'), icon=body.get('icon', 'tag'))
            db.add(cat)
            db.commit()
            return jsonify({'success': True, 'data': cat.to_dict()}), 201
        
        cats = db.query(Category).order_by(Category.name.asc()).all()
        return jsonify({'success': True, 'data': [c.to_dict() for c in cats]})
    finally:
        db.close()

@api_bp.route('/locations', methods=['GET', 'POST'])
def handle_locations():
    db = get_db()
    try:
        if request.method == 'POST':
            body = request.get_json() or {}
            name = body.get('name', '').strip()
            if not name:
                return jsonify({'success': False, 'error': 'Nome é obrigatório'}), 400
            loc = Location(name=name, type=body.get('type', 'Almoxarifado'), description=body.get('description'))
            db.add(loc)
            db.commit()
            return jsonify({'success': True, 'data': loc.to_dict()}), 201

        locs = db.query(Location).order_by(Location.name.asc()).all()
        return jsonify({'success': True, 'data': [l.to_dict() for l in locs]})
    finally:
        db.close()

@api_bp.route('/units', methods=['GET'])
def list_units():
    db = get_db()
    try:
        units = db.query(Unit).all()
        return jsonify({'success': True, 'data': [u.to_dict() for u in units]})
    finally:
        db.close()

@api_bp.route('/users', methods=['GET'])
def list_users():
    db = get_db()
    try:
        users = db.query(User).all()
        roles = db.query(Role).all()
        return jsonify({
            'success': True,
            'users': [u.to_dict() for u in users],
            'roles': [r.to_dict() for r in roles]
        })
    finally:
        db.close()

@api_bp.route('/audit', methods=['GET'])
def list_audit():
    db = get_db()
    try:
        limit = int(request.args.get('limit', 100))
        action = request.args.get('action')
        logs = audit_service.get_audit_logs(db, limit=limit, action=action)
        return jsonify({'success': True, 'data': logs, 'total': len(logs)})
    finally:
        db.close()

# ---------------------------------------------------------------------------
# EXPORTAÇÃO CSV
# ---------------------------------------------------------------------------
@api_bp.route('/reports/export/csv', methods=['GET'])
def export_csv():
    db = get_db()
    try:
        export_type = request.args.get('type', 'stock')
        output = io.StringIO()
        writer = csv.writer(output, delimiter=';')

        if export_type == 'stock':
            writer.writerow(['Codigo', 'Material', 'Categoria', 'Unidade', 'Localizacao', 'Estoque Atual', 'Minimo', 'Maximo', 'Status', 'Preco Custo', 'Preco Venda', 'Valor Total (R$)'])
            products = db.query(Product).filter(Product.is_active == True).all()
            for p in products:
                pd = p.to_dict()
                writer.writerow([
                    pd['code'], pd['name'], pd['category_name'], pd['unit_code'], pd['location_name'],
                    pd['stock_quantity'], pd['min_stock'], pd['max_stock'], pd['stock_status'],
                    f"{pd['cost_price']:.2f}", f"{pd['sale_price']:.2f}", f"{pd['stock_value']:.2f}"
                ])
            filename = 'contru_estoque_posicao.csv'
        else:
            writer.writerow(['Data/Hora', 'Material', 'Tipo', 'Quantidade', 'Saldo Anterior', 'Saldo Posterior', 'Valor (R$)', 'Origem/Destino', 'Documento', 'Usuario', 'Observacao'])
            movements = db.query(StockMovement).order_by(StockMovement.created_at.desc()).limit(1000).all()
            for m in movements:
                md = m.to_dict()
                writer.writerow([
                    md['created_at'], f"{md['product_code']} - {md['product_name']}", md['movement_type'],
                    md['quantity'], md['previous_balance'], md['new_balance'], f"{md['total_value']:.2f}",
                    md['origin_destination'] or '', md['document_ref'] or '', md['user_name'], md['reason_notes'] or ''
                ])
            filename = 'contru_estoque_movimentacoes.csv'

        csv_content = output.getvalue()
        return Response(
            '\ufeff' + csv_content,
            mimetype='text/csv; charset=utf-8',
            headers={'Content-Disposition': f'attachment;filename={filename}'}
        )
    finally:
        db.close()
