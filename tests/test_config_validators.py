import pytest
from config_env_initializer.config_validator import ConfigValidator, is_placeholder

# --- is_placeholder ---

@pytest.mark.parametrize("value,expected", [
    ("<REQUIRED>", True),
    ("<OPTIONAL>", True),
    ("<something>", True),
    ("value", False),
    ("<value", False),
    ("value>", False),
])
def test_is_placeholder(value, expected):
    assert is_placeholder(value) == expected


# --- log_level_valid ---

@pytest.mark.parametrize("level", ["debug", "INFO", "WaRnInG", "error", "CRITICAL"])
def test_log_level_valid_passes(level):
    ConfigValidator.log_level_valid(level, key="log_level")


@pytest.mark.parametrize("level", ["notice", 123, None])
def test_log_level_valid_fails(level):
    with pytest.raises(ValueError):
        ConfigValidator.log_level_valid(level, key="log_level")


# --- is_non_empty_str ---

def test_is_non_empty_str_passes():
    ConfigValidator.is_non_empty_str("valid", key="name")


@pytest.mark.parametrize("value", ["", "   ", None, 123])
def test_is_non_empty_str_fails(value):
    with pytest.raises(ValueError):
        ConfigValidator.is_non_empty_str(value, key="empty")


# --- is_bool_str ---

@pytest.mark.parametrize("value", ["true", "false", "TRUE", "False"])
def test_is_bool_str_passes(value):
    ConfigValidator.is_bool_str(value, key="flag")


@pytest.mark.parametrize("value", ["yes", "no", True, 1])
def test_is_bool_str_fails(value):
    with pytest.raises(ValueError):
        ConfigValidator.is_bool_str(value, key="bool_val")


# --- not_placeholder ---

def test_not_placeholder_passes():
    ConfigValidator.not_placeholder("real_value", key="field")


@pytest.mark.parametrize("value", ["<REQUIRED>", "<OPTIONAL>", "<pending>"])
def test_not_placeholder_fails(value):
    with pytest.raises(ValueError):
        ConfigValidator.not_placeholder(value, key="field")


# --- int_in_range ---

def test_int_in_range_passes():
    validator = ConfigValidator.int_in_range(min_value=1, max_value=5)
    for i in range(1, 6):
        validator(i, key="number")


@pytest.mark.parametrize("value", [0, 6, "3", None])
def test_int_in_range_fails(value):
    validator = ConfigValidator.int_in_range(min_value=1, max_value=5)
    with pytest.raises(ValueError):
        validator(value, key="number")
