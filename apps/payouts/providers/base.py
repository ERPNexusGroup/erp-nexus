"""Abstract base provider for bank integrations."""

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger('payouts.banks')


class BaseBankProvider(ABC):
    """
    Abstract base class for all bank providers.

    Implementations must provide concrete methods for transfer, validate_account,
    and get_balance. The close() method is optional (default no-op).
    """

    def __init__(self, api_key: str, api_secret: str = '', **kwargs):
        """
        Initialize the bank provider.

        Args:
            api_key: API key or username for authentication
            api_secret: API secret or password (optional)
            **kwargs: Additional provider-specific options (e.g., sandbox, timeout)
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.sandbox = kwargs.get('sandbox', False)
        self.timeout = kwargs.get('timeout', 30)
        self.retry_attempts = kwargs.get('retry_attempts', 3)

    @abstractmethod
    def transfer(
        self,
        amount: Decimal,
        account_number: str,
        reference: str,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Execute a bank transfer.

        Args:
            amount: Amount to transfer (must be positive)
            account_number: Destination account number
            reference: Unique reference for the transaction
            **kwargs: Additional provider-specific parameters

        Returns:
            Dict with keys:
                - success (bool): Whether the transfer succeeded
                - tx_id (str): Transaction ID from the bank
                - bank_ref (str): Bank reference number
                - error (str): Error message if failed

        Raises:
            InsufficientFundsError: If account has insufficient balance
            AccountNotFoundError: If account does not exist
            BankConnectionError: If API call fails after retries
        """
        pass

    @abstractmethod
    def validate_account(self, account_number: str, rut: str = '') -> bool:
        """
        Validate that an account exists and can receive transfers.

        Args:
            account_number: Account number to validate
            rut: RUC or ID number of the account holder (optional)

        Returns:
            True if the account is valid

        Raises:
            AccountNotFoundError: If the account does not exist
            BankConnectionError: If validation fails due to connection issues
        """
        pass

    @abstractmethod
    def get_balance(self, account_number: str) -> Decimal:
        """
        Get the available balance of an account.

        Args:
            account_number: Account number

        Returns:
            Available balance as Decimal

        Raises:
            AccountNotFoundError: If the account does not exist
            BankConnectionError: If API call fails
        """
        pass

    def close(self) -> None:
        """
        Close the provider and clean up resources (e.g., HTTP sessions).

        This is a no-op by default. Override if the provider needs cleanup.
        """
        pass
