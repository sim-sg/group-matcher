from models import Row, Column, Node, Match
import os


def days_transformer(days_list):
    days_list = days_list[0].strip("[']")
    if "Saturday" in days_list:
        return 1
    elif "Sunday" in days_list:
        return 2
    elif "Tuesday" in days_list:
        return 3
    elif "Friday" in days_list:
        return 4
    elif "Monday" in days_list:
        return 5
    elif "Thursday" in days_list:
        return 6
    else:
        return 7


def time_transformer(times_list):
    times_list = times_list[0].strip("[']")
    if "Morning" in times_list:
        return 1
    elif "Afternoon" in times_list:
        return 2
    elif "Night" in times_list:
        return 3
    else:
        return 4


def year_transformer(year):
    year = year.lower()
    if "transfer" in year:
        return 3
    elif "junior" in year or "senior" in year:
        return 2
    elif "sophomore" in year:
        return 1
    else:
        return 1


def gender_transformer(gender):
    if len(gender) == 1:
        gender = gender[0]
        if gender == "Female":
            return 0
        elif gender == "Male":
            return 1
    return 2


def race_transformer(race):
    if len(race) == 1:
        race = race[0]
        if race == "White":
            return 0
        elif "Asian" in race:
            return 1
        elif race == "Hispanic":
            return 2
        elif race == "Black/African American":
            return 3
        elif "Alaska" in race:
            return 4
        elif "Islander" in race:
            return 5
        elif "Middle-Eastern" in race:
            return 6
        elif race == "Multiple races":
            return 7
        elif race == "Prefer not to answer" or True:
            return 8
    else:
        return 7


def timezone_transformer_delta(tz, delta=2):
    # Returns a list of all timezones that this person can attend for multi-partitioning purposes
    # -11 to +14
    # -22 to +28 for x2
    tz *= 2
    tz = min(max(round(tz), -22), 28)
    all_possible = list(range(tz - (delta * 2), tz + (delta * 2 + 1)))
    all_possible = [x for x in all_possible if -22 <= x <= 28]
    return all_possible


def timezone_bucketer(tz):
    # print(tz)
    if "-7" in tz:
        return 1
    elif "-5" in tz or "-4" in tz:
        return 2
    elif "+1" in tz:
        return 3
    elif "+5.5" in tz or "+8" in tz or "+9" in tz:
        return 4
    else:
        return 5


def email_transformer(email):
    return email.lower().strip()


# ## cancelled discussions; 12-1 and 5-6
# def discussion_transformer(disc_list):
#     times_list = []
#     if "10-11 M/W" in disc_list:
#         times_list.append(10)
#     if "11-12 M/W" in disc_list:
#         times_list.append(11)
#     if "1-2 M/W" in disc_list:
#         times_list.append(1)
#     if "2-3 M/W" in disc_list:
#         times_list.append(2)
#     if "3-4 M/W" in disc_list:
#         times_list.append(3)
#     if "4-5 M/W" in disc_list:
#         times_list.append(4)
#     return times_list


ROW_CONFIG = Row(
    [
        Column(
            "Email Address",
            "email",
            "email",
            is_optional=False,
            transformer=email_transformer,
        ),
        Column("SID", "sid", "sid", is_optional=False),
        Column("First name", "first_name", "text"),
        Column("Last name", "last_name", "text"),
        Column(
            "What year are you",
            "year",
            "radio",
            is_optional=True,
            transformer=year_transformer,
        ),
        Column(
            "Would you like to be part of a course study group?",
            "want_group",
            "text",
            transformer=lambda x: x == "Yes",
            is_optional=False,
        ),
        Column(
            "Do you have an existing study group of size 2-6 in mind",
            "is_existing",
            "text",
            transformer=lambda x: x == "Yes",
            is_optional=False,
        ),
        Column(
            "timezone offset",
            "timezone",
            "text",
            transformer=timezone_bucketer,
            is_optional=True,
        ),
        Column(
            "times of the day",
            "meeting_time",
            "checkbox",
            # transformer=time_transformer,
            is_optional=True,
        ),
        Column(
            "days of the week",
            "meeting_days",
            "checkbox",
            # transformer=days_transformer,
            is_optional=True,
        ),
        Column(
            "Would you like to attend the same discussion",
            "disc_with_group",
            "text",
            transformer=lambda x: "yes, i would like to" in x.lower(),
            is_optional=True,
        ),
        Column(
            "discussion section times",
            "disc_times_options",
            "checkbox",
            is_optional=True,
            # transformer=discussion_transformer,
        ),
        Column(
            "2nd Group Member Berkeley Student Email",
            "groupmember2",
            "email",
            is_optional=True,
            transformer=email_transformer,
        ),
        Column(
            "3rd Group Member Berkeley Student Email",
            "groupmember3",
            "email",
            is_optional=True,
            transformer=email_transformer,
        ),
        Column(
            "4th Group Member Berkeley Student Email",
            "groupmember4",
            "email",
            is_optional=True,
            transformer=email_transformer,
        ),
        Column(
            "5th Group Member Berkeley Student Email",
            "groupmember5",
            "email",
            is_optional=True,
            transformer=email_transformer,
        ),
        Column(
            "6th Group Member Berkeley Student Email",
            "groupmember6",
            "email",
            is_optional=True,
            transformer=email_transformer,
        ),
        Column(
            "Will you be on the Berkeley campus",
            "remote",
            "radio",
            is_optional=True,
            transformer=lambda x: "Yes" in x,
        ),
        Column(
            "discussion section times",
            "sections",
            "checkbox",
            is_optional=True,
            transformer=lambda x: "Yes" in x,
        ),
        Column(
            "Which of these options best describes your race?",
            "race",
            "checkbox",
            is_optional=True,
            transformer=race_transformer,
        ),
        Column(
            "How do you self-identify?",
            "gender",
            "checkbox",
            is_optional=True,
            transformer=gender_transformer,
        ),
    ]
)

CONSTRAINTS = {
    "Partition": ["year", "remote", "meeting_days", "meeting_time"],
    "Existing": {
        "type": "explicit_keys",
        "flag": "is_existing",
        "id_key": "email",
        "data": [
            "groupmember2",
            "groupmember3",
            "groupmember4",
            "groupmember5",
            "groupmember6",
        ],
    },
    # "Best-effort": [],
    "Best-effort": [
        ["gender", "race"],
        [1, 1],
    ],  # column ID's for features followed by weights
}

MIN_GROUP_SIZE = 3
MAX_GROUP_SIZE = 6
MIN_PARTITION_SIZE = 3


def pregroup_nodes(nodes: list) -> list:
    # Only match students who want a group
    filtered = [node for node in nodes if node.props[0]["want_group"]]
    by_email = {}
    for node in filtered:
        by_email[node.props[0]["email"]] = node
    filtered = list(by_email.values())
    # return filtered

    # Now pre-pair students who want to be pre-paired
    # indices_to_remove = []
    # paired = []
    # for (i, node) in enumerate(filtered):
    #     partner = by_email.get(node.props[0]["pregroup_partner"], None)
    #     if partner and i not in indices_to_remove:
    #         found = filtered.index(partner)
    #         assert found is not None and found != i
    #         indices_to_remove.append(i)
    #         indices_to_remove.append(found)
    #         print(
    #             i,
    #             found,
    #             node.props[0]["pregroup_partner"],
    #             partner.props[0]["email"],
    #         )
    #         paired.append(node + partner)
    # print(
    #     "People who entered a partner who did not fill out the form:",
    #     [
    #         (i, n.props[0]["pregroup_partner"])
    #         for i, n in enumerate(filtered)
    #         if i not in indices_to_remove and n.props[0]["pregroup_partner"]
    #     ],
    # )
    # for i, n in enumerate(filtered):
    #     if i not in indices_to_remove and n.props[0]["pregroup_partner"]:
    #         n.props[0][
    #             "pregroup_partner"
    #         ] += " (this person did not fill out the form or incorrect email!)"
    # filtered = [filtered[i] for i in range(len(filtered)) if i not in indices_to_remove]
    # filtered += paired
    return filtered


def batch(arr, n=2):
    ret = []
    if not len(arr) // n:
        return [arr]
    for i in range(len(arr) // n):
        at = arr[i * n : i * n + n]
        if i + 1 >= len(arr) // n:
            at = arr[i * n :]
        ret.append(at)
    return ret


def group_races(arr, n=2):
    by_race = {}
    for node in arr:
        currnode_race = node["race"]
        by_race[currnode_race] = by_race.get(currnode_race, []) + [node]
    for race in list(by_race.keys()):
        members = by_race[race]
        if len(members) > 1:
            yield from batch(members, n=n)
            del by_race[race]
    yield from batch(sum(by_race.values(), []), n=n)


def group_genders(arr, n=2):
    by_gender = {}
    for node in arr:
        by_gender[node["gender"]] = by_gender.get(node["gender"], []) + [node]
    yield from group_races(by_gender.get(1, []), n=n)
    if 1 in by_gender:
        del by_gender[1]
    yield from group_races(sum(list(by_gender.values()), []), n=n)


def postprocess_partitions(subgroups: list) -> list:
    # Black
    # Pacific Islander / Alaskan
    # Cis Female
    # Hispanic
    # All non-male/female genders
    # Race: 2-6 are underrepresented
    # Gender: not male == underrepresented

    for (group_num, group) in enumerate(subgroups):
        new_nodes = []
        for at in group_genders(sum((node.props for node in group[2]), [])):
            merged = Node(at, size=len(at), assigned=True)
            new_nodes.append(merged)
        subgroups[group_num] = (group[0], group[1], new_nodes, group[3])

    return subgroups


def is_black(props):
    return props["race"] is not None and props["race"] == 3


def is_hispanic(props):
    return props["race"] is not None and props["race"] == 2


def is_islander(props):
    return props["race"] is not None and props["race"] == 5


def is_alaskan(props):
    return props["race"] is not None and props["race"] == 4


def is_female(props):
    return props["gender"] is not None and props["gender"] == 0


def is_nonmf(props):
    return props["gender"] is not None and props["gender"] not in (0, 1)


def is_underrepresented(props):
    return (
        props["race"] is not None
        and 2 <= props["race"] <= 6
        or (props["gender"] is not None and props["gender"] != 1)
    )


def post_processing(matches: list):
    from collections import Counter
    import pandas as pd

    # TODO: fix that it's hardcoded for now, should generalize by partition criteria and type.
    def reconstruct_path(match: Match):
        if "modification" in str(match.path):
            match.path = []
            if len(set([x["year"] for x in match.node.props])) == 1:
                match.path.append(["year", match.node.props[0]["year"]])
            if len(set([x["remote"] for x in match.node.props])) == 1:
                match.path.append(["remote", match.node.props[0]["remote"]])
                day_flag = 0
                for day in [
                    "Monday",
                    "Tueday",
                    "Wednesday",
                    "Thursday",
                    "Friday",
                    "Saturday",
                    "Sunday",
                ]:
                    if (
                        all(
                            [
                                (x["meeting_days"] and day in x["meeting_days"])
                                for x in match.node.props
                            ]
                        )
                        and not day_flag
                    ):
                        day_flag = 1
                        match.path.append(["meeting_days", day])
                        time_flag = 0
                        for time in ["Morning", "Afternoon", "Evening", "Night"]:
                            if (
                                all(
                                    [
                                        (
                                            x["meeting_time"]
                                            and time in x["meeting_time"]
                                        )
                                        for x in match.node.props
                                    ]
                                )
                                and not time_flag
                            ):
                                time_flag = 1
                                match.path.append(["meeting_time", time])

    def describe_group(match: Match):
        race_map = {
            0: "White",
            1: "Asian",
            2: "Hispanic",
            3: "Black",
            4: "Alaska",
            5: "Islander",
            6: "Middle-Eastern",
            7: "Multiple Races",
            8: "DTS",
            None: "DTS",
        }

        gender_map = {0: "Female", 1: "Male", 2: "Non-M/F", 3: "DTS", None: "DTS"}

        return (
            ", ".join(
                [
                    (race_map[x.get("race", 8)] + " " + gender_map[x.get("gender", 3)])
                    for x in match.node.props
                ]
            )
            + " ("
            + (
                ", ".join(f"{x[0]}: {x[1]}" for x in match.path)
                if isinstance(match.path, tuple)
                else match.path
            )
            + ")"
        )

    by_size = {}
    for match in matches:
        if match.source == "existing":
            continue
        by_size[match.size] = by_size.get(match.size, []) + [match]
    matches = [match for match in matches if match not in by_size[2]]
    for arr in batch(by_size[2], n=2):
        props = sum((x.node.props for x in arr), [])
        node = Node(props, size=(len(arr) * 2), assigned=True)
        matches.append(Match(node=node, source="path", path="(manually fixed)"))

    # handle students who asked for existing groups, but for some reason (didn't communicate, etc.) ended up as a solo (and now, we have no non-demo preferences to go off of)
    existing_singletons = []
    for match in matches:
        if match.source != "existing":
            continue
        if match.size == 1:
            existing_singletons.append(match)
    print(f"Singleton count: {len(existing_singletons)}")
    matches = [match for match in matches if match not in existing_singletons]
    for props in group_genders(
        [match.node.props[0] for match in existing_singletons], n=3
    ):
        # props = sum((x.node.props for x in arr), [])
        # print(len(props))
        node_size = len(props)
        if node_size == 1:
            print(props[0])
        node = Node(props, size=node_size, assigned=True)
        matches.append(
            Match(
                node=node,
                source="path",
                path="(singleton manually fixed)",
            )
        )

    # For female students; find groups with only 1 female. Take females from half of them, and add to the other half (pair up).
    # TODO: implement odd-number workaround
    female_groups = []
    for match in matches:
        if match.source == "existing" or match.path == "(singleton manually fixed)":
            continue
        num_female_students = 0
        for x in match.node.props:
            if is_female(x):
                num_female_students = num_female_students + 1
        if num_female_students == 1:
            female_groups.append(match)
    female_groups = sorted(female_groups, key=lambda x: x.size, reverse=True)
    if len(female_groups) % 2 == 1:
        print(f"{len(female_groups)}, CANNOT pair all females")
    for i in range(len(female_groups) // 2):
        member = [x for x in female_groups[i].node.props if is_female(x)][0]
        # if is_female(member):
        #     continue
        female_groups[i].node.size -= 1
        female_groups[i].node.props.remove(member)
        female_groups[i].path = "(gender modification singletons - 1)"
        j = i + len(female_groups) // 2
        female_groups[j].node.size += 1
        female_groups[j].node.props.append(member)
        female_groups[j].path = "(gender modification singletons + 1)"

    # Pair up hispanic students
    hispanic_groups = []
    for match in matches:
        if match.source == "existing" or match.path == "(singleton manually fixed)":
            continue
        num_hispanic_students = 0
        for x in match.node.props:
            if is_hispanic(x):
                num_hispanic_students = num_hispanic_students + 1
        if num_hispanic_students == 1:
            hispanic_groups.append(match)
    hispanic_groups = sorted(hispanic_groups, key=lambda x: x.size, reverse=True)
    for i in range(len(hispanic_groups) // 2):
        member = [x for x in hispanic_groups[i].node.props if is_hispanic(x)][0]
        # if is_female(member):
        #     continue
        hispanic_groups[i].node.size -= 1
        hispanic_groups[i].node.props.remove(member)
        hispanic_groups[i].path = "(hispanic modification singletons - 1)"
        j = i + len(hispanic_groups) // 2
        hispanic_groups[j].node.size += 1
        hispanic_groups[j].node.props.append(member)
        hispanic_groups[j].path = "(hispanic modification singletons + 1)"

    # Pair up black students
    black_groups = []
    for match in matches:
        if match.source == "existing" or match.path == "(singleton manually fixed)":
            continue
        num_black_students = 0
        for x in match.node.props:
            if is_black(x):
                num_black_students = num_black_students + 1
        if num_black_students == 1:
            black_groups.append(match)
    black_groups = sorted(black_groups, key=lambda x: x.size, reverse=True)
    print("BLACK: ", black_groups)
    for i in range(len(black_groups) // 2):
        member = [x for x in black_groups[i].node.props if is_black(x)][0]
        # if is_female(member):
        #     continue
        black_groups[i].node.size -= 1
        black_groups[i].node.props.remove(member)
        black_groups[i].path = "(black modification singletons - 1)"
        j = i + len(black_groups) // 2
        black_groups[j].node.size += 1
        black_groups[j].node.props.append(member)
        black_groups[j].path = "(black modification singletons + 1)"

    total_num = 0
    minority_groups = [
        ("Black", is_black),
        ("Hispanic", is_hispanic),
        ("Islander", is_islander),
        ("Alaskan", is_alaskan),
        ("female", is_female),
        ("non-mf", is_nonmf),
        ("underrepresented", is_underrepresented),
    ]
    for (minority_group, minority_fn) in minority_groups:
        fractions, lengths = {}, {}
        for match in matches:
            if match.source == "existing":
                continue
            num_minority = sum(1 for x in match.node.props if minority_fn(x))
            group_desc = describe_group(match)
            if num_minority > 0:
                fractions[num_minority] = fractions.get(num_minority, []) + [group_desc]
                lengths[num_minority] = lengths.get(num_minority, 0) + match.size

        counter = fractions
        if not counter:
            print(f"No {minority_group} members found, skipping.")
            continue

        print("")
        print(
            f"For all {len(sum(counter.values(), []))} groups ({sum(lengths.values())} students) with {minority_group} member(s):"
        )
        for k in sorted(counter.keys()):
            print(
                f"\t{len(counter[k]) / len(sum(counter.values(), [])):.1%} ({len(counter[k])} groups) representing {lengths[k] / sum(lengths.values()):.1%} of {minority_group} students had {k} {minority_group} member(s):"
            )
            print("******")
            print("\n".join(counter[k]))
            print("******")

    out = []
    for match in matches:
        added = [x["partner"] for x in match.node.props if "partner" in x]
        match.node.props += added
    match_depths = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for match in matches:
        reconstruct_path(match)
    for (i, match) in enumerate(matches):
        if (
            match.path
            and str(match.path) != "(manually fixed)"
            and str(match.path) != "(singleton manually fixed)"
            and "modification" not in str(match.path)
        ):
            print(match.path)
            curr_path = match.path
            if type(curr_path) == tuple:
                match_depths[len(match.path)] = match_depths[len(match.path)] + 1
            if len(match.path) == 5:
                common_remoteness = match.path[1][1]
                common_meeting_day = match.path[2][1]
                common_meeting_time = match.path[3][1]
                common_section = match.path[4][1]
            elif len(match.path) == 4:
                common_remoteness = match.path[1][1]
                common_meeting_day = match.path[2][1]
                common_meeting_time = match.path[3][1]
                common_section = " "
            elif len(match.path) == 3:
                common_remoteness = match.path[1][1]
                common_meeting_day = match.path[2][1]
                common_meeting_time = " "
                common_section = " "
            elif len(match.path) == 2:
                common_remoteness = match.path[1][1]
                common_meeting_day = " "
                common_meeting_time = " "
                common_section = " "
        else:
            common_remoteness = " "
            common_meeting_day = " "
            common_meeting_time = " "
            common_section = " "
            curr_path = str(match.path)
        for person in match.node.props:
            out.append(
                {
                    "group_num": i,
                    "email": person["email"],
                    "sid": person["sid"],
                    "first": person["first_name"],
                    "last": person["last_name"],
                    "incoming_partners": person.get("incoming_partners", "N/A"),
                    "outgoing_partners": person.get("outgoing_partners", "N/A"),
                    "race": person["race"],
                    "gender": person["gender"],
                    "had existing": person["is_existing"],
                    "meeting days": person["meeting_days"],
                    "meeting times": person["meeting_time"],
                    "common_remoteness": common_remoteness,
                    "common_meeting_day": common_meeting_day,
                    "common_meeting_time": common_meeting_time,
                    "common_section": common_section,
                    "path": curr_path,
                }
            )

    print("*** Match Stats ***")
    print(match_depths)
    print("***")
    df = pd.DataFrame(out)
    out_fname = "out-private.csv"
    out_fname_format = "out-private-{}.csv"
    if os.path.isfile(out_fname):
        i = 2
        while os.path.isfile(out_fname_format.format(i)):
            i += 1
        out_fname = out_fname_format.format(i)
    print(f"Outputting {len(out)} students to '{out_fname}'.")
    df.to_csv(out_fname, encoding="utf-8", index=False)
