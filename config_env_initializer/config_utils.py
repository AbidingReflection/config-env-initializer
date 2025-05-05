from pathlib import Path
from datetime import datetime, timezone
import importlib.util
import sys
import yaml

from config_env_initializer.config_validator import ConfigValidator


def import_schema_module(schema_path: Path):
    """Dynamically import the schema module."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    spec = importlib.util.spec_from_file_location("schema_module", schema_path)
    schema_module = importlib.util.module_from_spec(spec)
    sys.modules["schema_module"] = schema_module
    spec.loader.exec_module(schema_module)

    return schema_module


def import_schema(schema_path: Path):
    schema_module = import_schema_module(schema_path)
    if not hasattr(schema_module, "schema"):
        raise AttributeError(f"{schema_path} must define a 'schema' dictionary")
    return schema_module.schema


def import_validators(schema_path: Path):
    from config_env_initializer.config_validator import ConfigValidator
    base_validators = ConfigValidator.get_all_validators()

    schema_module = import_schema_module(schema_path)
    custom = getattr(schema_module, "custom_validators", {})

    return {**base_validators, **custom}



def generate_config(schema_path: Path = Path("schema/schema.py")):
    """Generates a config YAML file based on the provided schema."""
    try:
        print(f"Loading schema from: {schema_path}")
        schema = import_schema(schema_path)
    except Exception as e:
        print(f"Failed to load schema: {e}")
        return

    output_dir = Path("configs")
    output_dir.mkdir(parents=True, exist_ok=True)

    utc_now = datetime.now(timezone.utc)
    timestamp = utc_now.strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"generated_config_{timestamp}.yaml"

    if output_file.exists():
        response = input(f"{output_file} already exists. Overwrite? (y/n): ")
        if response.strip().lower() != "y":
            print("Aborted config generation.")
            return

    lines = [
        "# Auto-generated config file",
        f"# Schema source: {schema_path}",
        f"# Generated: {utc_now.isoformat()}",
        ""
    ]

    for key, attributes in schema.items():
        default = attributes.get("default", None)
        required = attributes.get("required", True)

        if default is not None:
            value = default
            comment = ""
        elif not required:
            value = "<OPTIONAL>"
            comment = "optional"
        else:
            value = "<REQUIRED>"
            comment = "required"

        line = yaml.dump({key: value}, default_flow_style=False).strip()
        lines.append(f"{line}  # {comment}" if comment else line)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"Generated config written to: {output_file}")


def validate_config(config_path: Path, schema_path: Path = Path("schema/schema.py")):
    """Validate a config YAML file against the schema and return a list of error strings."""
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}

    schema = import_schema(schema_path)
    validators = import_validators(schema_path)

    errors = []

    for key, rules in schema.items():
        value = config.get(key, None)

        if isinstance(value, str) and value.strip().startswith("<") and value.strip().endswith(">"):
            errors.append(f"{key}: contains placeholder value '{value}', must be replaced")
            continue

        if value is None:
            if rules.get("required", True):
                errors.append(f"{key}: missing required field")
            continue


        expected_type = rules.get("type")
        if expected_type and not isinstance(value, expected_type):
            errors.append(f"{key}: expected {expected_type.__name__}, got {type(value).__name__}")

        for validator_spec in rules.get("validators", []):
            try:
                if isinstance(validator_spec, str):
                    if validator_spec not in validators:
                        errors.append(f"{key}: unknown validator '{validator_spec}'")
                        continue
                    validators[validator_spec](value, key=key)

                elif isinstance(validator_spec, dict):
                    name = validator_spec.get("name")
                    if name not in validators:
                        errors.append(f"{key}: unknown validator '{name}'")
                        continue
                    validator_func = validators[name](**{k: v for k, v in validator_spec.items() if k != "name"})
                    validator_func(value, key=key)

                else:
                    errors.append(f"{key}: invalid validator spec: {validator_spec}")

            except Exception as e:
                errors.append(f"{key}: validation error - {e}")

    return errors
