from config_env_initializer.config_validator import ConfigValidator

schema = {
    "log_dir": {
        "required": True,
        "type": str,
        "default": "logs",
        "validators": ["nonempty_string"]
    },
    "db_path": {
        "required": True,
        "type": str,
        "default": "db/data.db"
    },
    "debug": {
        "required": False,
        "type": bool,
        "default": False
    }
}

def custom_validators():
    return {
        "nonempty_string": ConfigValidator.nonempty_string
    }
