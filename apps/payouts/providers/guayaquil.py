"""Banco Guayaquil provider (mock implementation).

Real REST API integration not implemented yet. This mock is suitable
for development and testing.
"""

from decimal import Decimal
from typing import Dict, Any
import logging

from .base import BaseBankProvider

logger = logging.getLogger('payouts.banks.guayaquil')


class GuayaquilProvider(BaseBankProvider):
    """
    Mock implementation for Banco Guayaquil.

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
                'bank': 'guayaquil',
                'amount': str(amount),
                'account': account_number,
                'reference': reference,
            }
        )
        return {
            'success': True,
            'tx_id': f"MOCK-GUAYAQUIL-{reference}",
            'bank_ref': f"GUAY-{reference}",
            'error': '',
        }

    def validate_account(self, account_number: str, rut: str = '') -> bool:
        logger.info(
            "validate_account_mock",
            extra={'bank': 'guayaquil', 'account': account_number, 'rut': rut},
        )
        return True

    def get_balance(self, account_number: str) -> Decimal:
        logger.info(
            "get_balance_mock",
            extra={'bank': 'guayaquil', 'account': account_number},
        )
        return Decimal('10000.00')
