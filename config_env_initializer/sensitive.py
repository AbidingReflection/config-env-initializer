class SensitiveValue:
    def __init__(self, value):
        self._value = value

    def get(self):
        return self._value

    def __str__(self):
        return "*****"

    def __repr__(self):
        return "<SensitiveValue *****>"

    def __eq__(self, other):
        if isinstance(other, SensitiveValue):
            return self._value == other._value
        return self._value == other

    def __hash__(self):
        return hash(self._value)


def mask_config_for_logging(config: dict) -> dict:
    masked = {}

    for key, value in config.items():
        if key == "auth" and isinstance(value, dict):
            masked["auth"] = {k: "*****" for k in value.keys()}
        elif isinstance(value, SensitiveValue):
            masked[key] = "*****"
        else:
            masked[key] = value

    return masked
