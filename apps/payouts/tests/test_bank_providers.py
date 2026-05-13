"""Tests for bank provider implementations and factory."""

from decimal import Decimal
from unittest.mock import patch, MagicMock
import pytest

from apps.payouts.exceptions import (
    InsufficientFundsError,
    AccountNotFoundError,
    BankConnectionError,
)
from apps.payouts.factory import BankProviderFactory, BANK_MAP
from apps.payouts.providers.base import BaseBankProvider
from apps.payouts.providers.dummy import DummyProvider
from apps.payouts.providers.produbanco import ProdubancoProvider
from apps.payouts.providers.pichincha import PichinchaProvider
from apps.payouts.providers.guayaquil import GuayaquilProvider


# ─── Factory Tests ─────────────────────────────────────────────────────

def test_factory_unknown_bank_raises():
    """Factory raises ValueError for unsupported bank codes."""
    with pytest.raises(ValueError, match="Banco no soportado"):
        BankProviderFactory('unknown_bank')


def test_factory_produbanco_returns_instance():
    """Factory returns ProdubancoProvider instance."""
    provider = BankProviderFactory('produbanco', api_key='test', api_secret='secret')
    assert isinstance(provider, ProdubancoProvider)


def test_factory_pichincha_returns_instance():
    """Factory returns PichinchaProvider instance."""
    provider = BankProviderFactory('pichincha', api_key='test')
    assert isinstance(provider, PichinchaProvider)


def test_factory_guayaquil_returns_instance():
    """Factory returns GuayaquilProvider instance."""
    provider = BankProviderFactory('guayaquil', api_key='test')
    assert isinstance(provider, GuayaquilProvider)


def test_factory_dummy_returns_instance():
    """Factory returns DummyProvider instance."""
    provider = BankProviderFactory('dummy', api_key='test')
    assert isinstance(provider, DummyProvider)


def test_factory_case_insensitive():
    """Factory is case-insensitive for bank codes."""
    provider = BankProviderFactory('PRODUBANCO', api_key='test')
    assert isinstance(provider, ProdubancoProvider)


def test_bank_map_contains_all_providers():
    """BANK_MAP includes all expected providers."""
    expected = {'produbanco', 'pichincha', 'guayaquil', 'dummy'}
    assert set(BANK_MAP.keys()) == expected


# ─── DummyProvider Tests ────────────────────────────────────────────────

def test_dummy_provider_transfer_success():
    """DummyProvider.transfer returns success."""
    provider = DummyProvider(api_key='test')
    result = provider.transfer(
        amount=Decimal('100.00'),
        account_number='1234567890',
        reference='REF-001'
    )
    assert result['success'] is True
    assert 'tx_id' in result
    assert result['tx_id'] == 'DUMMY-TX-REF-001'
    assert result['error'] == ''


def test_dummy_provider_validate_account_always_true():
    """DummyProvider.validate_account always returns True."""
    provider = DummyProvider(api_key='test')
    assert provider.validate_account('1234567890') is True
    assert provider.validate_account('1234567890', rut='0912345678') is True


def test_dummy_provider_get_balance_high():
    """DummyProvider.get_balance returns a high mock balance."""
    provider = DummyProvider(api_key='test')
    balance = provider.get_balance('1234567890')
    assert balance == Decimal('1000000.00')


# ─── ProdubancoProvider Tests ──────────────────────────────────────────

def test_produbanco_initialization_with_sandbox():
    """ProdubancoProvider initializes correctly in sandbox mode."""
    provider = ProdubancoProvider(
        api_key='test_key',
        api_secret='test_secret',
        sandbox=True,
    )
    assert provider.sandbox is True
    assert 'sandbox.api.produbanco' in provider.base_url


def test_produbanco_initialization_production():
    """ProdubancoProvider initializes correctly in production mode."""
    provider = ProdubancoProvider(
        api_key='test_key',
        api_secret='test_secret',
        sandbox=False,
    )
    assert provider.sandbox is False
    assert 'api.produbanco' in provider.base_url
    assert 'sandbox' not in provider.base_url


def test_produbanco_transfer_success():
    """ProdubancoProvider.transfer handles successful response."""
    provider = ProdubancoProvider(api_key='test', api_secret='secret', sandbox=True)
    with patch.object(provider, 'session') as mock_session:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'transaction_id': 'TX-123456',
            'bank_reference': 'BANK-REF-789',
        }
        mock_session.post.return_value = mock_response

        result = provider.transfer(
            amount=Decimal('500.00'),
            account_number='1234567890',
            reference='PAY-001',
            currency='USD',
        )

        assert result['success'] is True
        assert result['tx_id'] == 'TX-123456'
        assert result['bank_ref'] == 'BANK-REF-789'
        assert result['error'] == ''


def test_produbanco_transfer_insufficient_funds_raises():
    """ProdubancoProvider.transfer raises InsufficientFundsError on 400 insufficient."""
    provider = ProdubancoProvider(api_key='test', api_secret='secret', sandbox=True)
    with patch.object(provider, 'session') as mock_session:
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            'error': {'message': 'Insufficient funds in account', 'code': 'INSUFFICIENT'}
        }
        mock_session.post.return_value = mock_response

        with pytest.raises(InsufficientFundsError, match="Insufficient funds"):
            provider.transfer(
                amount=Decimal('5000.00'),
                account_number='1234567890',
                reference='PAY-002',
            )


def test_produbanco_transfer_account_not_found_raises():
    """ProdubancoProvider.transfer raises AccountNotFoundError on 404."""
    provider = ProdubancoProvider(api_key='test', api_secret='secret', sandbox=True)
    with patch.object(provider, 'session') as mock_session:
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.json.return_value = {
            'error': {'message': 'Account not found', 'code': 'NOT_FOUND'}
        }
        mock_session.post.return_value = mock_response

        with pytest.raises(AccountNotFoundError, match="Account not found"):
            provider.transfer(
                amount=Decimal('100.00'),
                account_number='9999999999',
                reference='PAY-003',
            )


def test_produbanco_transfer_connection_error_raises():
    """ProdubancoProvider.transfer raises BankConnectionError on network failure."""
    provider = ProdubancoProvider(api_key='test', api_secret='secret', sandbox=True)
    with patch.object(provider, 'session') as mock_session:
        import requests
        mock_session.post.side_effect = requests.RequestException("Connection timeout")

        with pytest.raises(BankConnectionError, match="Connection failed"):
            provider.transfer(
                amount=Decimal('100.00'),
                account_number='1234567890',
                reference='PAY-004',
            )


def test_produbanco_validate_account_success():
    """ProdubancoProvider.validate_account returns True on valid account."""
    provider = ProdubancoProvider(api_key='test', api_secret='secret', sandbox=True)
    with patch.object(provider, 'session') as mock_session:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'valid': True}
        mock_session.get.return_value = mock_response

        result = provider.validate_account('1234567890', rut='0912345678')

        assert result is True


def test_produbanco_validate_account_not_found_raises():
    """ProdubancoProvider.validate_account raises AccountNotFoundError on 404."""
    provider = ProdubancoProvider(api_key='test', api_secret='secret', sandbox=True)
    with patch.object(provider, 'session') as mock_session:
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.json.return_value = {
            'error': {'message': 'Account not found', 'code': 'NOT_FOUND'}
        }
        mock_session.get.return_value = mock_response

        with pytest.raises(AccountNotFoundError, match="Account not found"):
            provider.validate_account('9999999999')


def test_produbanco_get_balance_success():
    """ProdubancoProvider.get_balance returns correct Decimal."""
    provider = ProdubancoProvider(api_key='test', api_secret='secret', sandbox=True)
    with patch.object(provider, 'session') as mock_session:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'available_balance': '2500.75'}
        mock_session.get.return_value = mock_response

        balance = provider.get_balance('1234567890')

        assert balance == Decimal('2500.75')


def test_produbanco_headers_include_auth():
    """ProdubancoProvider._headers includes correct auth headers."""
    provider = ProdubancoProvider(api_key='mykey', api_secret='mysecret', sandbox=True)
    headers = provider._headers()

    assert headers['Authorization'] == 'Bearer mykey'
    assert headers['X-API-Secret'] == 'mysecret'
    assert headers['Content-Type'] == 'application/json'


def test_produbanco_close_calls_session_close():
    """ProdubancoProvider.close() closes the HTTP session."""
    provider = ProdubancoProvider(api_key='test', api_secret='secret', sandbox=True)
    mock_session = MagicMock()
    provider.session = mock_session

    provider.close()
    mock_session.close.assert_called_once()


# ─── PichinchaProvider Tests ───────────────────────────────────────────

def test_pichincha_transfer_success():
    """PichinchaProvider.transfer returns success."""
    provider = PichinchaProvider(api_key='test')
    result = provider.transfer(
        amount=Decimal('200.00'),
        account_number='1234567890',
        reference='REF-PICH-001',
    )
    assert result['success'] is True
    assert 'MOCK-PICHINCHA' in result['tx_id']
    assert result['error'] == ''


def test_pichincha_validate_account_always_true():
    """PichinchaProvider.validate_account always returns True."""
    provider = PichinchaProvider(api_key='test')
    assert provider.validate_account('any_account') is True
    assert provider.validate_account('any_account', rut='0912345678') is True


def test_pichincha_get_balance_fixed():
    """PichinchaProvider.get_balance returns fixed mock balance."""
    provider = PichinchaProvider(api_key='test')
    balance = provider.get_balance('any_account')
    assert balance == Decimal('10000.00')


# ─── GuayaquilProvider Tests ───────────────────────────────────────────

def test_guayaquil_transfer_success():
    """GuayaquilProvider.transfer returns success."""
    provider = GuayaquilProvider(api_key='test')
    result = provider.transfer(
        amount=Decimal('300.00'),
        account_number='1234567890',
        reference='REF-GUAY-001',
    )
    assert result['success'] is True
    assert 'MOCK-GUAYAQUIL' in result['tx_id']
    assert result['error'] == ''


def test_guayaquil_validate_account_always_true():
    """GuayaquilProvider.validate_account always returns True."""
    provider = GuayaquilProvider(api_key='test')
    assert provider.validate_account('any_account') is True


def test_guayaquil_get_balance_fixed():
    """GuayaquilProvider.get_balance returns fixed mock balance."""
    provider = GuayaquilProvider(api_key='test')
    balance = provider.get_balance('any_account')
    assert balance == Decimal('10000.00')


# ─── BaseBankProvider Abstract Methods ─────────────────────────────────

def test_base_bank_provider_is_abstract():
    """BaseBankProvider cannot be instantiated directly."""
    with pytest.raises(TypeError):
        BaseBankProvider(api_key='test')


def test_dummy_provider_is_concrete():
    """DummyProvider is a concrete implementation."""
    provider = DummyProvider(api_key='test')
    assert isinstance(provider, BaseBankProvider)
    # Verify all abstract methods are implemented
    assert hasattr(provider, 'transfer')
    assert hasattr(provider, 'validate_account')
    assert hasattr(provider, 'get_balance')
