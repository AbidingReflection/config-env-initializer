import argparse
import sys
from pathlib import Path
import importlib.util

from config_env_initializer.config_loader import ConfigLoader
from config_env_initializer.project_setup import initialize_folders, get_folder_paths
from config_env_initializer.schema_utils import generate_config_template, validate_schema_file
from config_env_initializer.exceptions import ValidationError
from config_env_initializer.config_utils import generate_config
from config_env_initializer.config_utils import generate_config, validate_config


def load_schema_module(schema_path: Path):
    """Dynamically import a schema.py module from the provided path."""
    spec = importlib.util.spec_from_file_location("config_schema", schema_path)
    schema_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(schema_module)
    return schema_module

def main():
    parser = argparse.ArgumentParser(
        description=(
            "Config Environment Initializer CLI\n\n"
            "Commands:\n"
            "  validate-config <CONFIG> [SCHEMA]     Validate a config file against the schema.\n"
            "  validate-schema [SCHEMA]              Validate a schema file (default: schema/schema.py).\n"
            "  init-folders [SCHEMA]                 Create required directories based on schema rules.\n"
            "  generate-config [SCHEMA]              Generate a YAML config template from the schema.\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_config_parser = subparsers.add_parser("validate-config", help="Validate a config file against the schema.")
    validate_config_parser.add_argument("config_path", help="Path to the config YAML file.")
    validate_config_parser.add_argument("schema_path", nargs="?", help="Optional path to schema.py")

    validate_schema_parser = subparsers.add_parser("validate-schema", help="Validate a schema file.")
    validate_schema_parser.add_argument("schema_path", nargs="?", default=str(Path.cwd() / "schema" / "schema.py"))

    init_parser = subparsers.add_parser("init-folders", help="Create required project directories from schema.")
    init_parser.add_argument("schema_path", nargs="?", help="Optional path to schema.py")

    gen_parser = subparsers.add_parser("generate-config", help="Generate an example YAML config from the schema.")
    gen_parser.add_argument("schema_path", nargs="?", default=str(Path.cwd() / "schema" / "schema.py"))

    args = parser.parse_args()

    if args.command == "validate-schema":
        try:
            schema_module = load_schema_module(Path(args.schema_path))
            validate_schema_file(schema_module)
            print("[SUCCESS] Schema is valid.")
            sys.exit(0)
        except ValidationError as ve:
            print("[ERROR] Schema validation failed:")
            for line in ve.errors:
                print(f"  - {line}")
            sys.exit(1)
        except Exception as e:
            print(f"[ERROR] Unexpected error:\n  {str(e)}")
            sys.exit(1)

    elif args.command == "validate-config":
        try:
            schema_path = Path(args.schema_path) if args.schema_path else Path.cwd() / "schema" / "schema.py"
            config_path = Path(args.config_path)

            errors = validate_config(config_path=config_path, schema_path=schema_path)

            if errors:
                print("[ERROR] Config failed validation:")
                for err in errors:
                    print(f"  - {err}")
                sys.exit(1)
            else:
                print("[SUCCESS] Config is valid.")
                sys.exit(0)

        except Exception as e:
            print(f"[ERROR] Unexpected validation error:\n  {e}")
            sys.exit(2)

    elif args.command == "init-folders":
        try:
            schema_path = Path(args.schema_path) if args.schema_path else Path.cwd() / "schema" / "schema.py"
            schema_module = load_schema_module(schema_path)
            validate_schema_file(schema_module)
            project_root = Path.cwd()


            folders = get_folder_paths(schema_module, project_root)

            if len(folders) == 0:
                print("No new folders required.")
                sys.exit(0)
            else:
                print("The following folders will be created:")
                
                for folder in folders:
                    print(f"  - {folder}")

                confirm = input(f"\nProceed with initializing these folders in {project_root}? [y/N]: ").strip().lower()
                if confirm not in ("y", "yes"):
                    print("Aborted.")
                    sys.exit(0)

                initialize_folders(folders, project_root=project_root)
                print("[SUCCESS] Folders initialized successfully.")
                sys.exit(0)
        except Exception as e:
            print(f"[ERROR] Folder initialization failed:\n{e}")
            sys.exit(2)

    elif args.command == "generate-config":
        try:
            schema_path = Path(args.schema_path)
            generate_config(schema_path=schema_path)
            print("[SUCCESS] Config template generated.")
            sys.exit(0)
        except Exception as e:
            print(f"[ERROR] Config generation failed:\n{e}")
            sys.exit(3)





if __name__ == "__main__":
    main()
