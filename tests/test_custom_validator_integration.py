import textwrap
import yaml
import pytest
from pathlib import Path
from config_env_initializer.config_loader import ConfigLoader
from config_env_initializer.exceptions import ValidationError


def test_custom_validator_decorator_registration(tmp_path):
    # --- Setup schema.py with @CustomValidator.register() ---
    schema_path = tmp_path / "schema.py"
    schema_path.write_text(textwrap.dedent("""\
        from config_env_initializer.config_validator import CustomValidator

        @CustomValidator.register()
        def string_in_string(*, input_str):
            def validator(value, key=None):
                if not isinstance(value, str):
                    raise ValueError(f"{key} must be a string.")
                if input_str not in value:
                    raise ValueError(f"{key} must contain the substring '{input_str}'. Got: '{value}'")
            return validator

        schema = {
            "log_dir": {
                "type": str,
                "required": False,
                "validators": [],
                "default": "logs"
            },
            "log_level": {
                "type": str,
                "required": False,
                "validators": ["log_level_valid"],
                "default": "INFO"
            },
            "log_microseconds": {
                "type": bool,
                "required": False,
                "validators": [],
                "default": False
            },
            "output_dir": {
                "type": str,
                "required": True,
                "validators": [{"name": "string_in_string", "input_str": "output"}],
                "default": "output"
            }
        }
    """))

    # --- Setup config.yaml ---
    config_path = tmp_path / "config.yaml"
    config_path.write_text(textwrap.dedent("""\
        output_dir: my_output_folder
    """))

    # --- Load and validate using ConfigLoader ---
    loader = ConfigLoader(str(config_path), str(schema_path))
    assert loader.config["output_dir"] == "my_output_folder"
    assert loader.config["log_dir"] == "logs"
    assert loader.config["log_level"] == "INFO"
    assert loader.config["log_microseconds"] is False
