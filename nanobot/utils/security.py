"""
Security utilities for nanobot.

Provides configuration validation, rate limiting, and input sanitization.
"""

from __future__ import annotations

import os
import re
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

from loguru import logger


class ConfigValidator:
    """
    Validate nanobot configuration for security issues.

    Usage:
        validator = ConfigValidator()
        errors = validator.validate(config)
    """

    # Patterns for sensitive data
    API_KEY_PATTERN = re.compile(r'^[A-Za-z0-9_-]{20,}$')
    WEBHOOK_URL_PATTERN = re.compile(r'^https://')

    def __init__(self):
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def validate(self, config: Any) -> list[str]:
        """
        Validate entire configuration.

        Returns list of error messages.
        """
        self.errors = []
        self.warnings = []

        # Validate providers
        self._validate_providers(config)

        # Validate channels
        self._validate_channels(config)

        # Validate tools
        self._validate_tools(config)

        # Validate gateway
        self._validate_gateway(config)

        return self.errors

    def _validate_providers(self, config: Any) -> None:
        """Validate provider configurations."""
        if not hasattr(config, 'providers'):
            return

        providers = config.providers
        for provider_name in ['openrouter', 'anthropic', 'openai', 'deepseek']:
            provider = getattr(providers, provider_name, None)
            if provider and provider.api_key:
                # Check API key format
                if not self.API_KEY_PATTERN.match(provider.api_key):
                    self.warnings.append(
                        f"Provider '{provider_name}': API key format looks unusual"
                    )

                # Warn if API key is too short
                if len(provider.api_key) < 20:
                    self.errors.append(
                        f"Provider '{provider_name}': API key too short (min 20 chars)"
                    )

    def _validate_channels(self, config: Any) -> None:
        """Validate channel configurations."""
        if not hasattr(config, 'channels'):
            return

        channels = config.channels

        # Telegram
        if hasattr(channels, 'telegram') and channels.telegram.enabled:
            token = channels.telegram.token
            if not token:
                self.errors.append("Telegram enabled but no token configured")
            elif not token.startswith(('http', 'bot')):
                # Telegram bot tokens start with numbers, but we check if it looks like a token
                if len(token) < 30:
                    self.warnings.append("Telegram token format looks unusual")

            # Check allow_from
            if not channels.telegram.allow_from:
                self.warnings.append(
                    "Telegram: allow_from is empty (all users allowed)"
                )

        # Email
        if hasattr(channels, 'email') and channels.email.enabled:
            email = channels.email
            if not email.consent_granted:
                self.errors.append(
                    "Email channel: consent_granted must be true to enable"
                )
            if not email.imap_password or not email.smtp_password:
                self.errors.append(
                    "Email channel: passwords not configured"
                )

    def _validate_tools(self, config: Any) -> None:
        """Validate tool configurations."""
        if not hasattr(config, 'tools'):
            return

        tools = config.tools

        # Check if workspace restriction is enabled
        if hasattr(tools, 'restrict_to_workspace'):
            if not tools.restrict_to_workspace:
                self.warnings.append(
                    "Tools: restrict_to_workspace is disabled (security risk)"
                )

    def _validate_gateway(self, config: Any) -> None:
        """Validate gateway configuration."""
        if not hasattr(config, 'gateway'):
            return

        gateway = config.gateway

        # Warn if binding to all interfaces
        if gateway.host == "0.0.0.0":
            self.warnings.append(
                "Gateway: binding to all interfaces (0.0.0.0). "
                "Consider using 127.0.0.1 for local-only access."
            )

        # Check if using default port
        if gateway.port == 18790:
            self.warnings.append(
                "Gateway: using default port. Consider changing for production."
            )

    def get_report(self) -> str:
        """Generate validation report."""
        lines = ["Configuration Validation Report", "=" * 40]

        if self.errors:
            lines.append(f"\n❌ Errors ({len(self.errors)}):")
            for error in self.errors:
                lines.append(f"  - {error}")

        if self.warnings:
            lines.append(f"\n⚠️  Warnings ({len(self.warnings)}):")
            for warning in self.warnings:
                lines.append(f"  - {warning}")

        if not self.errors and not self.warnings:
            lines.append("\n✅ No issues found!")

        return "\n".join(lines)


class RateLimiter:
    """
    Token bucket rate limiter.

    Usage:
        limiter = RateLimiter(max_requests=10, window_seconds=60)

        if not limiter.is_allowed(user_id):
            return "Rate limit exceeded"
    """

    def __init__(self, max_requests: int = 10, window_seconds: float = 60):
        self._max_requests = max_requests
        self._window_seconds = window_seconds
        self._requests: dict[str, list[float]] = defaultdict(list)
        self._lock = None  # Async lock if needed

    def is_allowed(self, key: str) -> bool:
        """Check if request is allowed for key."""
        now = time.time()
        window_start = now - self._window_seconds

        # Remove old requests
        self._requests[key] = [
            ts for ts in self._requests[key] if ts > window_start
        ]

        # Check if under limit
        if len(self._requests[key]) < self._max_requests:
            self._requests[key].append(now)
            return True

        return False

    def get_remaining(self, key: str) -> int:
        """Get remaining requests for key."""
        now = time.time()
        window_start = now - self._window_seconds

        current_requests = [
            ts for ts in self._requests[key] if ts > window_start
        ]

        return max(0, self._max_requests - len(current_requests))

    def get_retry_after(self, key: str) -> float:
        """Get seconds until next request is allowed."""
        if not self._requests[key]:
            return 0

        oldest = min(self._requests[key])
        retry_after = oldest + self._window_seconds - time.time()

        return max(0, retry_after)

    def reset(self, key: str) -> None:
        """Reset rate limit for key."""
        self._requests[key] = []

    def clear(self) -> None:
        """Clear all rate limits."""
        self._requests.clear()


class InputSanitizer:
    """
    Sanitize user input to prevent injection attacks.

    Usage:
        sanitizer = InputSanitizer()
        safe_input = sanitizer.sanitize(user_input)
    """

    # Dangerous shell characters
    SHELL_DANGEROUS = re.compile(r'[;&|`$(){}!#*?~]')

    # Path traversal patterns
    PATH_TRAVERSAL = re.compile(r'\.\.[/\\]|[/\\]\.\.')

    # SQL injection patterns (basic)
    SQL_INJECTION = re.compile(
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|ALTER)\b|--|;)",
        re.IGNORECASE
    )

    def __init__(self, max_length: int = 10000):
        self._max_length = max_length

    def sanitize(self, text: str) -> str:
        """Sanitize text input."""
        if not text:
            return ""

        # Truncate if too long
        if len(text) > self._max_length:
            text = text[:self._max_length]

        return text

    def sanitize_path(self, path: str) -> str:
        """Sanitize file path to prevent traversal."""
        if not path:
            return ""

        # Remove path traversal patterns
        path = self.PATH_TRAVERSAL.sub('', path)

        # Normalize path separators
        path = path.replace('\\', '/')

        # Remove null bytes
        path = path.replace('\x00', '')

        return path

    def is_safe_shell_command(self, command: str) -> tuple[bool, str]:
        """
        Check if shell command is safe to execute.

        Returns (is_safe, reason).
        """
        if not command:
            return False, "Empty command"

        # Check for dangerous characters
        if self.SHELL_DANGEROUS.search(command):
            return False, "Contains dangerous shell characters"

        # Check for path traversal
        if self.PATH_TRAVERSAL.search(command):
            return False, "Contains path traversal"

        # Check for common dangerous commands
        dangerous_cmds = ['rm -rf', 'mkfs', 'dd if=', ':(){:|:&};:', 'fork']
        for dangerous in dangerous_cmds:
            if dangerous in command.lower():
                return False, f"Contains dangerous command: {dangerous}"

        return True, "Safe"

    def sanitize_url(self, url: str) -> tuple[bool, str]:
        """
        Validate and sanitize URL.

        Returns (is_valid, url_or_error).
        """
        if not url:
            return False, "Empty URL"

        # Check protocol
        if not url.startswith(('http://', 'https://')):
            return False, "URL must start with http:// or https://"

        # Check for internal URLs
        internal_patterns = [
            'localhost',
            '127.0.0.1',
            '192.168.',
            '10.',
            '172.16.',
            '172.17.',
            '172.18.',
            '172.19.',
            '172.2',
            '172.30.',
            '172.31.',
        ]

        for pattern in internal_patterns:
            if pattern in url.lower():
                return False, f"Internal URLs not allowed: {pattern}"

        return True, url


class SecretManager:
    """
    Manage secrets (API keys, passwords) securely.

    Usage:
        secrets = SecretManager()
        api_key = secrets.get("openrouter_api_key")
    """

    def __init__(self, secrets_dir: Path | None = None):
        if secrets_dir is None:
            secrets_dir = Path.home() / ".nanobot" / "secrets"

        self._secrets_dir = secrets_dir
        self._secrets_dir.mkdir(parents=True, exist_ok=True, mode=0o700)

    def set(self, name: str, value: str) -> None:
        """Store a secret."""
        # Sanitize name
        safe_name = re.sub(r'[^a-zA-Z0-9_]', '', name)

        # Write to file with restricted permissions
        secret_file = self._secrets_dir / safe_name
        secret_file.write_text(value, encoding="utf-8")

        # Set file permissions (Unix only)
        try:
            os.chmod(secret_file, 0o600)
        except OSError:
            pass  # Windows doesn't support Unix permissions

        logger.info("Secret '{}' stored securely", name)

    def get(self, name: str) -> str | None:
        """Retrieve a secret."""
        safe_name = re.sub(r'[^a-zA-Z0-9_]', '', name)
        secret_file = self._secrets_dir / safe_name

        if not secret_file.exists():
            return None

        try:
            return secret_file.read_text(encoding="utf-8").strip()
        except Exception as e:
            logger.error("Failed to read secret '{}': {}", name, e)
            return None

    def delete(self, name: str) -> bool:
        """Delete a secret."""
        safe_name = re.sub(r'[^a-zA-Z0-9_]', '', name)
        secret_file = self._secrets_dir / safe_name

        if secret_file.exists():
            secret_file.unlink()
            logger.info("Secret '{}' deleted", name)
            return True

        return False

    def list_secrets(self) -> list[str]:
        """List all stored secret names."""
        return [f.stem for f in self._secrets_dir.iterdir() if f.is_file()]


# Global instances
config_validator = ConfigValidator()
input_sanitizer = InputSanitizer()
rate_limiter = RateLimiter(max_requests=10, window_seconds=60)
