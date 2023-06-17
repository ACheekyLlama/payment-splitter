"""Command-line entrypoint."""
import argparse
import json

from .main import main


def parse_args() -> tuple[str, bool]:
    parser = argparse.ArgumentParser(
        prog="PaymentSplitter",
        description="Finds settle-up payments in Pocketsmith, and splits them into the constituent expenses from Splitwise.",
    )

    parser.add_argument(
        "config-file",
        default="config.json",
        help="Path to the config file.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't split the Pocketsmith transactions, just log what would have been created. Useful for verifying that it is working as expected.",
    )

    args = vars(parser.parse_args())

    return (args["config-file"], args["dry_run"])


def parse_config(config_file_path: str) -> tuple[str, str, list[int]]:
    try:
        with open(config_file_path, "r") as f:
            config = json.load(f)

            return (
                config["pocketsmith_api_key"],
                config["splitwise_api_key"],
                config["splitwise_groups"],
            )
    except OSError as e:
        raise Exception("Could not open configuration file.") from e
    except json.JSONDecodeError as e:
        raise Exception("Could not parse the configuration file.") from e
    except KeyError as e:
        raise Exception("Missing a key in the config file.") from e


config_file, dry_run = parse_args()
pocketsmith_key, splitwise_key, splitwise_groups = parse_config(config_file)
main(pocketsmith_key, splitwise_key, splitwise_groups, dry_run=dry_run)
