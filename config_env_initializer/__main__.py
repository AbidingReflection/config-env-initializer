import sys
from pathlib import Path
import importlib.util

from config_env_initializer.project_setup import initialize_folders, get_folder_paths, create_auth_examples
from config_env_initializer.schema_utils import validate_schema_file
from config_env_initializer.exceptions import ValidationError
from config_env_initializer.config_utils import generate_config, validate_config


def load_schema_module(schema_path: Path):
    spec = importlib.util.spec_from_file_location("config_schema", schema_path)
    schema_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(schema_module)
    return schema_module


def print_general_help():
    print("""=== Config Environment Initializer ===

Usage:
------
  config-init <command> [args...]

Commands:
--------
  validate-config <config.yaml> [schema.py]   Validate a config file against the schema
  validate-schema [schema.py]                 Validate the structure of a schema file
  init-folders    [schema.py]                 Create project folders defined in the schema
  generate-config [schema.py]                 Generate a sample config file from the schema
  initiate        [schema.py]                 Run all setup steps (validate, init, generate)

Shortcuts:
---------
  validate-config: valc, val-c, vc
  validate-schema: vals, val-s, vs
  init-folders:    initf, init-f, if
  generate-config: genc, gen-c, gc
  initiate:        init, i

Defaults:
---------
  schema.py path defaults to: ./schema/schema.py
""")


def validate_config_command(args):
    if len(args) < 1:
        print("[ERROR] Missing <config.yaml> path.")
        print("Usage: config-init validate-config <config.yaml> [schema.py]")
        sys.exit(1)

    config_path = Path(args[0])
    schema_path = Path(args[1]) if len(args) > 1 else Path("schema/schema.py")

    try:
        # Ensure the schema is executed, registering custom validators
        load_schema_module(schema_path)

        errors = validate_config(config_path=config_path, schema_path=schema_path)
        if errors:
            print("[ERROR] Config failed validation:")
            for err in errors:
                print(f"  - {err}")
            sys.exit(1)
        else:
            print("[SUCCESS] Config is valid.")
    except Exception as e:
        print(f"[ERROR] Unexpected validation error:\n  {e}")
        sys.exit(2)



def validate_schema_command(args):
    schema_path = Path(args[0]) if args else Path("schema/schema.py")
    try:
        schema_module = load_schema_module(schema_path)
        validate_schema_file(schema_module)
        print("[SUCCESS] Schema is valid.")
    except ValidationError as ve:
        print("[ERROR] Schema validation failed:")
        for line in ve.errors:
            print(f"  - {line}")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Unexpected error:\n  {e}")
        sys.exit(1)


def init_folders_command(args):
    schema_path = Path(args[0]) if args else Path("schema/schema.py")
    try:
        schema_module = load_schema_module(schema_path)
        validate_schema_file(schema_module)
        project_root = Path.cwd()
        folders = get_folder_paths(schema_module, project_root)

        if not folders:
            print("No new folders required.")
            sys.exit(0)

        print("The following folders will be created:")
        for folder in folders:
            print(f"  - {folder}")

        confirm = input(f"\nProceed with initializing these folders in {project_root}? [y/N]: ").strip().lower()
        if confirm not in ("y", "yes"):
            print("Aborted.")
            sys.exit(0)

        initialize_folders(folders, project_root=project_root)
        create_auth_examples(project_root=project_root, schema_module=schema_module)
        print("[SUCCESS] Folders initialized successfully.")
    except Exception as e:
        print(f"[ERROR] Folder initialization failed:\n{e}")
        sys.exit(2)


def generate_config_command(args):
    schema_path = Path(args[0]) if args else Path("schema/schema.py")
    try:
        generate_config(schema_path=schema_path)
        print("[SUCCESS] Config template generated.")
    except Exception as e:
        print(f"[ERROR] Config generation failed:\n{e}")
        sys.exit(3)


def initiate_command(args):
    print("[INFO] Running initialization sequence (validate-schema → init-folders → generate-config)...")
    try:
        validate_schema_command(args)
        init_folders_command(args)
        generate_config_command(args)
        print("[SUCCESS] Project initialization complete.")
    except SystemExit as e:
        # Pass through subcommand exit codes
        sys.exit(e.code)
    except Exception as e:
        print(f"[ERROR] Unexpected error during initiation:\n{e}")
        sys.exit(4)


# Canonical commands
COMMANDS = {
    "validate-config": validate_config_command,
    "validate-schema": validate_schema_command,
    "init-folders": init_folders_command,
    "generate-config": generate_config_command,
    "initiate": initiate_command,
}

# Aliases per command
COMMAND_ALIASES = {
    "validate-config": ["valc", "val-c", "vc"],
    "validate-schema": ["vals", "val-s", "vs"],
    "init-folders":    ["init-f", "if", "initf"],
    "generate-config": ["gen-config", "g-config", "gen-c", "genc", "gen-conf", "gc"],
    "initiate":        ["init", "i"],  # <- NEW
}


# Flat alias map: maps all aliases and canonical names to the real command name
RESOLVED_COMMANDS = {
    cmd: cmd
    for cmd in COMMANDS
}
for canonical, aliases in COMMAND_ALIASES.items():
    for alias in aliases:
        RESOLVED_COMMANDS[alias] = canonical


def main():
    if len(sys.argv) < 2:
        print("[ERROR] No command provided.\n")
        print_general_help()
        sys.exit(1)

    raw_command = sys.argv[1]
    args = sys.argv[2:]

    if raw_command in ("help", "--help", "-h"):
        print_general_help()
        sys.exit(0)

    resolved = RESOLVED_COMMANDS.get(raw_command)
    if not resolved:
        print(f"[ERROR] Unknown command '{raw_command}'\n")
        print_general_help()
        sys.exit(1)

    handler = COMMANDS[resolved]
    handler(args)


if __name__ == "__main__":
    main()
