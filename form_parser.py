import pandas as pd
from email.utils import parseaddr
from models import Row, Node


def is_all_digits(d):
    return all(ord("0") <= ord(x) <= ord("9") for x in str(d))


def is_float(x):
    try:
        float(x)
        return True
    except ValueError:
        return False


def is_valid_email(email):
    parsed_email = parseaddr(email)
    return len(parsed_email[0]) > 0 or len(parsed_email[1]) > 0


class TypeValidator(object):
    def __init__(self, validator=lambda x: True, transformer=lambda x: x):
        self.validator = validator
        self.transformer = transformer

    def __call__(self, typ, arg):
        if not self.validator(arg):
            raise UserWarning(f"Argument '{arg}' is not valid for type '{typ}'")
        return self.transformer(arg)


GLOBAL_TYPE_LIST = {
    "ignore": TypeValidator(),
    "text": TypeValidator(transformer=lambda x: x.strip() if x else x),
    "sid": TypeValidator(validator=is_all_digits, transformer=int),
    "email": TypeValidator(validator=is_valid_email),
    "boolean": TypeValidator(
        validator=lambda x: x in ["Yes", "No"], transformer=lambda x: x == "Yes"
    ),
    "checkbox": TypeValidator(
        transformer=lambda x: [elem.strip() for elem in x.split(",")]
    ),
    "radio": TypeValidator(),
    "dropdown": TypeValidator(),
    "scale": TypeValidator(validator=is_all_digits, transformer=int),
    "float": TypeValidator(validator=is_float, transformer=float),
    "int": TypeValidator(validator=is_all_digits, transformer=int),
}


def parse_column(col, val):
    # If nil value and optional column, ignore.
    if col.is_optional and not val:
        return None

    # Otherwise, transform it based on its associated default global transformer.
    type_transformed = GLOBAL_TYPE_LIST[col.col_type](col.col_type, val)

    # And wrap a column object around it (see Column.__call__ for implementation).
    return col(type_transformed)


def parse_from_csv(csv_path: str, row_config: Row, debug: bool = False) -> list:
    # Parse given CSV into a Pandas DataFrame object
    data = pd.read_csv(csv_path, dtype=str)

    # Construct a mapping from column index to Column object
    csv_columns = data.columns.values
    col_mapping = {x: None for x in range(len(csv_columns))}
    for col in row_config.cols:
        match = None
        matches = [name for name in csv_columns if col.col_title == name]
        if not matches:
            matches = [name for name in csv_columns if col.col_title in name]
            assert (
                matches
            ), f"No column title containing '{col.col_title}', as specified in the configuration file, was found in the given CSV!"
        match = matches[0]
        col_mapping[list(csv_columns).index(match)] = col

    # Print debug info if requested.
    if debug:
        print(col_mapping)

    # Parse each row properly into a Node object.
    nodes = []
    for row in data.itertuples(index=False, name=None):
        props = {}

        # Go through each column in the config file.
        for row_idx in col_mapping:
            # Figure out which column we're looking at.
            col = col_mapping[row_idx]
            if col is None:
                continue

            # Grab the value and account for Pandas' interesting design choices when it comes
            # to automatically deducing data types (overeager float conversion).
            value = row[row_idx]
            if isinstance(value, float) and str(value) == "nan":
                value = ""

            # Hand off the property to the column parser so it can be parsed with respect to
            # its type.
            props[col.col_id] = parse_column(col, value)

        # Add the constructed node to our final list.
        nodes.append(Node([props]))

    # And send off our result!
    return nodes
