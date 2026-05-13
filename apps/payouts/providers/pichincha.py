"""Banco Pichincha provider (mock implementation).

Real SOAP/JSON integration is not implemented due to closed documentation.
This is a mock provider suitable for development and testing.
"""

from decimal import Decimal
from typing import Dict, Any
import logging

from .base import BaseBankProvider

logger = logging.getLogger('payouts.banks.pichincha')


class PichinchaProvider(BaseBankProvider):
    """
    Mock implementation for Banco Pichincha.

    Always returns success with a fake transaction ID.
    validate_account() always returns True.
    get_balance() returns a fixed mock balance of 10,000.00.
    """

    def transfer(
        self,
        amount: Decimal,
        account_number: str,
        reference: str,
        **kwargs: Any
    ) -> Dict[str, Any]:
        logger.info(
            "transfer_mock",
            extra={
                'bank': 'pichincha',
                'amount': str(amount),
                'account': account_number,
                'reference': reference,
            }
        )
        # Mock successful transfer
        return {
            'success': True,
            'tx_id': f"MOCK-PICHINCHA-{reference}",
            'bank_ref': f"PICH-{reference}",
            'error': '',
        }

    def validate_account(self, account_number: str, rut: str = '') -> bool:
        logger.info(
            "validate_account_mock",
            extra={'bank': 'pichincha', 'account': account_number, 'rut': rut},
        )
        # Mock: always valid
        return True

    def get_balance(self, account_number: str) -> Decimal:
        logger.info(
            "get_balance_mock",
            extra={'bank': 'pichincha', 'account': account_number},
        )
        # Mock: return a fixed balance
        return Decimal('10000.00')
