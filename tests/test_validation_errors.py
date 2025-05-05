import pytest
from config_env_initializer.schema_utils import validate_config_against_schema
from config_env_initializer.exceptions import ValidationError

# --- Dummy schemas for testing ---
class DummyRequiredSchema:
    schema = {
        "project_name": {"type": str, "required": True},
        "db_dir": {"type": str, "required": True},
    }

class DummyWithOptional:
    schema = {
        "qtest_auth_path": {"type": str, "required": False},
    }

# --- Tests ---

def test_missing_required_fields():
    config = {}
    with pytest.raises(ValidationError) as exc_info:
        validate_config_against_schema(config, DummyRequiredSchema)

    message = str(exc_info.value)
    assert "- [project_name] Missing required config key: 'project_name'" in message
    assert "- [db_dir] Missing required config key: 'db_dir'" in message



def test_required_placeholders_trigger_error():
    config = {
        "project_name": "<REQUIRED>",
        "db_dir": "<REQUIRED>",
    }

    with pytest.raises(ValidationError) as exc_info:
        validate_config_against_schema(config, DummyRequiredSchema)

    message = str(exc_info.value)
    assert "unresolved placeholder" in message
    assert "[project_name]" in message
    assert "[db_dir]" in message


def test_optional_placeholder_also_triggers_warning():
    config = {
        "qtest_auth_path": "<OPTIONAL>"
    }

    with pytest.raises(ValidationError) as exc_info:
        validate_config_against_schema(config, DummyWithOptional)

    message = str(exc_info.value)
    assert "unresolved placeholder" in message
    assert "[qtest_auth_path]" in message
