from datetime import datetime, timezone
from database import PDVIntegration, Product, Stock, StockMovement
from services.audit_service import log_action

def get_or_create_pdv_config(db):
    """Recupera ou inicializa a entidade de status da integração PDV."""
    pdv = db.query(PDVIntegration).first()
    if not pdv:
        pdv = PDVIntegration(
            pdv_system_name="CONTRU PDV - Frente de Caixa Modular",
            status="PRONTO_PARA_INTEGRACAO",
            api_endpoint="/api/pdv/sync",
            webhook_url="https://api.contruestoque.com.br/v1/webhooks/pdv",
            config_json={
                "version": "2.0.4",
                "auth_type": "Bearer Token",
                "sync_interval_seconds": 60,
                "allow_negative_stock_on_sale": False,
                "field_mappings": {
                    "pdv_barcode": "product.pdv_code",
                    "sku": "product.code",
                    "price": "price.sale_price",
                    "stock_available": "stock.quantity"
                }
            }
        )
        db.add(pdv)
        db.commit()
    return pdv

def get_pdv_status_summary(db):
    """Calcula estatísticas de prontidão e sincronização com o PDV."""
    pdv = get_or_create_pdv_config(db)
    
    # Itens ativos cadastrados com código PDV configurado
    active_pdv_items = db.query(Product).filter(
        Product.is_active == True,
        Product.pdv_code != None
    ).count()

    total_products = db.query(Product).filter(Product.is_active == True).count()

    # Movimentações originadas pelo PDV
    pdv_sales_count = db.query(StockMovement).filter(
        StockMovement.movement_type == "PDV_VENDA"
    ).count()

    return {
        "status": pdv.status,
        "system_name": pdv.pdv_system_name,
        "last_sync_at": pdv.last_sync_at.isoformat() if pdv.last_sync_at else "Ainda não sincronizado",
        "configured_pdv_items": active_pdv_items,
        "total_active_items": total_products,
        "pdv_sales_total": pdv_sales_count,
        "api_endpoint": pdv.api_endpoint,
        "webhook_url": pdv.webhook_url,
        "config": pdv.config_json
    }

def get_catalog_for_pdv(db):
    """Retorna o catálogo de produtos no formato padronizado para sincronização de PDV."""
    products = db.query(Product).filter(Product.is_active == True).all()
    payload = []
    for p in products:
        payload.append({
            "internal_id": p.id,
            "sku": p.code,
            "barcode_pdv": p.pdv_code or p.code,
            "name": p.name,
            "unit": p.unit.code if p.unit else "UN",
            "category": p.category.name if p.category else "Geral",
            "sale_price": p.price.sale_price if p.price else 0.0,
            "current_stock": p.stock.quantity if p.stock else 0.0,
            "is_available": (p.stock.quantity if p.stock else 0.0) > 0
        })
    return payload

def process_pdv_sale(db, sale_payload, user_id=None, user_name=None):
    """
    Processa uma venda vinda do PDV (ou simulada pelo painel).
    Atualiza o estoque e registra movimentação do tipo PDV_VENDA (Regras 1, 2, 7, 9).
    """
    items = sale_payload.get("items", [])
    doc_ref = sale_payload.get("sale_document", f"CUPOM-PDV-{int(datetime.now().timestamp())}")
    terminal_id = sale_payload.get("terminal_id", "CAIXA-01")

    if not items:
        raise ValueError("A venda recebida do PDV não contém nenhum item.")

    processed_movements = []

    for it in items:
        product_id = it.get("product_id")
        sku = it.get("sku")
        qty = float(it.get("quantity", 1.0))
        unit_price = float(it.get("unit_price", 0.0))

        product = None
        if product_id:
            product = db.query(Product).filter(Product.id == product_id).first()
        elif sku:
            product = db.query(Product).filter(Product.code == sku).first()

        if not product:
            raise ValueError(f"Produto #{product_id or sku} não localizado no cadastro de estoque.")

        if not product.stock:
            raise ValueError(f"Item {product.code} não possui registro de estoque.")

        if product.stock.quantity < qty:
            raise ValueError(f"Estoque insuficiente para {product.name}! Saldo atual: {product.stock.quantity}, Solicitado: {qty}.")

        prev_balance = product.stock.quantity
        new_balance = round(prev_balance - qty, 2)
        product.stock.quantity = new_balance
        product.stock.updated_at = datetime.now(timezone.utc)

        movement = StockMovement(
            product_id=product.id,
            movement_type="PDV_VENDA",
            quantity=qty,
            previous_balance=prev_balance,
            new_balance=new_balance,
            unit_price=unit_price or (product.price.sale_price if product.price else 0.0),
            total_value=round(qty * (unit_price or (product.price.sale_price if product.price else 0.0)), 2),
            user_id=user_id,
            user_name=user_name or f"Operador {terminal_id}",
            origin_destination=f"Frente de Caixa - {terminal_id}",
            document_ref=doc_ref,
            reason_notes=f"Venda registrada no PDV ({doc_ref})",
            created_at=datetime.now(timezone.utc)
        )
        db.add(movement)
        processed_movements.append(movement)

    # Atualiza status e data de sincronização
    pdv = get_or_create_pdv_config(db)
    pdv.last_sync_at = datetime.now(timezone.utc)
    pdv.status = "CONECTADO_ATIVO"

    log_action(
        db, user_id=user_id, user_name=user_name,
        action="VENDA_PDV", entity_type="PDVIntegration",
        entity_id=pdv.id,
        description=f"Venda PDV {doc_ref} processada com sucesso: {len(items)} itens baixados no estoque."
    )

    db.commit()
    return {
        "success": True,
        "document": doc_ref,
        "items_count": len(items),
        "synced_at": pdv.last_sync_at.isoformat()
    }
