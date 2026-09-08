import os
from datetime import datetime, timezone
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import (
    create_engine, Column, Integer, String, Float, Boolean, 
    DateTime, ForeignKey, Text, JSON, Index, CheckConstraint
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, scoped_session

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()

def get_engine():
    global DATABASE_URL
    if not DATABASE_URL:
        local_db_path = os.path.join(os.path.dirname(__file__), "contru_estoque.db")
        db_uri = f"sqlite:///{local_db_path}"
        return create_engine(
            db_uri, 
            connect_args={"check_same_thread": False}, 
            echo=False
        )
    else:
        db_uri = DATABASE_URL
        if db_uri.startswith("postgres://"):
            db_uri = db_uri.replace("postgres://", "postgresql+psycopg2://", 1)
        elif db_uri.startswith("postgresql://") and not db_uri.startswith("postgresql+psycopg2://"):
            db_uri = db_uri.replace("postgresql://", "postgresql+psycopg2://", 1)
        
        return create_engine(
            db_uri,
            pool_pre_ping=True,
            pool_recycle=300,
            pool_size=10,
            max_overflow=20,
            echo=False
        )

engine = get_engine()
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
Base = declarative_base()

def utc_now():
    return datetime.now(timezone.utc)

# ---------------------------------------------------------------------------
# 1. ROLES & USERS (Perfis e Usuários com Senha Criptografada)
# ---------------------------------------------------------------------------
class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False) # admin, manager, stockist, viewer, financial
    display_name = Column(String(100), nullable=False)
    description = Column(String(255), nullable=True)
    permissions = Column(JSON, default=list)
    created_at = Column(DateTime, default=utc_now)

    users = relationship("User", back_populates="role")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "permissions": self.permissions or []
        }

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(120), nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=True)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    avatar = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    last_login_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    role = relationship("Role", back_populates="users")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role_id": self.role_id,
            "role": self.role.to_dict() if self.role else None,
            "avatar": self.avatar,
            "is_active": self.is_active,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

# ---------------------------------------------------------------------------
# 2. CATEGORIES, LOCATIONS & UNITS (Estruturas de Apoio)
# ---------------------------------------------------------------------------
class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(String(255), nullable=True)
    icon = Column(String(50), default="tag")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utc_now)

    products = relationship("Product", back_populates="category")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "icon": self.icon,
            "is_active": self.is_active
        }

class Location(Base):
    __tablename__ = "locations"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)
    type = Column(String(50), default="Almoxarifado")
    description = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utc_now)

    products = relationship("Product", back_populates="location")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "description": self.description,
            "is_active": self.is_active
        }

class Unit(Base):
    __tablename__ = "units"
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(10), unique=True, nullable=False)
    name = Column(String(50), nullable=False)

    def to_dict(self):
        return {"id": self.id, "code": self.code, "name": self.name}

# ---------------------------------------------------------------------------
# 3. PRODUCTS, STOCK & PRICES (Itens, Saldo e Preços)
# ---------------------------------------------------------------------------
class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(180), nullable=False, index=True)
    description = Column(Text, nullable=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    subcategory = Column(String(100), nullable=True)
    unit_id = Column(Integer, ForeignKey("units.id"), nullable=False)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=True)
    min_stock = Column(Float, default=10.0, nullable=False)
    max_stock = Column(Float, default=100.0, nullable=False)
    image_url = Column(String(500), nullable=True)
    pdv_code = Column(String(50), nullable=True, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    category = relationship("Category", back_populates="products")
    location = relationship("Location", back_populates="products")
    unit = relationship("Unit")
    stock = relationship("Stock", uselist=False, back_populates="product", cascade="all, delete-orphan")
    price = relationship("Price", uselist=False, back_populates="product", cascade="all, delete-orphan")
    movements = relationship("StockMovement", back_populates="product")
    price_histories = relationship("PriceHistory", back_populates="product")

    def to_dict(self, include_details=True):
        stock_qty = self.stock.quantity if self.stock else 0.0
        cost_p = self.price.cost_price if self.price else 0.0
        sale_p = self.price.sale_price if self.price else 0.0
        
        if stock_qty <= 0:
            stock_status = "SEM_ESTOQUE"
        elif stock_qty <= self.min_stock:
            stock_status = "ESTOQUE_BAIXO"
        elif stock_qty >= self.max_stock:
            stock_status = "EXCEDENTE"
        else:
            stock_status = "NORMAL"

        margin_percent = 0.0
        if cost_p > 0:
            margin_percent = round(((sale_p - cost_p) / cost_p) * 100, 1)

        suggested_restock = max(0.0, self.max_stock - stock_qty) if stock_qty <= self.min_stock else 0.0

        has_recent_price_change = False
        if self.price_histories:
            sorted_prices = sorted(self.price_histories, key=lambda x: x.created_at, reverse=True)
            if sorted_prices:
                last_p = sorted_prices[0]
                days_diff = (datetime.now(timezone.utc) - last_p.created_at.replace(tzinfo=timezone.utc)).days if last_p.created_at else 999
                if days_diff <= 30:
                    has_recent_price_change = True

        data = {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "description": self.description,
            "category_id": self.category_id,
            "category_name": self.category.name if self.category else "",
            "subcategory": self.subcategory,
            "unit_id": self.unit_id,
            "unit_code": self.unit.code if self.unit else "UN",
            "location_id": self.location_id,
            "location_name": self.location.name if self.location else "",
            "min_stock": self.min_stock,
            "max_stock": self.max_stock,
            "stock_quantity": stock_qty,
            "stock_status": stock_status,
            "suggested_restock": suggested_restock,
            "cost_price": cost_p,
            "sale_price": sale_p,
            "margin_percent": margin_percent,
            "stock_value": round(stock_qty * cost_p, 2),
            "image_url": self.image_url,
            "pdv_code": self.pdv_code,
            "is_active": self.is_active,
            "has_recent_price_change": has_recent_price_change,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
        return data

class Stock(Base):
    __tablename__ = "stock"
    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"), unique=True, nullable=False)
    quantity = Column(Float, default=0.0, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    product = relationship("Product", back_populates="stock")

class Price(Base):
    __tablename__ = "prices"
    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"), unique=True, nullable=False)
    cost_price = Column(Float, default=0.0, nullable=False)
    sale_price = Column(Float, default=0.0, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    product = relationship("Product", back_populates="price")

# ---------------------------------------------------------------------------
# 4. MOVIMENTAÇÕES E AJUSTES DE ESTOQUE (Imutáveis)
# ---------------------------------------------------------------------------
class StockMovement(Base):
    __tablename__ = "stock_movements"
    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    movement_type = Column(String(30), nullable=False, index=True)
    quantity = Column(Float, nullable=False)
    previous_balance = Column(Float, nullable=False)
    new_balance = Column(Float, nullable=False)
    unit_price = Column(Float, default=0.0)
    total_value = Column(Float, default=0.0)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    user_name = Column(String(120), nullable=True)
    origin_destination = Column(String(150), nullable=True)
    document_ref = Column(String(100), nullable=True)
    reason_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, index=True)

    product = relationship("Product", back_populates="movements")
    user = relationship("User")

    def to_dict(self):
        return {
            "id": self.id,
            "product_id": self.product_id,
            "product_code": self.product.code if self.product else "",
            "product_name": self.product.name if self.product else "",
            "category_name": self.product.category.name if self.product and self.product.category else "",
            "unit_code": self.product.unit.code if self.product and self.product.unit else "UN",
            "movement_type": self.movement_type,
            "quantity": self.quantity,
            "previous_balance": self.previous_balance,
            "new_balance": self.new_balance,
            "unit_price": self.unit_price,
            "total_value": self.total_value,
            "user_id": self.user_id,
            "user_name": self.user_name or (self.user.name if self.user else "Sistema"),
            "origin_destination": self.origin_destination,
            "document_ref": self.document_ref,
            "reason_notes": self.reason_notes,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class StockAdjustment(Base):
    __tablename__ = "stock_adjustments"
    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    movement_id = Column(Integer, ForeignKey("stock_movements.id"), nullable=False)
    previous_quantity = Column(Float, nullable=False)
    new_quantity = Column(Float, nullable=False)
    diff_quantity = Column(Float, nullable=False)
    justification = Column(Text, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=utc_now)

# ---------------------------------------------------------------------------
# 5. HISTÓRICO DE PREÇOS
# ---------------------------------------------------------------------------
class PriceHistory(Base):
    __tablename__ = "price_history"
    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    previous_cost_price = Column(Float, default=0.0)
    new_cost_price = Column(Float, default=0.0)
    previous_sale_price = Column(Float, default=0.0)
    new_sale_price = Column(Float, default=0.0)
    reason = Column(String(255), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    user_name = Column(String(120), nullable=True)
    created_at = Column(DateTime, default=utc_now, index=True)

    product = relationship("Product", back_populates="price_histories")

    def to_dict(self):
        return {
            "id": self.id,
            "product_id": self.product_id,
            "product_name": self.product.name if self.product else "",
            "previous_cost_price": self.previous_cost_price,
            "new_cost_price": self.new_cost_price,
            "previous_sale_price": self.previous_sale_price,
            "new_sale_price": self.new_sale_price,
            "cost_diff": round(self.new_cost_price - self.previous_cost_price, 2),
            "sale_diff": round(self.new_sale_price - self.previous_sale_price, 2),
            "reason": self.reason,
            "user_name": self.user_name or "Sistema",
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

# ---------------------------------------------------------------------------
# 6. INVENTÁRIO
# ---------------------------------------------------------------------------
class Inventory(Base):
    __tablename__ = "inventories"
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(50), unique=True, nullable=False)
    title = Column(String(150), nullable=False)
    type = Column(String(50), default="COMPLETO")
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=True)
    status = Column(String(30), default="EM_ANDAMENTO")
    notes = Column(Text, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    user_name = Column(String(120), nullable=True)
    started_at = Column(DateTime, default=utc_now)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    items = relationship("InventoryItem", back_populates="inventory", cascade="all, delete-orphan")
    category = relationship("Category")
    location = relationship("Location")

    def to_dict(self, include_items=False):
        total_items = len(self.items) if self.items else 0
        total_diff_qty = sum(item.diff_quantity for item in self.items) if self.items else 0.0
        total_diff_val = sum(item.diff_value for item in self.items) if self.items else 0.0
        
        data = {
            "id": self.id,
            "code": self.code,
            "title": self.title,
            "type": self.type,
            "category_name": self.category.name if self.category else "Todas",
            "location_name": self.location.name if self.location else "Todas",
            "status": self.status,
            "notes": self.notes,
            "user_name": self.user_name or "Sistema",
            "total_items": total_items,
            "total_diff_quantity": total_diff_qty,
            "total_diff_value": round(total_diff_val, 2),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
        if include_items:
            data["items"] = [item.to_dict() for item in self.items]
        return data

class InventoryItem(Base):
    __tablename__ = "inventory_items"
    id = Column(Integer, primary_key=True, autoincrement=True)
    inventory_id = Column(Integer, ForeignKey("inventories.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    system_quantity = Column(Float, default=0.0, nullable=False)
    counted_quantity = Column(Float, default=0.0, nullable=False)
    diff_quantity = Column(Float, default=0.0, nullable=False)
    diff_percent = Column(Float, default=0.0, nullable=False)
    cost_price = Column(Float, default=0.0, nullable=False)
    diff_value = Column(Float, default=0.0, nullable=False)
    notes = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=utc_now)

    inventory = relationship("Inventory", back_populates="items")
    product = relationship("Product")

    def to_dict(self):
        return {
            "id": self.id,
            "inventory_id": self.inventory_id,
            "product_id": self.product_id,
            "product_code": self.product.code if self.product else "",
            "product_name": self.product.name if self.product else "",
            "category_name": self.product.category.name if self.product and self.product.category else "",
            "unit_code": self.product.unit.code if self.product and self.product.unit else "UN",
            "system_quantity": self.system_quantity,
            "counted_quantity": self.counted_quantity,
            "diff_quantity": self.diff_quantity,
            "diff_percent": self.diff_percent,
            "cost_price": self.cost_price,
            "diff_value": self.diff_value,
            "notes": self.notes
        }

# ---------------------------------------------------------------------------
# 7. AUDITORIA COMPLETA (Imutável)
# ---------------------------------------------------------------------------
class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    user_name = Column(String(120), nullable=True)
    action = Column(String(50), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(String(50), nullable=True)
    description = Column(String(255), nullable=False)
    before_data = Column(JSON, nullable=True)
    after_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=utc_now, index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "user_name": self.user_name or "Sistema",
            "action": self.action,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "description": self.description,
            "before_data": self.before_data,
            "after_data": self.after_data,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

# ---------------------------------------------------------------------------
# 8. ESTRUTURA DE INTEGRAÇÃO COM PDV
# ---------------------------------------------------------------------------
class PDVIntegration(Base):
    __tablename__ = "pdv_integrations"
    id = Column(Integer, primary_key=True, autoincrement=True)
    pdv_system_name = Column(String(100), default="PDV Frente de Caixa")
    status = Column(String(50), default="AGUARDANDO_CONEXAO")
    last_sync_at = Column(DateTime, nullable=True)
    pending_items_count = Column(Integer, default=0)
    pending_movements_count = Column(Integer, default=0)
    api_endpoint = Column(String(255), default="/api/pdv/sync")
    webhook_url = Column(String(255), nullable=True)
    config_json = Column(JSON, default=dict)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    def to_dict(self):
        return {
            "id": self.id,
            "pdv_system_name": self.pdv_system_name,
            "status": self.status,
            "last_sync_at": self.last_sync_at.isoformat() if self.last_sync_at else None,
            "pending_items_count": self.pending_items_count,
            "pending_movements_count": self.pending_movements_count,
            "api_endpoint": self.api_endpoint,
            "webhook_url": self.webhook_url,
            "config": self.config_json or {}
        }

# ---------------------------------------------------------------------------
# 9. CONFIGURAÇÕES CORPORATIVAS DA EMPRESA (CompanySetting)
# ---------------------------------------------------------------------------
class CompanySetting(Base):
    __tablename__ = "company_settings"
    id = Column(Integer, primary_key=True, autoincrement=True)
    company_name = Column(String(180), default="CONTRU MATERIAIS DE CONSTRUÇÃO E INCLUSÃO LTDA")
    trade_name = Column(String(100), default="CONTRU ESTOQUE")
    cnpj = Column(String(25), default="42.891.023/0001-85")
    state_reg = Column(String(25), default="148.902.110.114")
    email = Column(String(120), default="suprimentos@contruestoque.com.br")
    phone = Column(String(30), default="(11) 3450-8900")
    address = Column(String(255), default="Av. dos Estados, 4500 - Galpão 04 - São Paulo/SP")
    allow_negative_stock = Column(Boolean, default=False)
    default_margin_percent = Column(Float, default=45.0)
    inventory_interval_days = Column(Integer, default=90)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    def to_dict(self):
        return {
            "company_name": self.company_name,
            "trade_name": self.trade_name,
            "cnpj": self.cnpj,
            "state_reg": self.state_reg,
            "email": self.email,
            "phone": self.phone,
            "address": self.address,
            "allow_negative_stock": self.allow_negative_stock,
            "default_margin_percent": self.default_margin_percent,
            "inventory_interval_days": self.inventory_interval_days,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

def init_db():
    Base.metadata.create_all(bind=engine)
    print("Tabelas criadas com sucesso no banco de dados.")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
