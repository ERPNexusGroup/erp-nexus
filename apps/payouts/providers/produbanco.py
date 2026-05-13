"""Produbanco bank provider implementation (REST API with retry logic)."""

import json
from decimal import Decimal
from typing import Dict, Any, Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import logging

from .base import BaseBankProvider
from ..exceptions import (
    InsufficientFundsError,
    AccountNotFoundError,
    BankConnectionError,
)

logger = logging.getLogger('payouts.banks.produbanco')


class ProdubancoProvider(BaseBankProvider):
    """
    Produbanco REST API provider.

    Supports sandbox and production modes. Uses retry logic for resilience.
    """

    def __init__(self, api_key: str, api_secret: str = '', **kwargs):
        super().__init__(api_key, api_secret, **kwargs)

        # Determine base URL from sandbox flag
        if self.sandbox:
            self.base_url = kwargs.get('sandbox_url', 'https://sandbox.api.produbanco.com.ec')
        else:
            self.base_url = kwargs.get('production_url', 'https://api.produbanco.com.ec')

        # Configure session with retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=self.retry_attempts,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def _headers(self) -> Dict[str, str]:
        """Build authorization headers."""
        return {
            'Authorization': f'Bearer {self.api_key}',
            'X-API-Secret': self.api_secret,
            'Content-Type': 'application/json',
        }

    def _handle_error_response(self, response: requests.Response, context: str) -> None:
        """
        Parse error responses and raise appropriate exceptions.

        Args:
            response: HTTP response object
            context: Operation context for logging

        Raises:
            InsufficientFundsError: For insufficient funds (400 with 'insufficient')
            AccountNotFoundError: For 404 errors
            BankConnectionError: For other connection/API errors
        """
        try:
            error_data = response.json()
            error_msg = error_data.get('error', {}).get('message', response.text)
            error_code = error_data.get('error', {}).get('code', '')
        except (json.JSONDecodeError, AttributeError):
            error_msg = response.text
            error_code = ''

        logger.warning(
            "bank_error",
            extra={
                'bank': 'produbanco',
                'context': context,
                'status_code': response.status_code,
                'error_code': error_code,
                'error_msg': error_msg[:200],
            }
        )

        if response.status_code == 400 and 'insufficient' in error_msg.lower():
            raise InsufficientFundsError(f"Insufficient funds: {error_msg}")
        elif response.status_code == 404:
            raise AccountNotFoundError(f"Account not found: {error_msg}")
        else:
            raise BankConnectionError(
                f"Bank API error ({response.status_code}): {error_msg}"
            )

    def transfer(
        self,
        amount: Decimal,
        account_number: str,
        reference: str,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Execute a transfer via Produbanco REST API.

        Endpoint: POST /transfers
        """
        url = f"{self.base_url}/transfers"
        payload = {
            'amount': str(amount),
            'account_number': account_number,
            'reference': reference,
            'currency': kwargs.get('currency', 'USD'),
        }

        try:
            response = self.session.post(
                url,
                headers=self._headers(),
                json=payload,
                timeout=self.timeout,
            )

            if response.status_code == 200:
                data = response.json()
                return {
                    'success': True,
                    'tx_id': data.get('transaction_id', ''),
                    'bank_ref': data.get('bank_reference', reference),
                    'error': '',
                }
            else:
                self._handle_error_response(response, 'transfer')

        except requests.RequestException as e:
            logger.error(
                "connection_error",
                extra={'bank': 'produbanco', 'context': 'transfer', 'error': str(e)},
            )
            raise BankConnectionError(f"Connection failed: {e}")

    def validate_account(self, account_number: str, rut: str = '') -> bool:
        """
        Validate account via Produbanco API.

        Endpoint: GET /accounts/{account_number}/validate
        """
        url = f"{self.base_url}/accounts/{account_number}/validate"
        params = {'rut': rut} if rut else {}

        try:
            response = self.session.get(
                url,
                headers=self._headers(),
                params=params,
                timeout=self.timeout,
            )

            if response.status_code == 200:
                data = response.json()
                return data.get('valid', False)
            else:
                self._handle_error_response(response, 'validate_account')

        except requests.RequestException as e:
            logger.error(
                "connection_error",
                extra={'bank': 'produbanco', 'context': 'validate_account', 'error': str(e)},
            )
            raise BankConnectionError(f"Connection failed: {e}")

    def get_balance(self, account_number: str) -> Decimal:
        """
        Get account balance via Produbanco API.

        Endpoint: GET /accounts/{account_number}/balance
        """
        url = f"{self.base_url}/accounts/{account_number}/balance"

        try:
            response = self.session.get(
                url,
                headers=self._headers(),
                timeout=self.timeout,
            )

            if response.status_code == 200:
                data = response.json()
                balance_str = data.get('available_balance', '0')
                return Decimal(balance_str)
            else:
                self._handle_error_response(response, 'get_balance')

        except requests.RequestException as e:
            logger.error(
                "connection_error",
                extra={'bank': 'produbanco', 'context': 'get_balance', 'error': str(e)},
            )
            raise BankConnectionError(f"Connection failed: {e}")

    def close(self) -> None:
        """Close the HTTP session."""
        self.session.close()
