class SensitiveValue:
    """Wrapper for sensitive values that hides their contents when printed or logged."""

    def __init__(self, value):
        self._value = value

    def get(self):
        """Returns the actual sensitive value."""
        return self._value

    def __str__(self):
        """Returns masked string representation."""
        return "*****"

    def __repr__(self):
        """Returns masked repr useful for logs/debugging."""
        return "<SensitiveValue *****>"

    def __eq__(self, other):
        """Equality check that supports comparison with raw or wrapped values."""
        if isinstance(other, SensitiveValue):
            return self._value == other._value
        return self._value == other

    def __hash__(self):
        """Hashes the underlying value for use in sets/dicts."""
        return hash(self._value)


def mask_config_for_logging(config: dict) -> dict:
    """Returns a copy of the config with sensitive fields (e.g. auth) masked."""
    masked = {}

    for key, value in config.items():
        if key == "auth" and isinstance(value, dict):
            # Mask each auth provider key but not their structure
            masked["auth"] = {k: "*****" for k in value.keys()}
        elif isinstance(value, SensitiveValue):
            masked[key] = "*****"
        else:
            masked[key] = value

    return masked
