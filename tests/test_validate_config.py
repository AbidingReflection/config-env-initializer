import pytest
from pathlib import Path
import yaml
from config_env_initializer.config_utils import validate_config, generate_config

def write_test_schema(tmp_path: Path):
    schema_code = """
from config_env_initializer.config_validator import ConfigValidator

class CustomValidator(ConfigValidator):
    @staticmethod
    def int_in_range(min_value, max_value):
        def validator(value, key=None):
            if not isinstance(value, int):
                raise ValueError(f"{key} must be an integer.")
            if not (min_value <= value <= max_value):
                raise ValueError(f"{key}={value} not in range [{min_value}, {max_value}]")
        return validator

custom_validators = {
    **CustomValidator.get_all_validators()
}

schema = {
    "name": {"type": str, "required": True, "default": None},
    "level": {"type": str, "required": True, "validators": ["log_level_valid"]},
    "timeout": {"type": int, "required": True, "validators": [{"name": "int_in_range", "min_value": 1, "max_value": 10}]},
    "optional_field": {"type": str, "required": False, "default": "abc"}
}
"""
    schema_path = tmp_path / "schema.py"
    schema_path.write_text(schema_code)
    return schema_path

def write_config_file(tmp_path: Path, content: dict):
    config_path = tmp_path / "test_config.yaml"
    config_path.write_text(yaml.dump(content))
    return config_path

def test_missing_required_field(tmp_path):
    schema_path = write_test_schema(tmp_path)
    config = {"level": "INFO", "timeout": 5}
    config_path = write_config_file(tmp_path, config)
    errors = validate_config(config_path, schema_path)
    assert any("name: missing required field" in err for err in errors)

def test_type_mismatch(tmp_path):
    schema_path = write_test_schema(tmp_path)
    config = {"name": "ProjectX", "level": "INFO", "timeout": "not_an_int"}
    config_path = write_config_file(tmp_path, config)
    errors = validate_config(config_path, schema_path)
    assert any("timeout: expected int" in err for err in errors)

def test_placeholder_value_detected(tmp_path):
    schema_path = write_test_schema(tmp_path)
    config = {"name": "<REQUIRED>", "level": "INFO", "timeout": 5}
    config_path = write_config_file(tmp_path, config)
    errors = validate_config(config_path, schema_path)
    assert any("name: contains placeholder value" in err for err in errors)

def test_failed_custom_validator(tmp_path):
    schema_path = write_test_schema(tmp_path)
    config = {"name": "X", "level": "INFO", "timeout": 99}
    config_path = write_config_file(tmp_path, config)
    errors = validate_config(config_path, schema_path)
    assert any("timeout: validation error" in err for err in errors)

def test_optional_field_is_ignored(tmp_path):
    schema_path = write_test_schema(tmp_path)
    config = {"name": "X", "level": "INFO", "timeout": 5}
    config_path = write_config_file(tmp_path, config)
    errors = validate_config(config_path, schema_path)
    assert errors == []

def test_valid_config_passes(tmp_path):
    schema_path = write_test_schema(tmp_path)
    config = {"name": "GoodProject", "level": "INFO", "timeout": 5, "optional_field": "abc"}
    config_path = write_config_file(tmp_path, config)
    errors = validate_config(config_path, schema_path)
    assert errors == []

def test_unknown_validator_name_string(tmp_path):
    schema_path = tmp_path / "schema.py"
    schema_path.write_text("""
schema = {
    "example": {
        "type": str,
        "required": True,
        "validators": ["nonexistent_validator"]
    }
}
""")
    config_path = write_config_file(tmp_path, {"example": "test"})
    errors = validate_config(config_path, schema_path)
    assert any("unknown validator 'nonexistent_validator'" in e for e in errors)

def test_unknown_validator_dict_name(tmp_path):
    schema_path = tmp_path / "schema.py"
    schema_path.write_text("""
schema = {
    "example": {
        "type": str,
        "required": True,
        "validators": [{"name": "does_not_exist"}]
    }
}
""")
    config_path = write_config_file(tmp_path, {"example": "test"})
    errors = validate_config(config_path, schema_path)
    assert any("unknown validator 'does_not_exist'" in e for e in errors)

def test_invalid_validator_type(tmp_path):
    schema_path = tmp_path / "schema.py"
    schema_path.write_text("""
schema = {
    "example": {
        "type": str,
        "required": True,
        "validators": [42]  # Invalid spec
    }
}
""")
    config_path = write_config_file(tmp_path, {"example": "test"})
    errors = validate_config(config_path, schema_path)
    assert any("invalid validator spec" in e for e in errors)

def test_empty_config_file(tmp_path):
    schema_path = tmp_path / "schema.py"
    schema_path.write_text("""
schema = {
    "required_key": {"type": str, "required": True}
}
""")
    empty_path = tmp_path / "empty.yaml"
    empty_path.write_text("")
    errors = validate_config(empty_path, schema_path)
    assert any("required_key: missing required field" in e for e in errors)

def test_validator_exception_handling(tmp_path):
    schema_path = tmp_path / "schema.py"
    schema_path.write_text("""
from config_env_initializer.config_validator import ConfigValidator
class CustomValidator(ConfigValidator):
    @staticmethod
    def explode(value, key=None):
        raise RuntimeError("Something went boom")

custom_validators = {"explode": CustomValidator.explode}

schema = {
    "danger": {
        "type": str,
        "required": True,
        "validators": ["explode"]
    }
}
""")
    config_path = write_config_file(tmp_path, {"danger": "test"})
    errors = validate_config(config_path, schema_path)
    assert any("danger: validation error - Something went boom" in e for e in errors)

def test_multiple_issues_per_key(tmp_path):
    schema_path = tmp_path / "schema.py"
    schema_path.write_text("""
from config_env_initializer.config_validator import ConfigValidator
class CustomValidator(ConfigValidator):
    @staticmethod
    def fail(value, key=None):
        raise ValueError(f"bad {key}")

custom_validators = {"fail": CustomValidator.fail}

schema = {
    "mykey": {
        "type": int,
        "required": True,
        "validators": ["fail"]
    }
}
""")
    config_path = write_config_file(tmp_path, {"mykey": "not_an_int"})
    errors = validate_config(config_path, schema_path)
    assert any("mykey: expected int" in e for e in errors)
    assert any("mykey: validation error - bad mykey" in e for e in errors)