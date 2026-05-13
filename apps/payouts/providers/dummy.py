"""Dummy bank provider for unit testing.

Always succeeds regardless of input. Use in tests only.
"""

from decimal import Decimal
from typing import Dict, Any

from .base import BaseBankProvider


class DummyProvider(BaseBankProvider):
    """
    Dummy provider that always returns success.

    - transfer: always succeeds with a deterministic tx_id
    - validate_account: always returns True
    - get_balance: returns a very high balance (1,000,000.00)
    """

    def transfer(
        self,
        amount: Decimal,
        account_number: str,
        reference: str,
        **kwargs: Any
    ) -> Dict[str, Any]:
        return {
            'success': True,
            'tx_id': f"DUMMY-TX-{reference}",
            'bank_ref': f"DUMMY-{reference}",
            'error': '',
        }

    def validate_account(self, account_number: str, rut: str = '') -> bool:
        return True

    def get_balance(self, account_number: str) -> Decimal:
        return Decimal('1000000.00')
