"""Factory for creating bank provider instances."""

from typing import Any

from .providers import (
    BaseBankProvider,
    ProdubancoProvider,
    PichinchaProvider,
    GuayaquilProvider,
    DummyProvider,
)

BANK_MAP = {
    'produbanco': ProdubancoProvider,
    'pichincha': PichinchaProvider,
    'guayaquil': GuayaquilProvider,
    'dummy': DummyProvider,
}


def BankProviderFactory(bank_code: str, **credentials: Any) -> BaseBankProvider:
    """
    Factory function to instantiate a bank provider.

    Args:
        bank_code: Bank identifier (e.g., 'produbanco', 'pichincha')
        **credentials: Provider-specific credentials (api_key, api_secret, etc.)

    Returns:
        BaseBankProvider: Instantiated provider

    Raises:
        ValueError: If the bank_code is not supported
    """
    try:
        provider_cls = BANK_MAP[bank_code.lower()]
    except KeyError:
        raise ValueError(f"Banco no soportado: {bank_code}")

    return provider_cls(**credentials)
