from copy import deepcopy
from config_env_initializer.config_validator import ConfigValidator
from config_env_initializer.exceptions import ValidationError


def validate_config_against_schema(config: dict, schema_module) -> dict:
    schema = _extract_schema(schema_module)
    custom_validators = _extract_custom_validators(schema_module)
    validated = deepcopy(config)
    errors = []

    for key, rules in schema.items():
        try:
            value = validated.get(key, None)
            validated[key] = _apply_defaults_and_check_required(key, value, rules)
            value = validated[key]
            _check_type(key, value, rules)
            _run_validators(key, value, rules, custom_validators, errors)
        except Exception as e:
            errors.append(f"[{key}] {str(e)}")

    if errors:
        raise ValidationError(errors)

    return validated


def _extract_schema(schema_module):
    schema = getattr(schema_module, "schema", None)
    if not isinstance(schema, dict):
        raise ValueError("schema.py must define a `schema` dictionary.")
    return schema


def _extract_custom_validators(schema_module):
    if hasattr(schema_module, "custom_validators"):
        validators = schema_module.custom_validators()
        if not isinstance(validators, dict):
            raise TypeError("custom_validators() must return a dictionary of callable validators.")
        return validators
    return {}


def _apply_defaults_and_check_required(key, value, rules):
    required = rules.get("required", False)
    default = rules.get("default", None)

    if value is None:
        if required and default is None:
            raise ValueError(f"Missing required config key: '{key}'")
        return default

    return value


def _check_type(key, value, rules):
    expected_type = rules.get("type")
    if expected_type and not isinstance(value, expected_type):
        raise TypeError(
            f"Config key '{key}' must be of type {expected_type.__name__}, "
            f"but got {type(value).__name__}."
        )


def _run_validators(key, value, rules, custom_validators, errors):
    for validator_spec in rules.get("validators", []):
        if isinstance(validator_spec, str):
            validator_name = validator_spec
            args = {}
        elif isinstance(validator_spec, dict):
            validator_name = validator_spec.get("name")
            args = {k: v for k, v in validator_spec.items() if k != "name"}
        else:
            errors.append(f"[{key}] Invalid validator format: {validator_spec}")
            continue

        validator = None

        if validator_name in custom_validators:
            validator = custom_validators[validator_name]
        elif hasattr(ConfigValidator, validator_name):
            validator = getattr(ConfigValidator, validator_name)
        else:
            errors.append(
                f"[{key}] Validator '{validator_name}' not found. "
                f"Define it in schema.py or ConfigValidator."
            )
            continue

        try:
            validator(value, key, **args)
        except Exception as e:
            errors.append(f"[{key}] {validator_name}: {str(e)}")
