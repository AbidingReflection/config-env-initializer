from copy import deepcopy
from config_env_initializer.config_validator import ConfigValidator
from config_env_initializer.exceptions import ValidationError
from config_env_initializer.config_utils import is_placeholder



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
    validators = getattr(schema_module, "custom_validators", None)
    if callable(validators):
        validators = validators()
    if validators and not isinstance(validators, dict):
        raise TypeError("custom_validators must be a dictionary or a function that returns a dictionary.")
    return validators or {}

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
    if isinstance(value, str) and is_placeholder(value):
        errors.append(f"[{key}] contains unresolved placeholder: {value}")
        return

    validator_specs = rules.get("validators") or []
    if rules.get("validator") and not validator_specs:
        validator_specs = [rules["validator"]]

    for validator_spec in validator_specs:
        # Inline callable (e.g., a lambda or function)
        if callable(validator_spec):
            try:
                validator_spec(value)
            except Exception as e:
                errors.append(f"[{key}] inline validator: {str(e)}")
            continue

        # Named string
        if isinstance(validator_spec, str):
            validator_name = validator_spec
            args = {}
        # Parametrized dict
        elif isinstance(validator_spec, dict):
            validator_name = validator_spec.get("name")
            args = {k: v for k, v in validator_spec.items() if k != "name"}
        else:
            errors.append(f"[{key}] Invalid validator format: {validator_spec}")
            continue

        if validator_name in custom_validators:
            validator_factory = custom_validators[validator_name]
        elif hasattr(ConfigValidator, validator_name):
            validator_factory = getattr(ConfigValidator, validator_name)
        else:
            errors.append(
                f"[{key}] Validator '{validator_name}' not found. "
                f"Define it in schema.py or ConfigValidator."
            )
            continue

        try:
            # Handle factory-style (dict-based) validators
            if isinstance(validator_spec, dict):
                validator_fn = validator_factory(**args)
                validator_fn(value, key)
            else:
                validator_factory(value, key)
        except Exception as e:
            errors.append(f"[{key}] {validator_name}: {str(e)}")

def generate_config_template(schema_module, include_required_placeholders=True) -> dict:
    """
    Generate a config dictionary from a schema, including default values and placeholders
    for required fields that lack defaults.

    Args:
        schema_module: The loaded schema module.
        include_required_placeholders (bool): If True, fill missing required keys with "<REQUIRED>".

    Returns:
        dict: A dictionary representing the template config.
    """
    schema = _extract_schema(schema_module)
    template = {}

    for key, rules in schema.items():
        default = rules.get("default", None)
        required = rules.get("required", False)

        if default is not None:
            template[key] = default
        elif required and include_required_placeholders:
            template[key] = "<REQUIRED>"

    return template

def validate_schema_file(schema_module):
    """
    Validates the structure and logic of a schema module.

    Raises:
        ValidationError: If issues are found with the schema.
    """
    errors = []
    schema = _extract_schema(schema_module)
    custom_validators = _extract_custom_validators(schema_module)

    for key, rules in schema.items():
        if not isinstance(rules, dict):
            errors.append(f"[{key}] Schema rules must be a dictionary.")
            continue

        if "type" not in rules:
            errors.append(f"[{key}] Missing required 'type' key in schema rules.")

        if "required" not in rules:
            errors.append(f"[{key}] Missing required 'required' key in schema rules.")

        validator_specs = rules.get("validators") or []
        if rules.get("validator") and not validator_specs:
            validator_specs = [rules["validator"]]

        for validator_spec in validator_specs:
            if isinstance(validator_spec, str):
                if validator_spec not in custom_validators and not hasattr(ConfigValidator, validator_spec):
                    errors.append(
                        f"[{key}] Validator '{validator_spec}' not found in custom_validators or ConfigValidator."
                    )
            elif isinstance(validator_spec, dict):
                name = validator_spec.get("name")
                if not name:
                    errors.append(f"[{key}] Validator dict missing 'name' key: {validator_spec}")
                elif name not in custom_validators and not hasattr(ConfigValidator, name):
                    errors.append(
                        f"[{key}] Validator dict references unknown name '{name}' not found in custom_validators or ConfigValidator."
                    )
            elif not callable(validator_spec):
                errors.append(f"[{key}] Invalid validator format: {validator_spec}")

    if errors:
        raise ValidationError(errors)

    return True