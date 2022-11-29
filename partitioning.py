from models import *


def run_multi_partitioning(
    config: Configuration, nodes: list, debug: bool = False
) -> list:
    col_set = [(x, dict()) for x in config.constraints["Partition"]]
    for node in nodes:
        for col, seen in col_set:
            prop_values = node.props[0][col]
            if isinstance(prop_values, list):
                for val in prop_values:
                    seen[val] = True
            else:
                seen[prop_values] = True
    col_set = [(col, list(seen.keys())) for col, seen in col_set]
    provisional = []
    dfs(config, nodes, col_set, provisional)
    tentative = uniquify_assignments(config, provisional)
    finalized = bottom_up_merge(config, tentative)
    return finalized


def list_elements_equal(a: list, b: list) -> bool:
    return len(a) == len(b) and all(a[i] == b[i] for i in range(len(a)))


# Phase 1 of multi-partitioning: forming provisional groups using partition criteria.
def dfs(
    config: Configuration,
    nodes: list,
    col_set: list,
    output: list,
    path: tuple = (),
    level: int = 0,
    debug: bool = False,
):
    # Compute the current group size
    current_group_size = sum(x.size for x in nodes)

    # Base case: stop recursing if we have reached the bottom of the partition tree or if our
    # current group size is smaller than the minimum partition size (e.g. 4 students)
    if level >= len(col_set) or current_group_size < config.min_partition_size:
        output.append((path, level, list(nodes), current_group_size))
        return

    # This helper function curries a value into a nested function, and that
    # nested function checks if a given node either is equal to the curried
    # value or contains the curried value
    def filter_helper(value):
        def check_filtering(node: Node):
            # Exclude this node if it's already been assigned somewhere.
            if node.assigned:
                return False

            # Return true if the current node column contains the curried value
            # or is equal to it
            prop_values = node.props[0][col]
            if isinstance(prop_values, list):
                return value in prop_values
            else:
                return value == prop_values

        return check_filtering

    # Figure out which column we are on and extract the set of all possible values in that column
    col, seen = col_set[level]

    # Loop over all possible values of the current column
    for val in seen:
        # Filter current nodes and isolate elements which either include or contain val
        filtered_vals = list(filter(filter_helper(val), nodes))
        if not filtered_vals:
            continue

        # Set up our output array and new path tuple for recursive DFS call
        children_output = []
        new_path = tuple(list(path) + [(col, val)])

        # Recursively call DFS
        dfs(
            config,
            filtered_vals,
            col_set,
            children_output,
            new_path,
            level + 1,
            debug=debug,
        )

        output.extend(children_output)


# Phase 2 of multi-partitioning: forming tentative group assignments that do not have
# any student assigned to multiple groups (i.e. form a valid, unique assignment).
def uniquify_assignments(
    config: Configuration, groups: list, debug: bool = False
) -> list:
    output = []
    phase_counter = 0
    phase_min_cutoffs = [config.min_group_size, config.min_group_size // 2, 1]
    phase_max_cutoffs = [config.max_group_size, config.max_group_size * 3, float("inf")]
    while True:
        min_so_far = float("inf")
        groups = [group for group in groups if group[2]]
        selected_group = None
        for group in groups:
            for i in range(len(group[2]) - 1, -1, -1):
                node = group[2][i]
                if node.assigned:
                    del group[2][i]

            min_group_size = phase_min_cutoffs[phase_counter]
            max_group_size = phase_max_cutoffs[phase_counter]
            group_count = sum(x.size for x in group[2])
            if (
                group_count < min_so_far
                and min_group_size <= group_count <= max_group_size
            ):
                min_so_far = group_count
                selected_group = group

        if not selected_group:
            if phase_counter == len(phase_min_cutoffs):
                break
            else:
                phase_counter += 1
                continue

        for elem in selected_group[2]:
            elem.assigned = True

        groups.remove(selected_group)
        selected_group = list(selected_group)
        selected_group[3] = sum(node.size for node in selected_group[2])
        selected_group = tuple(selected_group)
        output.append(selected_group)

    return output


# Phase 3 of multi-partitioning: finalizing group compositions to avoid group
# size violations (by merging groups up the partition tree in order of edge-hop
# distance).
def bottom_up_merge(config: Configuration, groups: list, debug: bool = False) -> list:
    # Sort tentative groups in order of shortest path first (i.e. most partitioned)
    merged_groups = []
    groups = sorted(groups, key=lambda x: len(x[0]))

    # Keep merging groups as necessary until none remain.
    while groups:
        # Pick off the group at the end (the one with the longest path).
        at = groups.pop()

        # If group is big enough, no need to merge
        if at[3] > config.min_group_size or at[3] >= config.max_group_size:
            merged_groups.append(at)
            continue

        # Otherwise, find siblings and/or ancestors and/or aunts, uncles, etc. etc. and merge
        # Keep going up a partition tree level (edge-hops) and looking for ancestors until we find
        # enough that we can merge them all and no longer violate the minimum group size
        # criteria.
        at_path = at[0]
        next_at_path = at[0]
        num_ancestors = 0
        if debug:
            print("Looking for ancestors...", end=" ")
        while num_ancestors + at[3] <= config.min_group_size:
            at_path = next_at_path
            ancestors = []
            for group in groups:
                if list_elements_equal(at_path, group[0][: len(at_path)]):
                    ancestors.append(group)
            num_ancestors = sum(group[3] for group in ancestors)
            if debug:
                print(at_path, num_ancestors)
                print(list(x[0] for x in ancestors))
            next_at_path = tuple(list(at_path)[:-1])
            if not next_at_path:
                break
        if debug:
            print(f"found {num_ancestors} ancestors.")

        # If we are small but we found tons of ancestor groups, let's only merge as many as are needed as
        # to form a group of sufficient size instead of just merging all of them.
        ancestors = sorted(ancestors, key=lambda x: x[3])
        num_needed = 0
        while at[3] + sum(
            x[3] for x in ancestors[:num_needed]
        ) <= config.min_group_size and num_needed <= len(ancestors):
            num_needed += 1
        num_ancestors = sum(x[3] for x in ancestors[:num_needed])
        if debug:
            print(f"Only need {num_ancestors} ancestors to merge")

        # Remove the merged groups' separate entries
        ancestors = ancestors[:num_needed]
        for ancestor in ancestors:
            groups.remove(ancestor)

        # Create a big merged group and add it to the output list
        merged_group = (
            at_path,
            len(at_path) - 1,
            sum((x[2] for x in ancestors), []) + at[2],
            num_ancestors + at[3],
        )
        merged_groups.append(merged_group)

    # Return final list of merged groups
    return merged_groups
