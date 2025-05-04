# config_env_initializer — Feature Overview

`config_env_initializer` is a reusable Python package designed to standardize and secure configuration handling for script-based projects. It provides structured loading, validation, logging setup, folder initialization, and safe secret handling.

---

## Core Purpose

The goal of this package is to:

- Load a YAML configuration file
- Normalize and validate it using a Python-based schema
- Handle optional external auth credentials securely
- Prepare the logger using config-defined parameters
- Initialize project folder structure (logs, output, db, etc.)
- Provide a structured, ready-to-use config dictionary for scripts

---

## Core Features

### Config Loading

- Entry point: `ConfigLoader(config_path_str, schema_path_str=None)`
- Converts string paths to `Path` objects with cross-platform compatibility
- Falls back to `schema/schema.py` if no schema path is provided
- Validates that the YAML is a dictionary at the top level

### Schema Validation

- External schema is a Python file defining:
  - Keys
  - Required status
  - Default values
  - Validation functions
- Supports static or schema-local custom validators
- Validates validator function names and presence
- Applies all validations before raising error
- Merges defaults and raises if required fields are missing

### Config Normalization

- Replaces spaces in config keys with underscores
- Converts all keys to a consistent case
- Detects and prevents key collisions after normalization

### Auth Handling

- Config keys ending in `_auth_path` point to secure YAML files
- External auth files must contain key-value pairs
- Loaded values are wrapped in `SensitiveValue`, which prevents accidental exposure via logs or print
- Resulting config gains a reserved `config["auth"]` block with nested secret stores (per system name)

### Logging

- Config options control:
  - `log_dir`
  - `log_level`
  - `log_microseconds`
  - `log_prefix`
- Logging includes:
  - Rotating log file handler
  - Console handler
- Microsecond-level precision is optional
- Loggers are injected into the config under `config["logger"]`

### Folder Structure Initialization

- All config keys ending in `_dir` are used to create folders if missing
- Directory creation is restricted to the project root (config file parent by default)
- Uses logger for messages when available; otherwise prints
- Differentiates between already existing and newly created folders

---

## CLI Entry Point

The package supports CLI usage via:

```bash
python -m config_env_initializer --validate config.yaml
python -m config_env_initializer --init-folders config.yaml
