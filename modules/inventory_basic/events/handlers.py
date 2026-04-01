"""
Handlers de eventos para inventory_basic.

Emite:
  - inventory.low_stock → cuando un producto baja del mínimo
  - inventory.movement  → cuando hay un movimiento

Recibe:
  - invoice.created → descuenta stock por facturación
"""
import logging

logger = logging.getLogger(__name__)


def on_invoice_created(payload: dict):
    """Descuenta stock cuando se crea una factura."""
    logger.info(f"Factura creada, descontando stock: {payload}")
    # Lógica para descontar productos de la factura


def on_order_confirmed(payload: dict):
    """Reserva stock cuando se confirma un pedido."""
    logger.info(f"Pedido confirmado, reservando stock: {payload}")
