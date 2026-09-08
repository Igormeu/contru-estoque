from datetime import datetime, timezone, timedelta
from sqlalchemy import func
from database import Product, Stock, StockMovement, Price, Category, Location, PriceHistory

def get_dashboard_data(db):
    """Calcula todos os indicadores (KPIs), dados de gráficos e alertas do Dashboard."""
    # 1. Total e Ativos
    total_products = db.query(Product).count()
    active_products = db.query(Product).filter(Product.is_active == True).count()

    # 2. Estoques, Valor e Alertas
    products = db.query(Product).filter(Product.is_active == True).all()
    
    total_stock_qty = 0.0
    total_stock_value = 0.0
    low_stock_count = 0
    zero_stock_count = 0
    low_stock_items = []
    
    category_valuation = {}

    for p in products:
        qty = p.stock.quantity if p.stock else 0.0
        cost_p = p.price.cost_price if p.price else 0.0
        val = qty * cost_p

        total_stock_qty += qty
        total_stock_value += val

        cat_name = p.category.name if p.category else "Outros"
        category_valuation[cat_name] = category_valuation.get(cat_name, 0.0) + val

        if qty <= 0:
            zero_stock_count += 1
            low_stock_items.append({
                "id": p.id,
                "code": p.code,
                "name": p.name,
                "current": qty,
                "min": p.min_stock,
                "urgency": "RUPTURA"
            })
        elif qty <= p.min_stock:
            low_stock_count += 1
            low_stock_items.append({
                "id": p.id,
                "code": p.code,
                "name": p.name,
                "current": qty,
                "min": p.min_stock,
                "urgency": "BAIXO"
            })

    # 3. Entradas e Saídas no mês atual
    now = datetime.now(timezone.utc)
    month_start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)

    entries_month = db.query(
        func.coalesce(func.sum(StockMovement.quantity), 0.0)
    ).filter(
        StockMovement.movement_type == "ENTRADA",
        StockMovement.created_at >= month_start
    ).scalar()

    exits_month = db.query(
        func.coalesce(func.sum(StockMovement.quantity), 0.0)
    ).filter(
        StockMovement.movement_type.in_(["SAIDA", "PDV_VENDA"]),
        StockMovement.created_at >= month_start
    ).scalar()

    # 4. Últimas 8 movimentações
    recent_movements = db.query(StockMovement).order_by(
        StockMovement.created_at.desc()
    ).limit(8).all()

    # 5. Top 5 materiais mais movimentados
    top_moved_query = db.query(
        Product.name,
        Product.code,
        func.sum(StockMovement.quantity).label("total_qty")
    ).join(StockMovement, Product.id == StockMovement.product_id)\
     .group_by(Product.id)\
     .order_by(func.sum(StockMovement.quantity).desc())\
     .limit(5).all()

    top_moved = [
        {"name": row[0], "code": row[1], "quantity": float(row[2])}
        for row in top_moved_query
    ]

    # 6. Alertas recentes de preço (últimos 30 dias)
    recent_price_changes = db.query(PriceHistory).order_by(
        PriceHistory.created_at.desc()
    ).limit(5).all()

    # 7. Dados de movimentação mensal (últimos 6 meses) para o gráfico Entradas x Saídas
    months_labels = []
    entries_series = []
    exits_series = []

    for i in range(5, -1, -1):
        # Mês retroativo
        calc_date = now - timedelta(days=i * 30)
        m_start = datetime(calc_date.year, calc_date.month, 1, tzinfo=timezone.utc)
        if calc_date.month == 12:
            m_end = datetime(calc_date.year + 1, 1, 1, tzinfo=timezone.utc)
        else:
            m_end = datetime(calc_date.year, calc_date.month + 1, 1, tzinfo=timezone.utc)

        month_name = calc_date.strftime("%b/%y")
        months_labels.append(month_name)

        ent = db.query(func.coalesce(func.sum(StockMovement.quantity), 0.0)).filter(
            StockMovement.movement_type == "ENTRADA",
            StockMovement.created_at >= m_start,
            StockMovement.created_at < m_end
        ).scalar()
        entries_series.append(float(ent))

        sai = db.query(func.coalesce(func.sum(StockMovement.quantity), 0.0)).filter(
            StockMovement.movement_type.in_(["SAIDA", "PDV_VENDA"]),
            StockMovement.created_at >= m_start,
            StockMovement.created_at < m_end
        ).scalar()
        exits_series.append(float(sai))

    return {
        "kpis": {
            "total_items": total_products,
            "active_items": active_products,
            "total_stock_quantity": round(total_stock_qty, 2),
            "total_stock_value": round(total_stock_value, 2),
            "low_stock_count": low_stock_count,
            "zero_stock_count": zero_stock_count,
            "entries_this_month": round(float(entries_month), 2),
            "exits_this_month": round(float(exits_month), 2)
        },
        "charts": {
            "comparison": {
                "labels": months_labels,
                "entries": entries_series,
                "exits": exits_series
            },
            "category_valuation": {
                "categories": list(category_valuation.keys()),
                "values": [round(v, 2) for v in category_valuation.values()]
            },
            "top_moved": top_moved
        },
        "alerts": {
            "critical_stock": low_stock_items[:8],
            "recent_price_changes": [p.to_dict() for p in recent_price_changes]
        },
        "recent_movements": [m.to_dict() for m in recent_movements]
    }

def get_full_stock_report(db, category_id=None, status_filter=None):
    """Relatório completo de posição de estoque."""
    query = db.query(Product).filter(Product.is_active == True)
    if category_id:
        query = query.filter(Product.category_id == category_id)

    products = query.order_by(Product.name.asc()).all()
    report = []
    for p in products:
        p_dict = p.to_dict()
        if status_filter and p_dict["stock_status"] != status_filter:
            continue
        report.append(p_dict)
    return report
