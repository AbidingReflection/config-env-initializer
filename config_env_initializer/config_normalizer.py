def normalize_config_keys(config: dict) -> dict:
    """
    Normalize keys by replacing spaces with underscores and lowercasing them.
    Raises an error if key collisions occur during normalization.

    Args:
        config (dict): Raw config dictionary loaded from YAML.

    Returns:
        dict: Normalized config dictionary.
    """
    normalized = {}
    collisions = []

    for key, value in config.items():
        new_key = key.strip().replace(" ", "_").lower()

        if new_key in normalized:
            collisions.append((key, new_key))
        else:
            normalized[new_key] = value

    if collisions:
        messages = [f"'{original}' → '{normalized_key}'" for original, normalized_key in collisions]
        raise ValueError(
            "Config key collisions detected after normalization:\n" +
            "\n".join(messages)
        )

    return normalized
