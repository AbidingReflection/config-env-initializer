from pathlib import Path
import yaml
import importlib.util
from pprint import pformat

from config_env_initializer.schema_utils import validate_config_against_schema
from config_env_initializer.sensitive import SensitiveValue, mask_config_for_logging
from config_env_initializer.config_utils import normalize_config_keys
from config_env_initializer.logger_setup import prepare_logger
from config_env_initializer.execution_monitor import Execution_Monitor
from config_env_initializer.exceptions import ValidationError


class ConfigLoader:
    """Loads, validates, and enriches a YAML config with logging, auth, and monitoring."""

    def __init__(self, config_path_str: str, schema_path_str: str = None):
        """Initializes the config loader and sets up auth, logger, and execution monitor."""
        self.config_path = self._resolve_path(config_path_str)
        self.schema_path = self._resolve_path(schema_path_str) if schema_path_str else self._default_schema_path()

        self._assert_exists(self.config_path, "YAML config")
        self._assert_exists(self.schema_path, "Schema")

        self.raw_config = self._load_yaml(self.config_path)
        self.schema_module = self._load_schema_module(self.schema_path)

        self.config = self._load_and_validate_config(self.raw_config, self.schema_module)
        self.auth = self._load_auth_data()
        self.logger = self._setup_logger()

        self.config["auth"] = self.auth
        self.config["logger"] = self.logger
        self.logger.info(f"Logger successfully initialized: {self.logger}")
        self.auth_keys = list(self.auth.keys())

        script_name = self.config.get('script_name', 'script_execution')
        execution_monitor: Execution_Monitor = Execution_Monitor(self.config, script_name)
        self.config["execution_monitor"] = execution_monitor
        self.logger.info("Execution monitor successfully initialized.\nConfig:\n%s", pformat(self.config))


        self.logger.info(f"Loaded and validated config:",)

    def _load_and_validate_config(self, raw_config: dict, schema_module) -> dict:
        """Normalizes and validates raw config against a schema."""
        normalized_config = normalize_config_keys(raw_config)
        try:
            return validate_config_against_schema(normalized_config, schema_module)
        except ValidationError:
            raise

    def _setup_logger(self):
        """Creates a logger based on config settings."""
        log_path = Path(self.config["log_dir"])
        use_micro = self.config["log_microseconds"]
        log_level = self.config["log_level"]
        prefix = self.config.get("log_prefix", "")
        return prepare_logger(
            self.config,
            log_path,
            output_name_prefix=prefix,
            use_microseconds=use_micro,
            log_level=log_level,
        )

    def _load_auth_data(self) -> dict:
        """Loads and wraps sensitive auth values from *_auth_path keys."""
        auth_data = {}
        for key, value in self.config.items():
            if key.endswith("_auth_path"):
                system = key.replace("_auth_path", "")
                path = self._resolve_path(value)
                self._assert_exists(path, f"{system} auth")
                raw_auth = self._load_yaml(path)
                if not isinstance(raw_auth, dict):
                    raise ValueError(f"{key} must point to a YAML file with key-value pairs.")
                # Wrap values as SensitiveValue for masking
                auth_data[system] = {k: SensitiveValue(v) for k, v in raw_auth.items()}
        return auth_data

    def _resolve_path(self, path_str: str) -> Path:
        """Normalizes and resolves a filesystem path."""
        if isinstance(path_str, str):
            path_str = path_str.replace("\\", "/")  # Windows path fix
        return Path(path_str).expanduser().resolve()

    def _default_schema_path(self) -> Path:
        """Returns the default schema path if not specified."""
        return (Path.cwd() / "schema" / "schema.py").resolve()

    def _assert_exists(self, path: Path, label: str):
        """Raises if the given path does not exist as a file."""
        if not path.is_file():
            raise FileNotFoundError(f"{label} file not found at: {path}")

    def _load_yaml(self, path: Path) -> dict:
        """Parses a YAML file and returns its dictionary contents."""
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not isinstance(data, dict):
            raise ValueError("YAML config must be a dictionary at the top level.")
        return data

    def _load_schema_module(self, path: Path):
        """Loads a Python schema module from a file."""
        spec = importlib.util.spec_from_file_location("config_schema", path)
        schema_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(schema_module)
        return schema_module

    def get_masked_config(self) -> dict:
        """Returns the config with sensitive values masked for logging."""
        return mask_config_for_logging(self.config)
