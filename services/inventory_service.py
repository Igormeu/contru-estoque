from datetime import datetime, timezone
from database import Inventory, InventoryItem, Product, Stock, StockMovement
from services.audit_service import log_action

def create_inventory(db, title, inventory_type="COMPLETO", category_id=None, location_id=None, notes=None, user_id=None, user_name=None):
    """
    Cria uma nova sessão de inventário e inclui os itens correspondentes com snapshot do saldo do sistema.
    """
    # Gera código sequencial amigável INV-YYYY-XXX
    current_year = datetime.now(timezone.utc).year
    count_this_year = db.query(Inventory).filter(Inventory.code.like(f"INV-{current_year}-%")).count() + 1
    code = f"INV-{current_year}-{count_this_year:03d}"

    inventory = Inventory(
        code=code,
        title=title or f"Inventário Geral {code}",
        type=inventory_type,
        category_id=category_id if inventory_type == "CATEGORIA" else None,
        location_id=location_id if inventory_type == "LOCALIZACAO" else None,
        status="EM_ANDAMENTO",
        notes=notes,
        user_id=user_id,
        user_name=user_name or "Sistema",
        started_at=datetime.now(timezone.utc)
    )
    db.add(inventory)
    db.flush()

    # Seleciona produtos alvo
    query = db.query(Product).filter(Product.is_active == True)
    if inventory_type == "CATEGORIA" and category_id:
        query = query.filter(Product.category_id == category_id)
    elif inventory_type == "LOCALIZACAO" and location_id:
        query = query.filter(Product.location_id == location_id)

    products = query.all()
    for prod in products:
        sys_qty = prod.stock.quantity if prod.stock else 0.0
        cost_p = prod.price.cost_price if prod.price else 0.0
        
        item = InventoryItem(
            inventory_id=inventory.id,
            product_id=prod.id,
            system_quantity=sys_qty,
            counted_quantity=sys_qty, # Inicialmente preenchido com sistema, usuário edita
            diff_quantity=0.0,
            diff_percent=0.0,
            cost_price=cost_p,
            diff_value=0.0
        )
        db.add(item)

    log_action(
        db, user_id=user_id, user_name=user_name,
        action="CRIACAO_INVENTARIO", entity_type="Inventory",
        entity_id=inventory.id,
        description=f"Abertura de inventário {code} ({inventory_type}) com {len(products)} itens."
    )

    db.commit()
    return inventory.to_dict(include_items=True)

def update_inventory_counts(db, inventory_id, counts_data):
    """
    Atualiza as quantidades contadas fisicamente e recalcula divergências automaticamente.
    counts_data: list of dicts: [{"item_id": 1, "counted_quantity": 45.0, "notes": "OK"}]
    """
    inventory = db.query(Inventory).filter(Inventory.id == inventory_id).first()
    if not inventory:
        raise ValueError(f"Inventário #{inventory_id} não encontrado.")

    if inventory.status != "EM_ANDAMENTO":
        raise ValueError("Este inventário já está finalizado ou cancelado e não aceita mais alterações.")

    for item_data in counts_data:
        item_id = item_data.get("item_id")
        counted_qty = float(item_data.get("counted_quantity", 0.0))
        item_notes = item_data.get("notes")

        inv_item = db.query(InventoryItem).filter(
            InventoryItem.id == item_id,
            InventoryItem.inventory_id == inventory.id
        ).first()

        if inv_item:
            sys_qty = inv_item.system_quantity
            diff_qty = round(counted_qty - sys_qty, 2)
            
            diff_pct = 0.0
            if sys_qty > 0:
                diff_pct = round((diff_qty / sys_qty) * 100, 2)
            elif diff_qty > 0:
                diff_pct = 100.0

            diff_val = round(diff_qty * inv_item.cost_price, 2)

            inv_item.counted_quantity = counted_qty
            inv_item.diff_quantity = diff_qty
            inv_item.diff_percent = diff_pct
            inv_item.diff_value = diff_val
            if item_notes is not None:
                inv_item.notes = item_notes

    db.commit()
    return inventory.to_dict(include_items=True)

def finalize_inventory(db, inventory_id, user_id=None, user_name=None):
    """
    Finaliza o inventário aplicando as divergências no saldo real do estoque e
    gerando movimentações automáticas do tipo INVENTARIO (Regras 1, 2, 9).
    """
    inventory = db.query(Inventory).filter(Inventory.id == inventory_id).first()
    if not inventory:
        raise ValueError(f"Inventário #{inventory_id} não encontrado.")

    if inventory.status != "EM_ANDAMENTO":
        raise ValueError("O inventário já se encontra finalizado.")

    divergent_items_count = 0
    total_adjusted_value = 0.0

    for item in inventory.items:
        if item.diff_quantity != 0.0:
            product = db.query(Product).filter(Product.id == item.product_id).first()
            if not product or not product.stock:
                continue

            prev_balance = product.stock.quantity
            new_balance = round(item.counted_quantity, 2)

            # Atualiza estoque
            product.stock.quantity = new_balance
            product.stock.updated_at = datetime.now(timezone.utc)

            # Cria movimentação do tipo INVENTARIO
            movement = StockMovement(
                product_id=product.id,
                movement_type="INVENTARIO",
                quantity=abs(item.diff_quantity),
                previous_balance=prev_balance,
                new_balance=new_balance,
                unit_price=item.cost_price,
                total_value=abs(item.diff_value),
                user_id=user_id,
                user_name=user_name or "Sistema",
                origin_destination=f"Inventário {inventory.code}",
                reason_notes=f"Divergência apurada no {inventory.code}: Contado {item.counted_quantity} vs Sistema {item.system_quantity} ({'+' if item.diff_quantity > 0 else ''}{item.diff_quantity}).",
                created_at=datetime.now(timezone.utc)
            )
            db.add(movement)
            divergent_items_count += 1
            total_adjusted_value += abs(item.diff_value)

    inventory.status = "FINALIZADO"
    inventory.completed_at = datetime.now(timezone.utc)

    log_action(
        db, user_id=user_id, user_name=user_name,
        action="FINALIZACAO_INVENTARIO", entity_type="Inventory",
        entity_id=inventory.id,
        description=f"Inventário {inventory.code} finalizado. {divergent_items_count} itens ajustados automaticamente (Total divergências: R$ {total_adjusted_value:.2f})."
    )

    db.commit()
    return inventory.to_dict(include_items=True)

def get_all_inventories(db):
    """Lista todos os inventários cadastrados."""
    inventories = db.query(Inventory).order_by(Inventory.created_at.desc()).all()
    return [inv.to_dict(include_items=False) for inv in inventories]

def get_inventory_details(db, inventory_id):
    """Recupera os detalhes completos de um inventário com seus itens."""
    inventory = db.query(Inventory).filter(Inventory.id == inventory_id).first()
    if not inventory:
        return None
    return inventory.to_dict(include_items=True)
