from pathlib import Path
from typing import List

def initialize_folders(folders: List[Path], project_root: Path = None, logger=None):
    """
    Create all specified folders, constrained to the project root.

    Args:
        folders (list[Path or str]): List of folder paths to create.
        project_root (Path): Optional base path. Defaults to cwd.
        logger (optional): Logger object (optional).

    Raises:
        ValueError: If any target directory is outside the project root.
    """
    root = Path(project_root).resolve() if project_root else Path.cwd().resolve()

    def log_debug(msg: str):
        logger.debug(msg) if logger else print(f"[DEBUG] {msg}")

    def log_info(msg: str):
        logger.info(msg) if logger else print(msg)

    log_debug(f"Project root: {root}")

    for raw_path in folders:
        path = Path(raw_path).expanduser().resolve()

        if path.is_symlink():
            raise ValueError(f"Refusing to create symbolic link path: {path}")

        try:
            path.relative_to(root)
        except ValueError:
            raise ValueError(f"Refusing to create '{path}': outside of project root '{root}'")

        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            log_info(f"Created: {path}")
        else:
            log_debug(f"Exists:  {path}")



def get_folder_paths(schema_module, project_root: Path) -> list[Path]:
    """Return a list of full folder paths to be created based on schema directives."""
    project_dirs = getattr(schema_module, "project_dirs", [])
    sub_project_dirs = getattr(schema_module, "sub_project_dirs", [])
    sub_projects = getattr(schema_module, "sub_projects", [])

    all_folders = []

    for key in project_dirs:
        if isinstance(key, str):
            all_folders.append(project_root / key)

    for key in sub_project_dirs:
        if isinstance(key, str):
            base = project_root / key
            all_folders.append(base)

            if isinstance(sub_projects, list):
                for sub in sub_projects:
                    all_folders.append(base / sub)

    # Only return folders that don't already exist
    folders_to_create = [folder for folder in all_folders if not folder.exists()]
    return folders_to_create
