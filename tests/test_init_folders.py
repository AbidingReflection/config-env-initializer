
import textwrap
import pytest
from pathlib import Path
import importlib.util

from config_env_initializer.project_setup import initialize_folders, get_folder_paths
from config_env_initializer.schema_utils import validate_schema_file

def load_schema_module(schema_path: Path):
    spec = importlib.util.spec_from_file_location("config_schema", schema_path)
    schema_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(schema_module)
    return schema_module

@pytest.fixture
def example_schema(tmp_path):
    schema_path = tmp_path / "schema.py"
    schema_path.write_text(textwrap.dedent("""\
        schema = {}  # Required for schema validation

        project_dirs = ["db"]
        sub_project_dirs = ["logs", "output"]
        sub_projects = ["extract_1", "extract_2"]
    """))

    return schema_path


def test_schema_validation_fails_on_typo(tmp_path):
    """Ensure schema validation fails when required fields are missing."""
    bad_schema_path = tmp_path / "bad_schema.py"
    bad_schema_path.write_text("""\
# schema = {}  # Intentionally missing

project_dirs = ["db"]
sub_project_dirs = ["logs", "output"]
sub_projects = ["extract_1", "extract_2"]
""")
    schema_module = load_schema_module(bad_schema_path)

    with pytest.raises(ValueError, match="schema.py must define a `schema` dictionary"):
        validate_schema_file(schema_module)


def test_folder_initialization(tmp_path):
    """Explicit test using known-good schema values."""
    # Define correct schema directly
    schema_path = tmp_path / "schema.py"
    schema_path.write_text(textwrap.dedent("""\
        schema = {}  # Required for schema validation

        project_dirs = ["db"]
        sub_project_dirs = ["logs", "output"]
        sub_projects = ["extract_1", "extract_2"]
    """))


    schema_module = load_schema_module(schema_path)
    validate_schema_file(schema_module)

    expected_rel_paths = [
        "db",
        "logs",
        "logs/extract_1",
        "logs/extract_2",
        "output",
        "output/extract_1",
        "output/extract_2",
    ]
    expected_abs_paths = [tmp_path / rel for rel in expected_rel_paths]

    folders = get_folder_paths(schema_module, tmp_path)
    assert sorted(folders) == sorted(expected_abs_paths), "Mismatch in expected folders"

    initialize_folders(folders, project_root=tmp_path)

    for folder in expected_abs_paths:
        assert folder.exists() and folder.is_dir(), f"Missing expected folder: {folder}"

def test_existing_folders_are_not_recreated(tmp_path):
    schema_path = tmp_path / "schema.py"
    schema_path.write_text(textwrap.dedent("""\
        schema = {}  # Required for schema validation

        project_dirs = ["db"]
        sub_project_dirs = ["logs", "output"]
        sub_projects = ["extract_1", "extract_2"]
    """))

    schema_module = load_schema_module(schema_path)
    validate_schema_file(schema_module)

    folders = get_folder_paths(schema_module, tmp_path)

    precreated = [tmp_path / "logs", tmp_path / "output/extract_1"]
    for path in precreated:
        path.mkdir(parents=True, exist_ok=True)
        (path / ".marker").write_text("preserve me")

    initialize_folders(folders, project_root=tmp_path)

    for folder in folders:
        assert folder.exists() and folder.is_dir()

    for path in precreated:
        assert (path / ".marker").read_text() == "preserve me"
