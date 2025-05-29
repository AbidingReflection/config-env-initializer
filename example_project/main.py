from pprint import pprint
from config_env_initializer.config_loader import ConfigLoader

def main():
    config_path = r"configs\generated_config_20250508_024143.yaml"

    loader = ConfigLoader(config_path)
    config = loader.config

    print("\nLoaded and validated config:")
    pprint(config, indent=4)

if __name__ == "__main__":
    main()
