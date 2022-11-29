from models import *


def handle_existing(config: Configuration, nodes: list, debug: bool = False) -> list:
    # Grab relevant configuration parameters.
    assert config.constraints["Existing"]["type"] in (
        "min_sid",
        "explicit_keys",
    ), "Only minimum / unique group SID and explicit group member keys implemented for group matching!"
    flag_key = config.constraints["Existing"]["flag"]
    groups = {}

    if config.constraints["Existing"]["type"] == "min_sid":
        data_key = config.constraints["Existing"]["data"][0]

        # Go through each parsed node, group any which match the flag key into
        # their groups based on min/unique SID, and take them out of the
        # main matching pool.
        for i in range(len(nodes) - 1, -1, -1):
            curr_node = nodes[i].props[0]
            if curr_node[flag_key] and nodes[i].size == 1:
                groups.setdefault(curr_node[data_key], [])
                groups[curr_node[data_key]].append(curr_node)
                del nodes[i]
    elif config.constraints["Existing"]["type"] == "explicit_keys":
        data_keys = config.constraints["Existing"]["data"]
        id_key = config.constraints["Existing"]["id_key"]
        predecessor_map = {}  # predecessor map
        successor_map = {}
        key_to_node = {}

        # Go through each parsed node, group any which match the flag key into
        # their groups based on min/unique SID, and take them out of the
        # main matching pool.
        num_deleted = 0
        for i in range(len(nodes) - 1, -1, -1):
            curr_node = nodes[i].props[0]
            if curr_node[flag_key] and nodes[i].size == 1:
                assert curr_node[id_key] not in key_to_node
                key_to_node[curr_node[id_key]] = nodes[i]
                successor_map[curr_node[id_key]] = [
                    curr_node[key] for key in data_keys if curr_node[key]
                ]
                group_keys = sorted(
                    successor_map[curr_node[id_key]] + [curr_node[id_key]]
                )
                for group_key in group_keys:
                    predecessor_map.setdefault(group_key, [])
                    predecessor_map[group_key].append(curr_node[id_key])
                del nodes[i]
                num_deleted += 1
        # print(f"{num_deleted} students removed.")

        # Another pass to merge groups since lots of them forget to list all other
        # partners and only list a few
        seen_ids = set()
        for group_key in predecessor_map:
            if group_key in seen_ids or group_key not in key_to_node:
                continue
            have = []
            q = predecessor_map[group_key] + [group_key]
            if debug:
                print("\nstarting", group_key)
            while q:
                at = q.pop()
                if at in seen_ids or at not in key_to_node:
                    if debug:
                        print("bye", at, at in seen_ids, at not in key_to_node)
                        print(key_to_node)
                    continue
                if debug:
                    print(at)
                seen_ids.add(at)
                have.append(at)
                q.extend([k for k in predecessor_map[at] if k not in seen_ids])
                q.extend([k for k in successor_map[at] if k not in seen_ids])
            if debug:
                print(group_key, len(have))
            groups[group_key] = [key_to_node[k].props[0] for k in have]

        # One last pass: annotate everybody with their incoming edges (people who put them as partners)
        for key in key_to_node:
            key_to_node[key].props[0]["incoming_partners"] = predecessor_map[key]
            for (i, person) in enumerate(successor_map[key]):
                if person not in key_to_node:
                    successor_map[key][
                        i
                    ] += " (this person did not fill out the form, indicated they wanted no study group, indicated they wanted a study group but did not have an existing one, or this is an incorrect email (check for typos)!)"
            key_to_node[key].props[0]["outgoing_partners"] = successor_map[key]

    # Print debugging info if requested.
    if debug:
        print([(i, len(x)) for i, x in sorted(groups.items(), key=lambda x: x[0])])
        print(len(groups))

    # Combine groups into singular Nodes and form explicit Match objects.
    out = []
    for group in groups.values():
        combined = Node(group, size=len(group), assigned=True)
        out.append(Match(combined, source="existing"))

    # Reap the rewards.
    return out
