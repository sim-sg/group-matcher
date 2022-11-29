class Column(object):
    def __init__(
        self,
        col_title: str,
        col_id: str,
        col_type: str,
        is_optional: bool = False,
        validator=lambda x: True,
        transformer=lambda x: x,
    ):
        """
        Create a column configuration object with the given parameters.

        Args:
            col_title (str): Substring of title of column for Pandas DataFrame indexing (will match first column header which contains this substring)
            col_id (str): An ID to use for this column
            col_type (str): Any of: ignore, text, sid, email, boolean, checkbox, radio, dropdown, scale, float, or int.
            is_optional (bool, optional): Whether this column needs to be filled out
            validator (callable, optional): An optional function that takes in appropriately-typed output and returns True if valid
            transformer (callable, optional): An optional function that takes in appropriately-typed output and returns a new representation to use
        """
        self.col_title = col_title
        self.col_id = col_id
        self.col_type = col_type
        self.is_optional = is_optional
        self.validator = validator
        self.transformer = transformer

    def __call__(self, arg):
        if not self.validator(arg):
            raise UserWarning(
                f"Argument '{arg}' is not valid for column ID '{self.col_id}' of type '{self.col_type}'"
            )
        return self.transformer(arg)

    def __str__(self):
        return f"Column ID '{self.col_id}' of type '{self.col_type}' with title substring '{self.col_title}'"

    def __repr__(self):
        return self.__str__()


class Row(object):
    def __init__(self, cols: list):
        self.cols = cols


class Configuration(object):
    FIELDS = {
        "ROW_CONFIG": "row_config",
        "CONSTRAINTS": "constraints",
        "MIN_GROUP_SIZE": "min_group_size",
        "MAX_GROUP_SIZE": "max_group_size",
        "MIN_PARTITION_SIZE": "min_partition_size",
        "postprocess_partitions": "postprocess_partitions",
        "post_processing": "post_processing",
    }

    OPTIONAL_FIELDS = [
        "postprocess_partitions",
        "post_processing",
    ]

    def __init__(self, module):
        for field in Configuration.FIELDS:
            self.__dict__[Configuration.FIELDS[field]] = module.__dict__.get(
                field, None
            )


class Node(object):
    def __init__(
        self, props: list, size: int = 1, assigned: bool = False
    ):
        self.props = props
        self.size = size
        self.assigned = assigned

    def to_json(self, group_num=-1):
        return [{"group_num": group_num, **prop} for prop in self.props]

    def __add__(self, other_node):
        return Node(
            self.props + other_node.props,
            self.size + other_node.size,
            self.assigned or other_node.assigned,
        )

    def __str__(self):
        return f"Node of size '{self.size}' of assigned value '{self.assigned}'"

    def __repr__(self):
        return self.__str__()


class Match(object):
    def __init__(self, node: Node, source="path", path=None):
        """
        Initialize a Match object with the given node and (optionally) source and path.

        Args:
            size (int): Description
            node (Node): Description
            source (str, optional): Description
            path (None, optional): Description
        """
        self.node = node
        self.source = source  # either "path" (a partition path) or "existing" (students explicitly chose their group)
        self.path = path

    def to_json(self, group_num=-1):
        return self.node.to_json(group_num=group_num)

    @property
    def size(self):
        return self.node.size

    @size.setter
    def set_size(self, new_size):
        assert new_size >= 0, "New size should be non-negative"
        self.node.size = new_size

    def merge_with(self, other_match):
        self.size += other_match.size
        self.node.size += other_match.node.size
        self.node.props.extend(other_match.node.props)

    def __add__(self, other_match):
        return Match(
            self.node + other_match.node,
            self.source
            if self.source == other_match.source
            else f"combined_{self.source}_{other_match.source}",
            path=self.path if self.path else other_match.path,
        )

    def __str__(self):
        out = f"Match: size '{self.size}'"
        if self.source == "path":
            out += f" from computed match, partition path: {self.path}"
        elif self.source == "existing":
            out += f" from a student-provided matching"
        return out

    def __repr__(self):
        return self.__str__()
