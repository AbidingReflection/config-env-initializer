import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Tuple

DEFAULT_EXCLUDE_CONFIG: Dict[str, List[str]] = {
    "prefixes": ["generated_config_"],
    "suffixes": [".swp", ".egg-info"],
    "filetypes": ["pyc", "log"],
    "folders": [
        '.git', 'venv', '__pycache__', 'logs', '.pytest_cache',
        'output', 'archive', '.DS_Store', 'build'
    ]
}

def get_timestamp() -> str:
    return datetime.now(timezone.utc).strftime('%y%m%dZ%H%M%S')

def extract_number(entry: str) -> int:
    match = re.match(r'^(\d+)', entry)
    return int(match.group(1)) if match else float('inf')

def archive_existing_file_trees(output_prefix: Path) -> None:
    archive_dir = output_prefix.parent / 'archive'
    archive_dir.mkdir(exist_ok=True)

    for file_path in output_prefix.parent.glob(f"{output_prefix.stem}*.txt"):
        try:
            timestamp = get_timestamp()
            archived_name = f"{file_path.stem}_archived_{timestamp}.txt"
            archived_path = archive_dir / archived_name
            file_path.rename(archived_path)
            print(f"Archived: {file_path.name} → {archived_path.name}")
        except OSError as e:
            print(f"Failed to archive {file_path.name}: {e}")

class ExclusionFilter:
    def __init__(self, prefixes: List[str], suffixes: List[str], filetypes: List[str], folders: List[str]):
        self.prefixes = prefixes
        self.suffixes = suffixes
        self.filetypes = {ftype.lstrip('.') for ftype in filetypes}
        self.folders = set(folders)

    def __call__(self, entry: Path) -> bool:
        return (
            any(entry.name.startswith(prefix) for prefix in self.prefixes) or
            any(entry.name.endswith(suffix) for suffix in self.suffixes) or
            entry.suffix.lstrip('.') in self.filetypes or
            entry.name in self.folders
        )

def format_exclusions(exclude_config: Dict[str, List[str]]) -> str:
    output = "Exclusions:\n"
    for key, values in exclude_config.items():
        output += f"  {key.capitalize()}:\n"
        output += ''.join(f"    - {val}\n" for val in values) if values else "    - None\n"
    return output

def generate_file_tree(
    target_path: Path,
    output_path: Path,
    exclude_config: Dict[str, List[str]],
    archive_previous: bool = True
) -> None:
    exclude_filter = ExclusionFilter(
        exclude_config.get("prefixes", []),
        exclude_config.get("suffixes", []),
        exclude_config.get("filetypes", []),
        exclude_config.get("folders", [])
    )

    if archive_previous:
        archive_existing_file_trees(output_path)

    timestamp = get_timestamp()
    output_base = output_path.with_suffix('')
    output_file = f"{output_base}_{timestamp}.txt"

    file_count = 0
    folder_count = 0

    with open(output_file, 'w', encoding='utf-8') as file:
        file.write(f"Target Path: {target_path.resolve()}\n")
        file.write(f"Output Path: {Path(output_file).resolve()}\n\n")
        file.write(f"{target_path.name}/\n")

        def walk_directory(current_path: Path, prefix: str = "") -> Tuple[int, int]:
            nonlocal file_count, folder_count
            try:
                entries = sorted(current_path.iterdir(), key=lambda e: (extract_number(e.name), e.name))
                entries = [e for e in entries if not exclude_filter(e)]

                for i, entry in enumerate(entries):
                    connector = "└─" if i == len(entries) - 1 else "├─"
                    line = f"{prefix}{connector} {entry.name}"
                    if entry.is_dir():
                        file.write(line + "/\n")
                        folder_count += 1
                        new_prefix = prefix + ("    " if connector == "└─" else "│   ")
                        walk_directory(entry, new_prefix)
                    else:
                        file.write(line + "\n")
                        file_count += 1
            except PermissionError:
                file.write(f"{prefix}└─ [Permission Denied: {current_path}]\n")
            except Exception as e:
                file.write(f"{prefix}└─ [Error accessing {current_path}: {e}]\n")

        walk_directory(target_path)

        file.write("\n" + format_exclusions(exclude_config))
        file.write(f"\nSummary:\n  Folders: {folder_count}\n  Files: {file_count}\n")

def find_project_root(start_path: Path = None) -> Path:
    start_path = start_path or Path.cwd()
    for parent in [start_path] + list(start_path.parents):
        if (parent / "pyproject.toml").exists() or (parent / ".git").exists():
            return parent
    return start_path

if __name__ == "__main__":
    import config_env_initializer

    # Start from the location of the installed package
    package_root = Path(config_env_initializer.__file__).resolve().parent

    # Walk upward until we find the project root (contains pyproject.toml or .git)
    def find_project_root(start: Path) -> Path:
        for parent in [start] + list(start.parents):
            if (parent / "pyproject.toml").exists() or (parent / ".git").exists():
                return parent
        return start  # fallback to whatever we got

    project_root = find_project_root(package_root)

    output_dir = project_root / "scripts" / "file_tree_output"
    output_dir.mkdir(parents=True, exist_ok=True)

    generate_file_tree(project_root, output_dir / "file_tree", DEFAULT_EXCLUDE_CONFIG)
