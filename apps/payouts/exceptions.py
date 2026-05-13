"""Custom exceptions for payouts bank integration."""

from django.utils.translation import gettext_lazy as _


class PayoutError(Exception):
    """Base exception for all payout-related errors."""
    pass


class BankError(PayoutError):
    """Base exception for bank-related errors."""
    pass


class InsufficientFundsError(BankError):
    """Raised when the account has insufficient funds for the transfer."""
    pass


class AccountNotFoundError(BankError):
    """Raised when the specified account number is not found."""
    pass


class BankConnectionError(BankError):
    """Raised when there is a problem connecting to the bank API."""
    pass
