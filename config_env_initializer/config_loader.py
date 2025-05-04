from pathlib import Path
import yaml
import importlib.util

from config_env_initializer.schema_utils import validate_config_against_schema
from config_env_initializer.sensitive import SensitiveValue, mask_config_for_logging
from config_env_initializer.config_normalizer import normalize_config_keys
from config_env_initializer.logger_setup import prepare_logger


class ConfigLoader:
    def __init__(self, config_path_str: str, schema_path_str: str = None):
        self.config_path = self._resolve_path(config_path_str)
        self.schema_path = self._resolve_path(schema_path_str) if schema_path_str else self._default_schema_path()

        self._assert_exists(self.config_path, "YAML config")
        self._assert_exists(self.schema_path, "Schema")

        # Load and normalize config
        raw_config = self._load_yaml(self.config_path)
        normalized_config = normalize_config_keys(raw_config)

        # Load and apply schema
        schema_module = self._load_schema_module(self.schema_path)
        validated_config = validate_config_against_schema(normalized_config, schema_module)

        # Load auth blocks
        auth_data = self._load_auth_paths(validated_config)
        validated_config["auth"] = auth_data

        # Prepare logger based on config
        log_path = Path(validated_config["log_dir"])
        use_micro = validated_config["log_microseconds"]
        log_level = validated_config["log_level"]
        prefix = validated_config.get("log_prefix", "")
        logger = prepare_logger(log_path, output_name_prefix=prefix, use_microseconds=use_micro, log_level=log_level)
        validated_config["logger"] = logger

        # Final assignments
        self.config = validated_config
        self.auth = auth_data
        self.logger = logger
        self.auth_keys = list(auth_data.keys())

    def _resolve_path(self, path_str: str) -> Path:
        return Path(path_str).expanduser().resolve()

    def _default_schema_path(self) -> Path:
        return (Path(__file__).parent.parent / "schema" / "schema.py").resolve()

    def _assert_exists(self, path: Path, label: str):
        if not path.is_file():
            raise FileNotFoundError(f"{label} file not found at: {path}")

    def _load_yaml(self, path: Path) -> dict:
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not isinstance(data, dict):
            raise ValueError("YAML config must be a dictionary at the top level.")
        return data

    def _load_schema_module(self, path: Path):
        spec = importlib.util.spec_from_file_location("config_schema", path)
        schema_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(schema_module)
        return schema_module

    def _load_auth_paths(self, config: dict) -> dict:
        auth_data = {}

        for key, value in config.items():
            if key.endswith("_auth_path"):
                system = key.replace("_auth_path", "")
                path = self._resolve_path(value)
                self._assert_exists(path, f"{system} auth")

                with path.open("r", encoding="utf-8") as f:
                    raw_auth = yaml.safe_load(f)

                if not isinstance(raw_auth, dict):
                    raise ValueError(f"{key} must point to a YAML file with key-value pairs.")

                wrapped = {k: SensitiveValue(v) for k, v in raw_auth.items()}
                auth_data[system] = wrapped

        return auth_data

    def get_masked_config(self) -> dict:
        return mask_config_for_logging(self.config)
