
# config-env-initializer

A lightweight and extensible tool for config management, schema validation, and project scaffolding.

---

## Installation

Install directly from GitHub:

```bash
pip install git+https://github.com/AbidingReflection/config-env-initializer.git
````

Or add the following to your `requirements.txt`:

```
git+https://github.com/AbidingReflection/config-env-initializer.git
```

---

## Usage in Your Project

### Define your schema in `schema/schema.py`

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

## Adding Custom Validators

Custom validators can now be registered using a decorator. This avoids manual boilerplate and allows validators to be defined directly in the schema file or project module.

### Example:

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

### Using custom validators in your schema:

```python
schema = {
    "name": {
        "type": str,
        "required": True,
        "validators": [
            "must_be_uppercase",
            {"name": "length_at_least", "min_length": 5}
        ]
    }
}
```

* Use a **string** for simple validators.
* Use a **dictionary** for parameterized validators. The `"name"` key must match the registered function name.

---

## CLI Command Reference

```bash
config-init [COMMAND] [ARGS]
```

### `generate-config [SCHEMA_PATH]`

Generate a YAML configuration template from the schema.

* Defaults to `schema/schema.py`
* Outputs to `configs/generated_config_<timestamp>.yaml`
* Marks missing values with `<REQUIRED>` or `<OPTIONAL>`

### `validate-config <CONFIG_PATH> [SCHEMA_PATH]`

Validate a config YAML file against a schema.

* Ensures required fields are present
* Verifies types and runs all validators
* Detects unresolved placeholder values
* Returns a full list of validation errors

### `validate-schema [SCHEMA_PATH]`

Validate the schema itself.

* Verifies structure and validator references
* Helps catch typos or missing logic early

### `init-folders [SCHEMA_PATH]`

Create folders based on schema rules.

* Uses `project_dirs`, `sub_project_dirs`, and `sub_projects` from the schema
* Prompts before creating folders

---

## Command Line Help

```bash
config-init --help
```

Example:

```
Config Environment Initializer CLI

Commands:
  validate-config <CONFIG> [SCHEMA]     Validate a config file against the schema.
  validate-schema [SCHEMA]              Validate a schema file (default: schema/schema.py).
  init-folders [SCHEMA]                 Create required directories based on schema rules.
  generate-config [SCHEMA]              Generate a YAML config template from the schema.

usage: config-init [-h] {validate-config,validate-schema,init-folders,generate-config} ...

options:
  -h, --help            show this help message and exit
```

---

## Development and Testing

Unit tests are located in the `tests/` directory.

To run the test suite:

```bash
pytest
```

---

## License

This project is licensed under the MIT License. See `LICENSE` for details.

```
