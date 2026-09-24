import pytest

from app.core.config import Settings


def test_production_service_accounts_require_explicit_session_secret():
    with pytest.raises(ValueError, match="SESSION_SECRET"):
        Settings(
            environment="production",
            database_url="postgresql+psycopg://db.example.test/monitor",
            cors_origins="https://monitor.example.test",
            require_api_key=True,
            auth_mode="service_accounts",
        )


def test_production_service_account_contract_is_valid_with_explicit_secret():
    settings = Settings(
        environment="production",
        database_url="postgresql+psycopg://db.example.test/monitor",
        cors_origins="https://monitor.example.test",
        require_api_key=True,
        auth_mode="service_accounts",
        session_secret="x" * 48,
    )
    assert settings.auth_mode == "service_accounts"


def test_production_rejects_sqlite_database():
    with pytest.raises(ValueError, match="server database"):
        Settings(
            environment="production",
            database_url="sqlite:///monitor.db",
            cors_origins="https://monitor.example.test",
            require_api_key=True,
            auth_mode="legacy_api_key",
            api_key="x" * 32,
        )
