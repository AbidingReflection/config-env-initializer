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

Custom validators allow project-specific logic to be applied during validation. You can define and register them by extending the base class and including a `custom_validators` dictionary in your `schema.py`.

### Example:

```python
from config_env_initializer.config_validator import ConfigValidator

class CustomValidator(ConfigValidator):
    @staticmethod
    def must_be_uppercase(value, key=None):
        if not isinstance(value, str):
            raise ValueError(f"{key} must be a string.")
        if value.upper() != value:
            raise ValueError(f"{key} must be uppercase.")

    @staticmethod
    def length_at_least(min_length):
        def validator(value, key=None):
            if not isinstance(value, str):
                raise ValueError(f"{key} must be a string.")
            if len(value) < min_length:
                raise ValueError(f"{key} must be at least {min_length} characters long.")
        return validator

custom_validators = {
    **CustomValidator.get_all_validators()
}
```

### Using the custom validators in your schema:

```python
schema = {
    "name": {
        "type": str,
        "required": True,
        "validators": ["must_be_uppercase", {"name": "length_at_least", "min_length": 5}]
    }
}
```

* For simple validators, use the function name as a string.
* For parameterized validators, use a dictionary with a `"name"` key and arguments matching the validator factory’s parameters.

---

## CLI Command Reference

```bash
config-init [COMMAND] [ARGS]
```

### `generate-config [SCHEMA_PATH]`

Generate an example YAML configuration based on the provided schema.

* Defaults to `schema/schema.py`
* Output is written to `configs/generated_config_<timestamp>.yaml`
* Fields with no default are marked `<REQUIRED>` or `<OPTIONAL>`

### `validate-config <CONFIG_PATH> [SCHEMA_PATH]`

Validate a configuration YAML file against a schema.

* Ensures required fields are present
* Type-checks all values
* Executes all validators (custom and built-in)
* Detects placeholder values such as `<REQUIRED>`
* Returns a list of all validation errors

### `validate-schema [SCHEMA_PATH]`

Validate the schema structure itself.

* Checks for missing or invalid validators
* Ensures schema structure is valid
* Helpful for CI enforcement or local dev sanity checks

### `init-folders [SCHEMA_PATH]`

Create folders as described by schema-based rules.

* Intended to enforce consistent project structure
* User confirmation is required before folders are created

---

## Command Line Help

```bash
config-init --help
```

Example output:

```
Config Environment Initializer CLI

Commands:
  validate-config <CONFIG> [SCHEMA]     Validate a config file against the schema.
  validate-schema [SCHEMA]              Validate a schema file (default: schema/schema.py).
  init-folders [SCHEMA]                 Create required directories based on schema rules.
  generate-config [SCHEMA]              Generate a YAML config template from the schema.

usage: config-init [-h] {validate-config,validate-schema,init-folders,generate-config} ...

positional arguments:
  {validate-config,validate-schema,init-folders,generate-config}
    validate-config     Validate a config file against the schema.
    validate-schema     Validate a schema file.
    init-folders        Create required project directories from schema.
    generate-config     Generate an example YAML config from the schema.

options:
  -h, --help            show this help message and exit
```

---

## Development and Testing

All functionality is covered by unit tests in the `tests/` folder. To run the test suite:

```bash
pytest
```

---

## License

This project is licensed under the MIT License. See `LICENSE` for details.
