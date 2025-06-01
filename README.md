# config-env-initializer

A lightweight, extensible Python tool for structured config management, schema validation, and project scaffolding.

---

## What It’s For

`config-env-initializer` helps Python developers safely load and validate YAML configuration files using Python-defined schemas. It also supports placeholder enforcement, reusable custom validators, secrets management, and automated folder scaffolding — ideal for script-heavy projects, internal tools, data pipelines, and CLI workflows.

---

## Installation

Install directly from GitHub:

```bash
pip install git+https://github.com/AbidingReflection/config-env-initializer.git
````

Or add this to your `requirements.txt`:

```
git+https://github.com/AbidingReflection/config-env-initializer.git
```

---

## Example Usage

### 1. Define your schema in `schema/schema.py`

```python
schema = {
    "project_name": {"type": str, "required": True},
    "timeout": {
        "type": int,
        "required": True,
        "validators": [{"name": "int_in_range", "min_value": 1, "max_value": 60}]
    },
    "log_level": {
        "type": str,
        "required": False,
        "validators": ["log_level_valid"],
        "default": "INFO"
    },
    "debug_mode": {"type": bool, "required": False, "default": False}
}
```

---

### 2. Generate a config template

```bash
config-init generate-config
```

Outputs:

```yaml
project_name: <REQUIRED>
timeout: <REQUIRED>
log_level: INFO
debug_mode: false
```

---

### 3. Validate a config file

```bash
config-init validate-config example_project/configs/dev.yaml
```

Returns a list of validation issues (if any) and confirms type safety, required values, and placeholder resolution.

---

## Custom Validators

You can register custom validators using a decorator, enabling rich validation logic directly in your schema.

### Example

```python
from config_env_initializer.config_validator import CustomValidator

@CustomValidator.register()
def must_be_uppercase(value, key=None):
    if not isinstance(value, str):
        raise ValueError(f"{key} must be a string.")
    if value.upper() != value:
        raise ValueError(f"{key} must be uppercase.")

@CustomValidator.register()
def length_at_least(value, *, min_length, key=None):
    if not isinstance(value, str):
        raise ValueError(f"{key} must be a string.")
    if len(value) < min_length:
        raise ValueError(f"{key} must be at least {min_length} characters long.")
```

Then reference them in your schema:

```python
"username": {
    "type": str,
    "required": True,
    "validators": [
        "must_be_uppercase",
        {"name": "length_at_least", "min_length": 5}
    ]
}
```

---

## CLI Command Reference

```bash
config-init [COMMAND] [ARGS]
```

| Command                                       | Description                                                     |
| --------------------------------------------- | --------------------------------------------------------------- |
| `generate-config [SCHEMA_PATH]`               | Generate a YAML config template with `<REQUIRED>` placeholders. |
| `validate-config <CONFIG_PATH> [SCHEMA_PATH]` | Validate a config file against the schema.                      |
| `validate-schema [SCHEMA_PATH]`               | Check the schema for structural and validator issues.           |
| `init-folders [SCHEMA_PATH]`                  | Create required folders defined by the schema logic.            |

Example:

```bash
config-init validate-config configs/dev.yaml
```

---

## Example Project

Check out [`example_project/`](./example_project) for:

* A working schema
* Sample config files
* Folder layout
* Auth/Secrets example

---

## Running Tests

```bash
pytest
```

Test cases are located in the `tests/` directory and include:

* Config validation logic
* Custom validator integration
* Schema behaviors
* Folder setup
