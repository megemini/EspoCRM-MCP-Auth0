"""Tests for src/config.py."""

from __future__ import annotations

import pytest

from src.config import Config, EspoCRMConfig, FGAConfig, OAuthConfig


class TestEspoCRMConfig:
    def test_default_values(self):
        cfg = EspoCRMConfig(url="http://crm", api_key="key123")
        assert cfg.auth_method == "apikey"
        assert cfg.timeout == 30
        assert cfg.secret_key is None

    def test_custom_values(self):
        cfg = EspoCRMConfig(
            url="http://crm",
            api_key="key123",
            secret_key="secret",
            auth_method="hmac",
            timeout=60,
        )
        assert cfg.auth_method == "hmac"
        assert cfg.timeout == 60


class TestFGAConfig:
    def test_defaults(self):
        cfg = FGAConfig(
            api_url="https://fga.dev",
            store_id="s1",
            client_id="c1",
            client_secret="cs",
        )
        assert cfg.enabled is True
        assert cfg.api_issuer == "auth.fga.dev"
        assert cfg.authorization_model_id is None

    def test_all_fields(self):
        cfg = FGAConfig(
            api_url="https://fga.dev",
            store_id="s1",
            client_id="c1",
            client_secret="cs",
            authorization_model_id="model-1",
            api_issuer="custom.issuer.com",
            api_audience="https://api.fga.dev/",
            enabled=True,
        )
        assert cfg.authorization_model_id == "model-1"


class TestOAuthConfig:
    def test_defaults(self):
        cfg = OAuthConfig(client_id="cid", client_secret="csec", secret_key="sk")
        assert cfg.enabled is True


class TestConfigFromEnv:
    def test_missing_required_vars(self, monkeypatch):
        for key in ["AUTH0_DOMAIN", "AUTH0_AUDIENCE", "ESPOCRM_URL", "ESPOCRM_API_KEY"]:
            monkeypatch.delenv(key, raising=False)
        with pytest.raises(ValueError, match="AUTH0_DOMAIN"):
            Config.from_env()

    def test_minimal_config(self, monkeypatch):
        env = {
            "AUTH0_DOMAIN": "test.auth0.com",
            "AUTH0_AUDIENCE": "https://api.test.com",
            "ESPOCRM_URL": "http://localhost:8080",
            "ESPOCRM_API_KEY": "test-key",
        }
        for k, v in env.items():
            monkeypatch.setenv(k, v)
        monkeypatch.setenv("FGA_ENABLED", "false")
        monkeypatch.setenv("OAUTH_ENABLED", "false")

        config = Config.from_env()
        assert config.auth0_domain == "test.auth0.com"
        assert config.espocrm.url == "http://localhost:8080"
        assert config.fga is None
        assert config.oauth is None

    def test_fga_enabled_requires_all_vars(self, monkeypatch):
        base = {
            "AUTH0_DOMAIN": "t.auth0.com",
            "AUTH0_AUDIENCE": "https://api.t.com",
            "ESPOCRM_URL": "http://c:8080",
            "ESPOCRM_API_KEY": "k",
        }
        for k, v in base.items():
            monkeypatch.setenv(k, v)
        monkeypatch.setenv("FGA_ENABLED", "true")
        monkeypatch.setenv("FGA_API_URL", "https://fga.dev")
        monkeypatch.setenv("FGA_STORE_ID", "s1")
        monkeypatch.setenv("FGA_CLIENT_ID", "c1")
        with pytest.raises(ValueError, match="FGA.*missing"):
            Config.from_env()

    def test_oauth_enabled_requires_all_vars(self, monkeypatch):
        base = {
            "AUTH0_DOMAIN": "t.auth0.com",
            "AUTH0_AUDIENCE": "https://api.t.com",
            "ESPOCRM_URL": "http://c:8080",
            "ESPOCRM_API_KEY": "k",
        }
        for k, v in base.items():
            monkeypatch.setenv(k, v)
        monkeypatch.setenv("FGA_ENABLED", "false")
        monkeypatch.setenv("OAUTH_ENABLED", "true")
        monkeypatch.setenv("OAUTH_CLIENT_ID", "cid")
        monkeypatch.setenv("OAUTH_CLIENT_SECRET", "csec")
        with pytest.raises(ValueError, match="OAuth.*missing"):
            Config.from_env()

    def test_invalid_auth_method(self, monkeypatch):
        base = {
            "AUTH0_DOMAIN": "t.auth0.com",
            "AUTH0_AUDIENCE": "https://api.t.com",
            "ESPOCRM_URL": "http://c:8080",
            "ESPOCRM_API_KEY": "k",
        }
        for k, v in base.items():
            monkeypatch.setenv(k, v)
        monkeypatch.setenv("FGA_ENABLED", "false")
        monkeypatch.setenv("OAUTH_ENABLED", "false")
        monkeypatch.setenv("ESPOCRM_AUTH_METHOD", "invalid")
        with pytest.raises(ValueError, match="Invalid ESPOCRM_AUTH_METHOD"):
            Config.from_env()
