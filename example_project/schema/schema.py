from config_env_initializer.config_validator import ConfigValidator

class CustomValidator(ConfigValidator):
    @staticmethod
    def int_in_range(min_value: int, max_value: int):
        """Returns a validator that checks if an int is within [min_value, max_value]."""
        def validator(value, key=None):
            if not isinstance(value, int):
                raise ValueError(f"{key} must be an integer.")
            if not (min_value <= value <= max_value):
                raise ValueError(f"{key}={value} not in range [{min_value}, {max_value}]")
        return validator

custom_validators = {
    **CustomValidator.get_all_validators()
}


project_dirs = ["config", "db"]
sub_project_dirs = ["logs", "output"]
sub_projects = ["extract_1", "extract_2"]

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
        "validators": [],  
        "default": "output"
    },
    "db_dir": {
        "type": str,
        "required": False,
        "validators": [],
        "default": "db"
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
