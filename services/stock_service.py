from datetime import datetime, timezone
from database import Product, Stock, StockMovement, StockAdjustment, Price
from services.audit_service import log_action

def get_product_or_404(db, product_id):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise ValueError(f"Material #{product_id} não encontrado.")
    return product

def ensure_stock_record(db, product_id):
    stock = db.query(Stock).filter(Stock.product_id == product_id).first()
    if not stock:
        stock = Stock(product_id=product_id, quantity=0.0)
        db.add(stock)
        db.flush()
    return stock

def register_entry(db, product_id, quantity, user_id=None, user_name=None, origin_destination=None, document_ref=None, unit_price=0.0, reason_notes=None):
    """
    Registra uma entrada de estoque (Regras 1, 2, 6, 9).
    Atualiza o saldo e gera o registro imutável de movimentação.
    """
    if quantity <= 0:
        raise ValueError("A quantidade de entrada deve ser maior que zero.")

    product = get_product_or_404(db, product_id)
    stock = ensure_stock_record(db, product_id)

    previous_balance = stock.quantity
    new_balance = round(previous_balance + float(quantity), 2)
    stock.quantity = new_balance
    stock.updated_at = datetime.now(timezone.utc)

    total_val = round(float(quantity) * float(unit_price), 2)

    movement = StockMovement(
        product_id=product.id,
        movement_type="ENTRADA",
        quantity=float(quantity),
        previous_balance=previous_balance,
        new_balance=new_balance,
        unit_price=float(unit_price),
        total_value=total_val,
        user_id=user_id,
        user_name=user_name or "Sistema",
        origin_destination=origin_destination or "Fornecedor",
        document_ref=document_ref,
        reason_notes=reason_notes,
        created_at=datetime.now(timezone.utc)
    )
    db.add(movement)
    db.flush()

    # Log de auditoria
    log_action(
        db, user_id=user_id, user_name=user_name,
        action="ENTRADA_ESTOQUE", entity_type="StockMovement",
        entity_id=movement.id,
        description=f"Entrada de {quantity} {product.unit.code if product.unit else 'UN'} do item {product.code} - {product.name}",
        before_data={"saldo_anterior": previous_balance},
        after_data={"saldo_novo": new_balance, "quantidade_entrada": quantity, "documento": document_ref}
    )

    db.commit()
    return movement.to_dict()

def register_exit(db, product_id, quantity, user_id=None, user_name=None, origin_destination=None, reason_notes=None, allow_negative=False):
    """
    Registra uma saída de estoque (Regras 1, 2, 7, 9).
    Bloqueia saldo negativo por padrão (Regra 7).
    """
    if quantity <= 0:
        raise ValueError("A quantidade de saída deve ser maior que zero.")

    product = get_product_or_404(db, product_id)
    stock = ensure_stock_record(db, product_id)

    previous_balance = stock.quantity
    new_balance = round(previous_balance - float(quantity), 2)

    # Regra 7: Estoque negativo bloqueado por padrão
    if new_balance < 0 and not allow_negative:
        raise ValueError(
            f"Operação cancelada: Saldo insuficiente em estoque! "
            f"Disponível: {previous_balance} | Solicitado: {quantity}."
        )

    stock.quantity = new_balance
    stock.updated_at = datetime.now(timezone.utc)

    # Preço de custo atual do produto
    unit_price = product.price.cost_price if product.price else 0.0
    total_val = round(float(quantity) * float(unit_price), 2)

    movement = StockMovement(
        product_id=product.id,
        movement_type="SAIDA",
        quantity=float(quantity),
        previous_balance=previous_balance,
        new_balance=new_balance,
        unit_price=float(unit_price),
        total_value=total_val,
        user_id=user_id,
        user_name=user_name or "Sistema",
        origin_destination=origin_destination or "Saída Interna/Consumo",
        reason_notes=reason_notes,
        created_at=datetime.now(timezone.utc)
    )
    db.add(movement)
    db.flush()

    # Log de auditoria
    log_action(
        db, user_id=user_id, user_name=user_name,
        action="SAIDA_ESTOQUE", entity_type="StockMovement",
        entity_id=movement.id,
        description=f"Saída de {quantity} {product.unit.code if product.unit else 'UN'} do item {product.code} - {product.name}",
        before_data={"saldo_anterior": previous_balance},
        after_data={"saldo_novo": new_balance, "quantidade_saida": quantity, "destino": origin_destination}
    )

    db.commit()
    return movement.to_dict()

def register_adjustment(db, product_id, new_quantity, justification, user_id=None, user_name=None):
    """
    Registra um ajuste manual de estoque (Regras 1, 4, 9).
    Exige justificativa obrigatória (Regra 4).
    """
    if not justification or not justification.strip():
        raise ValueError("A justificativa para ajuste manual de estoque é estritamente obrigatória.")

    if new_quantity < 0:
        raise ValueError("O novo saldo em estoque não pode ser negativo.")

    product = get_product_or_404(db, product_id)
    stock = ensure_stock_record(db, product_id)

    previous_balance = stock.quantity
    diff = round(float(new_quantity) - previous_balance, 2)

    if diff == 0:
        raise ValueError("O novo saldo informado é idêntico ao saldo atual em estoque.")

    stock.quantity = float(new_quantity)
    stock.updated_at = datetime.now(timezone.utc)

    unit_price = product.price.cost_price if product.price else 0.0
    total_val = round(abs(diff) * unit_price, 2)

    movement = StockMovement(
        product_id=product.id,
        movement_type="AJUSTE",
        quantity=abs(diff),
        previous_balance=previous_balance,
        new_balance=float(new_quantity),
        unit_price=unit_price,
        total_value=total_val,
        user_id=user_id,
        user_name=user_name or "Sistema",
        origin_destination="Ajuste Manual",
        reason_notes=f"Ajuste ({'+' if diff > 0 else ''}{diff}): {justification}",
        created_at=datetime.now(timezone.utc)
    )
    db.add(movement)
    db.flush()

    adjustment = StockAdjustment(
        product_id=product.id,
        movement_id=movement.id,
        previous_quantity=previous_balance,
        new_quantity=float(new_quantity),
        diff_quantity=diff,
        justification=justification.strip(),
        user_id=user_id,
        created_at=datetime.now(timezone.utc)
    )
    db.add(adjustment)
    db.flush()

    # Log de auditoria
    log_action(
        db, user_id=user_id, user_name=user_name,
        action="AJUSTE_ESTOQUE", entity_type="StockAdjustment",
        entity_id=adjustment.id,
        description=f"Ajuste manual de {previous_balance} para {new_quantity} no item {product.code}: {justification}",
        before_data={"saldo_anterior": previous_balance},
        after_data={"saldo_novo": new_quantity, "diferenca": diff, "justificativa": justification}
    )

    db.commit()
    return movement.to_dict()

def can_delete_product(db, product_id):
    """Regra 5: Impede exclusão definitiva de itens que possuam movimentações."""
    movements_count = db.query(StockMovement).filter(StockMovement.product_id == product_id).count()
    return movements_count == 0

def delete_or_inactivate_product(db, product_id, user_id=None, user_name=None):
    """
    Exclui o item se não tiver histórico; se tiver histórico, apenas inativa o item (Regra 5).
    """
    product = get_product_or_404(db, product_id)
    if not can_delete_product(db, product_id):
        # Apenas inativa
        product.is_active = False
        product.updated_at = datetime.now(timezone.utc)
        log_action(
            db, user_id=user_id, user_name=user_name,
            action="INATIVACAO", entity_type="Product",
            entity_id=product.id,
            description=f"Material {product.code} - {product.name} inativado pois possui histórico de movimentações."
        )
        db.commit()
        return {"action": "inactivated", "message": "O item possui movimentações registradas e foi INATIVADO para manter a integridade do histórico."}
    else:
        # Exclusão segura
        code = product.code
        name = product.name
        db.delete(product)
        log_action(
            db, user_id=user_id, user_name=user_name,
            action="EXCLUSAO", entity_type="Product",
            entity_id=product_id,
            description=f"Material {code} - {name} excluído definitivamente (sem histórico)."
        )
        db.commit()
        return {"action": "deleted", "message": f"Material {code} excluído com sucesso."}

def get_movements_history(db, product_id=None, movement_type=None, category_id=None, start_date=None, end_date=None, limit=200):
    """Recupera o histórico completo com filtros."""
    query = db.query(StockMovement).join(Product)
    
    if product_id:
        query = query.filter(StockMovement.product_id == product_id)
    if movement_type:
        query = query.filter(StockMovement.movement_type == movement_type.upper())
    if category_id:
        query = query.filter(Product.category_id == category_id)
    if start_date:
        query = query.filter(StockMovement.created_at >= start_date)
    if end_date:
        query = query.filter(StockMovement.created_at <= end_date)
        
    movements = query.order_by(StockMovement.created_at.desc()).limit(limit).all()
    return [m.to_dict() for m in movements]

def get_replenishment_items(db):
    """Retorna itens que precisam de reposição com cálculo de sugestão."""
    products = db.query(Product).filter(Product.is_active == True).all()
    replenishment_list = []
    
    for p in products:
        stock_qty = p.stock.quantity if p.stock else 0.0
        if stock_qty <= p.min_stock:
            cost_p = p.price.cost_price if p.price else 0.0
            suggested_qty = max(0.0, round(p.max_stock - stock_qty, 2))
            estimated_cost = round(suggested_qty * cost_p, 2)
            item_dict = p.to_dict()
            item_dict["suggested_restock"] = suggested_qty
            item_dict["estimated_replenishment_cost"] = estimated_cost
            item_dict["urgency"] = "CRITICA" if stock_qty == 0 else "ALTA"
            replenishment_list.append(item_dict)
            
    # Ordena por urgência (zerados primeiro, depois maior diferença)
    replenishment_list.sort(key=lambda x: (0 if x["stock_quantity"] == 0 else 1, x["stock_quantity"] / max(1, x["min_stock"])))
    return replenishment_list
