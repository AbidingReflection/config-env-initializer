REQUIRED_PLACEHOLDER = "<REQUIRED>"
OPTIONAL_PLACEHOLDER = "<OPTIONAL>"

def is_placeholder(value: str) -> bool:
    return isinstance(value, str) and value.strip().startswith("<") and value.strip().endswith(">")

class ConfigValidator: 
    @classmethod
    def get_all_validators(cls):
        return {
            name: method
            for name, method in vars(cls).items()
            if callable(method) and not name.startswith("_") and name != "get_all_validators" and name != "apply_validators"
        }

    @classmethod
    def apply_validators(cls, value, key, validators, custom_validators):
        for validator in validators:
            if callable(validator):
                validator(value, key)

            elif isinstance(validator, str):
                if validator not in custom_validators:
                    raise ValueError(f"Unknown validator: '{validator}'")
                custom_validators[validator](value, key)

            elif isinstance(validator, dict):
                name = validator.get("name")
                if not name or name not in custom_validators:
                    raise ValueError(f"Unknown validator name: '{name}'")
                validator_factory = custom_validators[name]

                # Build validator by calling the factory with args
                kwargs = {k: v for k, v in validator.items() if k != "name"}
                try:
                    validator_fn = validator_factory(**kwargs)
                except TypeError as te:
                    raise ValueError(f"Failed to initialize validator '{name}': {te}")

                validator_fn(value, key)

            else:
                raise ValueError(f"Invalid validator format for key '{key}': {validator}")

    @staticmethod
    def log_level_valid(value, key=None):
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if not isinstance(value, str):
            raise ValueError(f"{key} must be a string.")
        if value.upper() not in allowed:
            raise ValueError(f"{key}='{value}' is invalid. Must be one of {sorted(allowed)}.")

    @staticmethod
    def is_non_empty_str(value, key=None):
        if not isinstance(value, str):
            raise ValueError(f"{key} must be a string.")
        if not value.strip():
            raise ValueError(f"{key} cannot be an empty string.")

    @staticmethod
    def is_bool_str(value, key=None):
        if not isinstance(value, str):
            raise ValueError(f"{key} must be a string.")
        if value.lower() not in {"true", "false"}:
            raise ValueError(f"{key} must be 'true' or 'false' (case-insensitive).")

    @staticmethod
    def not_placeholder(value, key=None):
        if is_placeholder(value):
            raise ValueError(f"{key} contains unresolved placeholder value: {value}")

    @staticmethod
    def int_in_range(*, min_value: int, max_value: int):
        """Returns a validator that checks if an int is within [min_value, max_value]."""
        def validator(value, key=None):
            if not isinstance(value, int):
                raise ValueError(f"{key} must be an integer.")
            if not (min_value <= value <= max_value):
                raise ValueError(f"{key}={value} not in range [{min_value}, {max_value}]")
        return validator
