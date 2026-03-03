"""Tests for security utilities."""

import os

from nanobot.utils.security import (
    ConfigValidator,
    InputSanitizer,
    RateLimiter,
    SecretManager,
)


class MockConfig:
    """Mock configuration for testing."""

    def __init__(self):
        self.providers = MockProviders()
        self.channels = MockChannels()
        self.tools = MockTools()
        self.gateway = MockGateway()


class MockProviders:
    def __init__(self):
        self.openrouter = MockProviderConfig("sk-or-v1-abcdefghij1234567890")
        self.telegram = MockProviderConfig("")


class MockProviderConfig:
    def __init__(self, api_key):
        self.api_key = api_key


class MockChannels:
    def __init__(self):
        self.telegram = MockTelegramConfig()
        self.email = MockEmailConfig()


class MockTelegramConfig:
    def __init__(self):
        self.enabled = True
        self.token = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
        self.allow_from = []


class MockEmailConfig:
    def __init__(self):
        self.enabled = True
        self.consent_granted = False
        self.imap_password = ""
        self.smtp_password = ""


class MockTools:
    def __init__(self):
        self.restrict_to_workspace = False


class MockGateway:
    def __init__(self):
        self.host = "0.0.0.0"
        self.port = 18790


class TestConfigValidator:
    """Test configuration validation."""

    def test_valid_config(self):
        """Test validation of a valid config."""
        validator = ConfigValidator()
        config = MockConfig()
        config.providers.openrouter.api_key = "sk-or-v1-abcdefghij1234567890"
        config.channels.telegram.allow_from = ["123456"]
        config.tools.restrict_to_workspace = True
        # Fix email config to be valid
        config.channels.email.consent_granted = True
        config.channels.email.imap_password = "password"
        config.channels.email.smtp_password = "password"

        errors = validator.validate(config)

        # Should have warnings but no errors for valid config
        assert len(errors) == 0

    def test_api_key_too_short(self):
        """Test API key length validation."""
        validator = ConfigValidator()
        config = MockConfig()
        config.providers.openrouter.api_key = "short"

        errors = validator.validate(config)

        assert any("too short" in error for error in errors)

    def test_empty_telegram_token(self):
        """Test Telegram token validation."""
        validator = ConfigValidator()
        config = MockConfig()
        config.channels.telegram.token = ""

        errors = validator.validate(config)

        assert any("Telegram" in error and "token" in error for error in errors)

    def test_email_consent_required(self):
        """Test email consent validation."""
        validator = ConfigValidator()
        config = MockConfig()
        config.channels.email.consent_granted = False
        config.channels.email.imap_password = "password"
        config.channels.email.smtp_password = "password"

        errors = validator.validate(config)

        assert any("consent_granted" in error for error in errors)

    def test_workspace_restriction_warning(self):
        """Test workspace restriction warning."""
        validator = ConfigValidator()
        config = MockConfig()
        config.tools.restrict_to_workspace = False

        errors = validator.validate(config)
        warnings = validator.warnings

        assert any("restrict_to_workspace" in warning for warning in warnings)

    def test_gateway_binding_warning(self):
        """Test gateway binding warning."""
        validator = ConfigValidator()
        config = MockConfig()
        config.gateway.host = "0.0.0.0"

        errors = validator.validate(config)
        warnings = validator.warnings

        assert any("0.0.0.0" in warning for warning in warnings)

    def test_get_report(self):
        """Test report generation."""
        validator = ConfigValidator()
        config = MockConfig()
        config.providers.openrouter.api_key = "short"

        validator.validate(config)
        report = validator.get_report()

        assert "Errors" in report or "Warnings" in report


class TestRateLimiter:
    """Test rate limiting functionality."""

    def test_is_allowed_under_limit(self):
        """Test requests under limit are allowed."""
        limiter = RateLimiter(max_requests=5, window_seconds=60)

        for i in range(5):
            assert limiter.is_allowed("user1") is True

    def test_is_allowed_over_limit(self):
        """Test requests over limit are denied."""
        limiter = RateLimiter(max_requests=3, window_seconds=60)

        # Use up all requests
        for i in range(3):
            limiter.is_allowed("user1")

        # Next request should be denied
        assert limiter.is_allowed("user1") is False

    def test_is_allowed_different_users(self):
        """Test rate limits are per-user."""
        limiter = RateLimiter(max_requests=1, window_seconds=60)

        limiter.is_allowed("user1")
        assert limiter.is_allowed("user2") is True

    def test_get_remaining(self):
        """Test getting remaining requests."""
        limiter = RateLimiter(max_requests=5, window_seconds=60)

        limiter.is_allowed("user1")
        limiter.is_allowed("user1")
        limiter.is_allowed("user1")

        remaining = limiter.get_remaining("user1")
        assert remaining == 2

    def test_get_retry_after(self):
        """Test getting retry-after time."""
        limiter = RateLimiter(max_requests=1, window_seconds=60)

        limiter.is_allowed("user1")
        retry_after = limiter.get_retry_after("user1")

        assert retry_after > 0
        assert retry_after <= 60

    def test_reset(self):
        """Test resetting rate limit for a user."""
        limiter = RateLimiter(max_requests=1, window_seconds=60)

        limiter.is_allowed("user1")
        limiter.reset("user1")

        assert limiter.is_allowed("user1") is True

    def test_clear(self):
        """Test clearing all rate limits."""
        limiter = RateLimiter(max_requests=1, window_seconds=60)

        limiter.is_allowed("user1")
        limiter.is_allowed("user2")
        limiter.clear()

        assert limiter.get_remaining("user1") == 1
        assert limiter.get_remaining("user2") == 1

    def test_window_expiry(self):
        """Test that old requests expire."""
        limiter = RateLimiter(max_requests=1, window_seconds=0.1)

        limiter.is_allowed("user1")
        import time

        time.sleep(0.2)

        # Should be allowed after window expires
        assert limiter.is_allowed("user1") is True


class TestInputSanitizer:
    """Test input sanitization."""

    def test_sanitize_basic(self):
        """Test basic text sanitization."""
        sanitizer = InputSanitizer(max_length=100)

        result = sanitizer.sanitize("Hello, World!")
        assert result == "Hello, World!"

    def test_sanitize_truncate(self):
        """Test truncation of long input."""
        sanitizer = InputSanitizer(max_length=10)

        result = sanitizer.sanitize("This is a very long string")
        assert len(result) == 10

    def test_sanitize_path_basic(self):
        """Test basic path sanitization."""
        sanitizer = InputSanitizer()

        result = sanitizer.sanitize_path("/home/user/file.txt")
        assert result == "/home/user/file.txt"

    def test_sanitize_path_traversal(self):
        """Test path traversal prevention."""
        sanitizer = InputSanitizer()

        result = sanitizer.sanitize_path("../../etc/passwd")
        assert ".." not in result

    def test_sanitize_path_null_byte(self):
        """Test null byte removal."""
        sanitizer = InputSanitizer()

        result = sanitizer.sanitize_path("/file\x00.txt")
        assert "\x00" not in result

    def test_is_safe_shell_command_safe(self):
        """Test safe command detection."""
        sanitizer = InputSanitizer()

        is_safe, reason = sanitizer.is_safe_shell_command("ls -la")
        assert is_safe is True

    def test_is_safe_shell_command_dangerous_chars(self):
        """Test dangerous character detection."""
        sanitizer = InputSanitizer()

        is_safe, reason = sanitizer.is_safe_shell_command("ls; rm -rf /")
        assert is_safe is False
        assert "dangerous" in reason.lower()

    def test_is_safe_shell_command_dangerous_cmd(self):
        """Test dangerous command detection."""
        sanitizer = InputSanitizer()

        is_safe, reason = sanitizer.is_safe_shell_command("rm -rf /")
        assert is_safe is False

    def test_sanitize_url_valid(self):
        """Test valid URL acceptance."""
        sanitizer = InputSanitizer()

        is_valid, result = sanitizer.sanitize_url("https://example.com")
        assert is_valid is True
        assert result == "https://example.com"

    def test_sanitize_url_no_http(self):
        """Test URL protocol requirement."""
        sanitizer = InputSanitizer()

        is_valid, result = sanitizer.sanitize_url("example.com")
        assert is_valid is False
        assert "http" in result.lower()

    def test_sanitize_url_internal_blocked(self):
        """Test internal URL blocking."""
        sanitizer = InputSanitizer()

        is_valid, result = sanitizer.sanitize_url("http://192.168.1.1/admin")
        assert is_valid is False
        assert "Internal" in result


class TestSecretManager:
    """Test secret management."""

    def test_set_and_get(self, tmp_path):
        """Test storing and retrieving secrets."""
        manager = SecretManager(secrets_dir=tmp_path)

        manager.set("test_key", "test_value")
        result = manager.get("test_key")

        assert result == "test_value"

    def test_get_nonexistent(self, tmp_path):
        """Test retrieving non-existent secret."""
        manager = SecretManager(secrets_dir=tmp_path)

        result = manager.get("nonexistent")

        assert result is None

    def test_delete(self, tmp_path):
        """Test deleting secrets."""
        manager = SecretManager(secrets_dir=tmp_path)

        manager.set("test_key", "test_value")
        deleted = manager.delete("test_key")
        result = manager.get("test_key")

        assert deleted is True
        assert result is None

    def test_delete_nonexistent(self, tmp_path):
        """Test deleting non-existent secret."""
        manager = SecretManager(secrets_dir=tmp_path)

        deleted = manager.delete("nonexistent")

        assert deleted is False

    def test_list_secrets(self, tmp_path):
        """Test listing stored secrets."""
        manager = SecretManager(secrets_dir=tmp_path)

        manager.set("key1", "value1")
        manager.set("key2", "value2")

        secrets = manager.list_secrets()

        assert "key1" in secrets
        assert "key2" in secrets

    def test_secret_name_sanitization(self, tmp_path):
        """Test secret name sanitization."""
        manager = SecretManager(secrets_dir=tmp_path)

        # Names with special characters should be sanitized
        manager.set("test-key_123", "value")
        result = manager.get("test-key_123")

        assert result == "value"

    def test_file_permissions(self, tmp_path):
        """Test that secret files have restricted permissions."""
        manager = SecretManager(secrets_dir=tmp_path)

        manager.set("test_key", "test_value")

        secret_file = tmp_path / "test_key"
        if os.name != "nt":  # Unix permissions only
            mode = oct(secret_file.stat().st_mode)[-3:]
            assert mode == "600"
