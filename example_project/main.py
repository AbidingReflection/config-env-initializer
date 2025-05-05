from pprint import pprint
from config_env_initializer.config_loader import ConfigLoader

def main():
    config_path = "configs/generated_config_20250505_021344.yaml"

    loader = ConfigLoader(config_path)
    config = loader.config

    print("\nLoaded and validated config:")
    pprint(config)

if __name__ == "__main__":
    main()
