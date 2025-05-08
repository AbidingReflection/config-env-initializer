from config_env_initializer.config_validator import CustomValidator

@CustomValidator.register()
def string_in_string(value, *, input_str, key=None):
    if not isinstance(value, str):
        raise ValueError(f"{key} must be a string.")
    if input_str not in value:
        raise ValueError(f"{key} must contain the substring '{input_str}'. Got: '{value}'")


project_dirs = ["configs", "db", "auth"]
sub_project_dirs = ["logs", "output"]
sub_projects = ["extract_1", "extract_2"]
auth_systems = ["qtest", "jira"]

schema = {
    "project_name": {
        "type": str,
        "required": True,
        "validators": [],
        "default": None
    },
    "log_dir": {
        "type": str,
        "required": True,
        "validators": [],
        "default": "logs"
    },
    "log_level": {
        "type": str,
        "required": False,
        "validators": ["log_level_valid"],
        "default": "INFO"
    },
    "log_microseconds": {
        "type": bool,
        "required": False,
        "validators": [],  
        "default": False
    },
    "output_dir": {
        "type": str,
        "required": False,
        "validators": [{"name": "string_in_string", "input_str": "out"}],  
        "default": "output"
    },
    "db_dir": {
        "type": str,
        "required": True,
        "validators": [],
        "default": None
    },
    "qtest_auth_path": {
        "type": str,
        "required": False,
        "validators": [],
        "default": None
    },
    "timeout": {
        "type": int,
        "required": True,
        "validators": [{"name": "int_in_range", "min_value": 5, "max_value": 60}],
        "default": 10
    },
    "retries": {
        "type": int,
        "required": False,
        "validators": [{"name": "int_in_range", "min_value": 0, "max_value": 10}],
        "default": 3
    },
}
