from pathlib import Path

def initialize_folders(config: dict, project_root: Path = None):
    """
    Create required folders defined in config, constrained to the project root.

    Args:
        config (dict): Validated configuration (with 'logger' key).
        project_root (Path): Optional base path. Defaults to Path.cwd().

    Raises:
        ValueError: If a directory path is outside the allowed root.
    """
    root = project_root.resolve() if project_root else Path.cwd().resolve()
    logger = config.get("logger", None)

    def log_debug(msg: str):
        logger.debug(msg) if logger else print(f"[DEBUG] {msg}")

    def log_info(msg: str):
        logger.info(msg) if logger else print(msg)

    log_debug(f"📦 Project Root: {root}")

    folder_keys = [k for k in config if k.endswith("_dir")]

    for key in folder_keys:
        folder_raw = config.get(key)
        if not isinstance(folder_raw, (str, Path)):
            raise ValueError(f"{key} must be a string or Path, got: {type(folder_raw)}")

        folder_path = Path(folder_raw).expanduser().resolve()

        try:
            folder_path.relative_to(root)
        except ValueError:
            raise ValueError(f"Refusing to create '{folder_path}': outside of project root '{root}'")

        if not folder_path.exists():
            folder_path.mkdir(parents=True, exist_ok=True)
            log_info(f"📁 Created: {folder_path}")
        else:
            log_debug(f"✅ Exists:  {folder_path}")
