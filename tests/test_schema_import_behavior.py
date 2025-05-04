import pytest
import textwrap
import tempfile
import os
from pathlib import Path
from config_env_initializer.__main__ import load_schema_module
from config_env_initializer.schema_utils import validate_schema_file
from config_env_initializer.exceptions import ValidationError

def _write_temp_schema(contents: str) -> Path:
    tmp_dir = tempfile.TemporaryDirectory()
    schema_path = Path(tmp_dir.name) / "schema.py"
    schema_path.write_text(textwrap.dedent(contents))
    return schema_path, tmp_dir

def test_schema_module_missing_schema_key():
    file_contents = """
    # No schema defined at all
    """
    path, tmp = _write_temp_schema(file_contents)

    with pytest.raises(ValueError, match="schema.py must define a `schema` dictionary"):
        validate_schema_file(load_schema_module(path))

def test_schema_module_with_syntax_error():
    file_contents = """
    schema = {
        "bad": {
            "type": str
            "required": True,
        }
    }
    """
    path, tmp = _write_temp_schema(file_contents)

    with pytest.raises(SyntaxError):
        load_schema_module(path)
