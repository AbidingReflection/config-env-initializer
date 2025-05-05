import tempfile
from pathlib import Path
from unittest.mock import patch
from datetime import datetime, timezone
from config_env_initializer.config_utils import generate_config


def create_test_schema_file(dir_path: Path) -> Path:
    schema_code = """
schema = {
    "project_name": {
        "type": str,
        "required": True,
        "default": None,
        "validators": []
    },
    "log_dir": {
        "type": str,
        "required": True,
        "default": "logs",
        "validators": []
    },
    "log_level": {
        "type": str,
        "required": False,
        "default": "INFO",
        "validators": []
    },
    "debug_mode": {
        "type": bool,
        "required": False,
        "default": False,
        "validators": []
    },
    "timeout": {
        "type": int,
        "required": True,
        "default": None,
        "validators": []
    },
    "retries": {
        "type": int,
        "required": False,
        "default": None,
        "validators": []
    }
}
"""
    schema_path = dir_path / "schema.py"
    schema_path.write_text(schema_code)
    return schema_path


def test_generate_config_creates_expected_yaml(tmp_path):
    import os
    os.chdir(tmp_path)
    schema_path = create_test_schema_file(tmp_path)
    fixed_time = datetime(2025, 5, 4, 22, 0, 0, tzinfo=timezone.utc)

    with patch("builtins.input", return_value="y"), \
         patch("config_env_initializer.config_utils.datetime") as mock_datetime:

        mock_datetime.now.side_effect = lambda tz=None: fixed_time
        mock_datetime.now.return_value.isoformat = lambda: fixed_time.isoformat()

        generate_config(schema_path=schema_path)

    output_files = list((tmp_path / "configs").glob("generated_config_*.yaml"))
    assert output_files, "No config file was generated"

    output_text = output_files[0].read_text()

    assert "# Schema source:" in output_text
    assert "project_name: <REQUIRED>" in output_text
    assert "log_dir: logs" in output_text
    assert "log_level: INFO" in output_text
    assert "debug_mode: false" in output_text
    assert "timeout: <REQUIRED>" in output_text
    assert "retries: <OPTIONAL>" in output_text
    assert "2025-05-04T22:00:00+00:00" in output_text


def test_generate_config_respects_overwrite_prompt(tmp_path):
    import os

    os.chdir(tmp_path)

    schema_path = create_test_schema_file(tmp_path)

    # First run: create the config
    with patch("builtins.input", return_value="y"):
        generate_config(schema_path=schema_path)

    # Get the generated file path
    generated_files = list((tmp_path / "configs").glob("generated_config_*.yaml"))
    assert generated_files
    existing_file = generated_files[0]
    original_content = existing_file.read_text()

    # Second run: say "n" to overwrite
    with patch("builtins.input", return_value="n"):
        generate_config(schema_path=schema_path)

    # File content should be unchanged
    assert existing_file.read_text() == original_content
