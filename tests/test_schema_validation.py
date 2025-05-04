import pytest
from config_env_initializer.schema_utils import validate_schema_file
from config_env_initializer.exceptions import ValidationError

# Simulates a working schema module
class ValidSchemaModule:
    schema = {
        "some_key": {"type": str, "required": True, "default": "hi"}
    }
    custom_validators = {}

# Simulates a schema with a missing validator
class InvalidSchemaMissingValidator:
    schema = {
        "some_key": {"type": str, "required": True, "validators": ["does_not_exist"]}
    }
    custom_validators = {}

def test_valid_schema_passes():
    assert validate_schema_file(ValidSchemaModule) is True

def test_invalid_schema_missing_validator():
    with pytest.raises(ValidationError) as exc_info:
        validate_schema_file(InvalidSchemaMissingValidator)

    assert any("Validator 'does_not_exist'" in msg for msg in exc_info.value.errors)


def test_multiple_schema_issues_reported():
    class MultipleIssuesSchema:
        schema = {
            "first_broken_key": {
                "type": str,
                "required": True,
                "validators": ["missing_validator_1"],
            },
            "second_broken_key": {
                "type": str,
                "required": True,
                "validators": ["missing_validator_2"],
            },
        }
        custom_validators = {}

    with pytest.raises(ValidationError) as exc_info:
        validate_schema_file(MultipleIssuesSchema)

    errors = exc_info.value.errors
    assert isinstance(errors, list)
    assert len(errors) == 2
    assert "[first_broken_key]" in errors[0]
    assert "[second_broken_key]" in errors[1]


def test_invalid_dict_validator_name():
    class DictValidatorSchema:
        schema = {
            "timeout": {
                "type": int,
                "required": True,
                "validators": [{"name": "int_in_rlange", "min_value": 1, "max_value": 10}]
            }
        }
        custom_validators = {}

    with pytest.raises(ValidationError) as exc_info:
        validate_schema_file(DictValidatorSchema)

    errors = exc_info.value.errors
    assert any("Validator dict references unknown name 'int_in_rlange'" in msg for msg in errors)


def test_builtin_validators_are_discoverable():
    from config_env_initializer.config_validator import ConfigValidator

    validators = ConfigValidator.get_all_validators()
    assert "log_level_valid" in validators
    assert "is_non_empty_str" in validators
    assert callable(validators["log_level_valid"])


def test_get_all_validators_excludes_utility_methods():
    from config_env_initializer.config_validator import ConfigValidator

    validators = ConfigValidator.get_all_validators()
    assert "get_all_validators" not in validators, (
        "`get_all_validators` should not appear in discovered validators."
    )
