import unittest
from datetime import datetime, timezone
from database import SessionLocal, init_db, Product, Stock, StockMovement, PriceHistory, AuditLog
from services import stock_service, price_service, inventory_service, pdv_service

class TestContruEstoque(unittest.TestCase):
    def setUp(self):
        init_db()
        self.db = SessionLocal()

    def tearDown(self):
        self.db.close()

    def test_01_stock_entry_updates_balance_and_creates_movement(self):
        """Regra 1: Nunca alterar saldo sem gerar movimentação."""
        product = self.db.query(Product).first()
        initial_balance = product.stock.quantity

        res = stock_service.register_entry(
            self.db, product_id=product.id, quantity=10.0,
            user_name="Tester", origin_destination="Fornecedor Teste",
            document_ref="NF-TEST-01", unit_price=50.0
        )
        self.db.refresh(product)
        self.assertEqual(product.stock.quantity, initial_balance + 10.0)
        self.assertEqual(res["movement_type"], "ENTRADA")
        self.assertEqual(res["new_balance"], initial_balance + 10.0)

    def test_02_negative_stock_blocked_by_default(self):
        """Regra 7: Estoque negativo bloqueado por padrão."""
        product = self.db.query(Product).first()
        excessive_qty = product.stock.quantity + 99999.0
        with self.assertRaises(ValueError) as context:
            stock_service.register_exit(
                self.db, product_id=product.id, quantity=excessive_qty,
                user_name="Tester", origin_destination="Obra"
            )
        self.assertIn("Saldo insuficiente", str(context.exception))

    def test_03_stock_adjustment_requires_justification(self):
        """Regra 4: Ajustes de estoque exigem justificativa obrigatória."""
        product = self.db.query(Product).first()
        with self.assertRaises(ValueError) as context:
            stock_service.register_adjustment(
                self.db, product_id=product.id, new_quantity=product.stock.quantity + 5,
                justification="", user_name="Tester"
            )
        self.assertIn("justificativa", str(context.exception).lower())

    def test_04_cannot_delete_product_with_movements(self):
        """Regra 5: Itens com histórico não podem ser excluídos definitivamente (devem ser inativados)."""
        product = self.db.query(Product).filter(Product.is_active == True).first()
        res = stock_service.delete_or_inactivate_product(self.db, product.id, user_name="Tester")
        self.assertEqual(res["action"], "inactivated")
        self.db.refresh(product)
        self.assertFalse(product.is_active)
        # Reativa para outros testes
        product.is_active = True
        self.db.commit()

    def test_05_price_change_creates_history(self):
        """Regra 3: Alterações de preço devem possuir histórico e motivo."""
        product = self.db.query(Product).first()
        old_cost = product.price.cost_price
        new_cost = old_cost + 15.0

        hist = price_service.update_product_price(
            self.db, product_id=product.id, new_cost_price=new_cost,
            reason="Aumento de combustíveis e logística", user_name="Financeiro Teste"
        )
        self.assertEqual(hist["new_cost_price"], new_cost)
        self.assertEqual(hist["reason"], "Aumento de combustíveis e logística")

    def test_06_replenishment_suggestions(self):
        """Regra 6: Identificação de reposição (Estoque <= Mínimo) e sugestão de compra."""
        items = stock_service.get_replenishment_items(self.db)
        self.assertGreater(len(items), 0)
        for it in items:
            self.assertLessEqual(it["stock_quantity"], it["min_stock"])
            self.assertGreaterEqual(it["suggested_restock"], 0)

    def test_07_pdv_sale_simulation(self):
        """Seção 14: Simulação de venda PDV dando baixa automática em estoque."""
        product = self.db.query(Product).filter(Product.stock.has(Stock.quantity > 5)).first()
        initial_qty = product.stock.quantity

        res = pdv_service.process_pdv_sale(self.db, {
            "sale_document": "CUPOM-TESTE-999",
            "terminal_id": "CAIXA-01",
            "items": [{"product_id": product.id, "quantity": 2.0, "unit_price": product.price.sale_price}]
        }, user_name="Operador PDV")

        self.assertTrue(res["success"])
        self.db.refresh(product)
        self.assertEqual(product.stock.quantity, initial_qty - 2.0)

if __name__ == "__main__":
    unittest.main(verbosity=2)
