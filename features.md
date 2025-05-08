# config_env_initializer — Feature Overview

`config_env_initializer` is a reusable Python package designed to standardize and secure configuration handling for script-based projects. It provides structured loading, schema-driven validation, logging setup, folder initialization, and secure secret management.

---

## Core Purpose

The goal of this package is to:

- Load a YAML configuration file
- Normalize and validate it using a Python-based schema
- Support extensible, decorator-based custom validators
- Handle optional external auth credentials securely
- Prepare the logger using config-defined parameters
- Initialize project folder structure (logs, output, db, etc.)
- Provide a structured, ready-to-use config dictionary for scripts

---

## Core Features

### Config Loading

- Entry point: `ConfigLoader(config_path_str, schema_path_str=None)`
- Converts input paths to `Path` objects with platform independence
- Defaults to `schema/schema.py` if no schema path is provided
- Ensures the loaded YAML config is a dictionary
- Automatically loads referenced auth credentials

### Schema Validation

- External schema is a Python file defining:
  - Keys
  - Types
  - Required status
  - Default values
  - Validators
- Supports:
  - Built-in validators (e.g. `log_level_valid`)
  - Decorator-registered custom validators via `@CustomValidator.register()`
  - Parameterized validators with kwargs (`{"name": ..., ...}`)
- Unified resolver loads all registered validator sources
- Validation applies all checks before raising comprehensive error output
- Default values are merged in; missing required fields trigger errors

### Config Normalization

- Standardizes config keys by:
  - Replacing spaces with underscores
  - Lowercasing keys (or applying consistent casing rules)
- Prevents collisions from normalization mismatches

### Auth Handling

- Config keys ending in `_auth_path` load secure YAML files
- Auth files must contain flat key-value structures
- Values are wrapped in `SensitiveValue` to prevent log exposure
- Loaded into a special `config["auth"]` block under their system names

### Logging

- Configurable options include:
  - `log_dir`
  - `log_level`
  - `log_microseconds`
  - `log_prefix`
- Logging setup includes:
  - Console handler
  - Rotating file handler
- Microsecond precision is optional
- Logger instance injected into `config["logger"]`

### Folder Structure Initialization

- Controlled by schema fields:
  - `project_dirs`, `sub_project_dirs`, and `sub_projects`
- Config keys ending in `_dir` also trigger directory creation
- Scoped to the project root (inferred from the config path)
- Logs or prints creation status with clear differentiation between new and existing folders

---

## CLI Entry Point

The package supports direct CLI usage via the `config-init` command:

```bash
config-init validate-config configs/dev.yaml
config-init validate-schema
config-init generate-config
config-init init-folders
