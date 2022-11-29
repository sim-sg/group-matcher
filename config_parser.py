from importlib import util
from models import Configuration


CONFIG_MODULE_NAME = "config_module"


def verify_config(config_module: object):
    keys = vars(config_module)
    for field in Configuration.FIELDS:
        if field not in Configuration.OPTIONAL_FIELDS:
            assert (
                field in keys
            ), f"Configuration key '{field}' not found in configuration file!"


def import_config(file_path: str):
    # Import and execute module from source file
    spec = util.spec_from_file_location(CONFIG_MODULE_NAME, file_path)
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # Verify module configuration, raising AssertionError if invalid
    verify_config(module)

    # Wrap relevant parts of config in Configuration model object and return
    return Configuration(module)
