from datetime import datetime, timezone
from database import Product, Price, PriceHistory
from services.audit_service import log_action

def update_product_price(db, product_id, new_cost_price=None, new_sale_price=None, reason=None, user_id=None, user_name=None):
    """
    Atualiza o preço de custo e/ou venda do produto (Regras 3, 9, 10).
    Exige justificativa obrigatória e armazena histórico imutável.
    """
    if not reason or not reason.strip():
        raise ValueError("O motivo para a alteração de preço é estritamente obrigatório.")

    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise ValueError(f"Material #{product_id} não encontrado.")

    price = db.query(Price).filter(Price.product_id == product_id).first()
    if not price:
        price = Price(product_id=product_id, cost_price=0.0, sale_price=0.0)
        db.add(price)
        db.flush()

    prev_cost = price.cost_price
    prev_sale = price.sale_price

    final_cost = float(new_cost_price) if new_cost_price is not None else prev_cost
    final_sale = float(new_sale_price) if new_sale_price is not None else prev_sale

    if final_cost < 0 or final_sale < 0:
        raise ValueError("Os preços não podem ser valores negativos.")

    if final_cost == prev_cost and final_sale == prev_sale:
        raise ValueError("Os novos preços informados são idênticos aos preços atuais.")

    # Atualiza o preço atual
    price.cost_price = final_cost
    price.sale_price = final_sale
    price.updated_at = datetime.now(timezone.utc)
    product.updated_at = datetime.now(timezone.utc)

    # Registra o histórico
    history = PriceHistory(
        product_id=product.id,
        previous_cost_price=prev_cost,
        new_cost_price=final_cost,
        previous_sale_price=prev_sale,
        new_sale_price=final_sale,
        reason=reason.strip(),
        user_id=user_id,
        user_name=user_name or "Sistema",
        created_at=datetime.now(timezone.utc)
    )
    db.add(history)
    db.flush()

    # Log de auditoria
    log_action(
        db, user_id=user_id, user_name=user_name,
        action="REAJUSTE_PRECO", entity_type="Price",
        entity_id=price.id,
        description=f"Preço reajustado para o item {product.code} - {product.name}. Custo: R$ {prev_cost:.2f} -> R$ {final_cost:.2f} | Venda: R$ {prev_sale:.2f} -> R$ {final_sale:.2f}. Motivo: {reason}",
        before_data={"custo": prev_cost, "venda": prev_sale},
        after_data={"custo": final_cost, "venda": final_sale, "motivo": reason}
    )

    db.commit()
    return history.to_dict()

def get_product_price_history(db, product_id):
    """Retorna o histórico de preços ordenado cronologicamente de um material."""
    histories = db.query(PriceHistory).filter(
        PriceHistory.product_id == product_id
    ).order_by(PriceHistory.created_at.desc()).all()
    return [h.to_dict() for h in histories]

def get_all_recent_price_changes(db, limit=50):
    """Retorna todas as alterações recentes de preços do sistema."""
    histories = db.query(PriceHistory).order_by(PriceHistory.created_at.desc()).limit(limit).all()
    return [h.to_dict() for h in histories]
