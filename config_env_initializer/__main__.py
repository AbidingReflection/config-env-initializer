import argparse
import sys
from pathlib import Path
from config_env_initializer import ConfigLoader
from config_env_initializer.project_setup import initialize_folders

def main():
    parser = argparse.ArgumentParser(
        description="Config Environment Initializer CLI"
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--validate", metavar="CONFIG_PATH", help="Validate a config file.")
    group.add_argument("--init-folders", metavar="CONFIG_PATH", help="Validate config and create required folders.")

    parser.add_argument("--schema", metavar="SCHEMA_PATH", help="Optional schema path override.")

    args = parser.parse_args()
    config_path = args.validate or args.init_folders
    schema_path = args.schema

    try:
        loader = ConfigLoader(config_path, schema_path)
    except Exception as e:
        print(f"❌ Config failed validation:\n{e}")
        sys.exit(1)

    if args.validate:
        print("✅ Config is valid.")
        sys.exit(0)

    if args.init_folders:
        project_root = Path(config_path).expanduser().resolve().parent
        try:
            initialize_folders(loader.config, project_root=project_root)
            print("✅ Folders initialized successfully.")
            sys.exit(0)
        except Exception as e:
            print(f"❌ Folder initialization failed:\n{e}")
            sys.exit(2)

if __name__ == "__main__":
    main()
