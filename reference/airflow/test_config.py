import yaml
import os


def test_config_file(config_path):
    """
    Function to test and validate the config.yaml file structure and contents.
    """
    try:
        # Load the config file
        with open(config_path, "r") as file:
            config = yaml.safe_load(file)

        # Check required sections
        required_sections = ["mlflow", "kafka"]
        for section in required_sections:
            if section not in config:
                raise KeyError(f"Missing required section: {section}")

        # Validate mlflow section
        mlflow_keys = ["registered_model_name", "tracking_uri", "artifact_location", "s3_endpoint_url"]
        for key in mlflow_keys:
            if key not in config["mlflow"]:
                raise KeyError(f"Missing required key in mlflow: {key}")

        # Validate kafka section
        kafka_keys = ["bootstrap_servers", "username", "password", "topic", "output_topic"]
        for key in kafka_keys:
            if key not in config["kafka"]:
                raise KeyError(f"Missing required key in kafka: {key}")

        # All checks passed
        print("config.yaml is valid!")

    except yaml.YAMLError as e:
        print(f"YAML format error: {e}")
    except KeyError as e:
        print(f"Configuration error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


# Path to your config.yaml file
config_path = "config.yaml"

# Ensure the file exists
if os.path.exists(config_path):
    test_config_file(config_path)
else:
    print(f"Configuration file not found at {config_path}")
