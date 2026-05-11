"""API endpoints para inventory_basic."""
from ninja import Router, Schema
from typing import Optional
from decimal import Decimal

router = Router()


class CategoryOut(Schema):
    id: int
    code: str
    name: str
    is_active: bool


class ProductOut(Schema):
    id: int
    sku: str
    name: str
    category: str
    unit_price: float
    stock_quantity: float
    is_low_stock: bool
    is_active: bool


class StockMovementOut(Schema):
    id: int
    product_sku: str
    movement_type: str
    quantity: float
    reference: str
    created_at: str


class StockSummary(Schema):
    total_products: int
    total_stock_value: float
    low_stock_count: int
    categories: int


@router.get("/categories", response=list[CategoryOut])
def list_categories(request):
    """Lista categorías de productos."""
    from inventory_basic.core.models import Category
    qs = Category.objects.filter(is_active=True)
    return [CategoryOut(id=c.id, code=c.code, name=c.name, is_active=c.is_active) for c in qs]


@router.get("/products", response=list[ProductOut])
def list_products(request, category: str = None, low_stock: bool = None):
    """Lista productos con filtros opcionales."""
    from inventory_basic.core.models import Product
    qs = Product.objects.filter(is_active=True).select_related("category")
    if category:
        qs = qs.filter(category__code=category)
    if low_stock is not None:
        if low_stock:
            qs = qs.filter(stock_quantity__lte=models.F("min_stock"))
    return [
        ProductOut(
            id=p.id, sku=p.sku, name=p.name,
            category=p.category.code,
            unit_price=float(p.unit_price),
            stock_quantity=float(p.stock_quantity),
            is_low_stock=p.is_low_stock,
            is_active=p.is_active,
        )
        for p in qs[:100]
    ]


@router.get("/summary", response=StockSummary)
def stock_summary(request):
    """Resumen de inventario."""
    from inventory_basic.core.models import Product, Category
    from django.db.models import F, Sum

    products = Product.objects.filter(is_active=True)
    total_value = products.aggregate(
        total=Sum(F("stock_quantity") * F("unit_price"))
    )["total"] or 0

    return StockSummary(
        total_products=products.count(),
        total_stock_value=float(total_value),
        low_stock_count=products.filter(stock_quantity__lte=F("min_stock")).count(),
        categories=Category.objects.filter(is_active=True).count(),
    )


@router.post("/movements", response=StockMovementOut)
def create_movement(request, product_sku: str, movement_type: str, quantity: float, reference: str = ""):
    """Registra un movimiento de inventario."""
    from inventory_basic.core.models import Product, StockMovement

    product = Product.objects.get(sku=product_sku, is_active=True)
    movement = StockMovement.objects.create(
        product=product,
        movement_type=movement_type,
        quantity=quantity,
        reference=reference,
    )
    return StockMovementOut(
        id=movement.id,
        product_sku=product.sku,
        movement_type=movement.movement_type,
        quantity=float(movement.quantity),
        reference=movement.reference,
        created_at=str(movement.created_at),
    )
