import os
import argparse
import config_parser
import form_parser
import partitioning
import existing_groups
import best_effort
import time
import pandas as pd


def run():
    # Handle command-line argument parsing
    start_time = time.time()
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument(
        "config_file",
        help="Path to the matching configuration file (is a Python file).",
    )
    arg_parser.add_argument(
        "csv_file",
        help="Path to the CSV file of people to match (e.g. Google form responses).",
    )
    arg_parser.add_argument(
        "--debug", help="Turn on debug logging.", action="store_true"
    )
    parsed_args = arg_parser.parse_args()
    debug = parsed_args.debug

    # Dynamically import and verify configuration file
    print("~~Parsing~~")
    print("Parsing configuration file...", end=" ")
    config = config_parser.import_config(parsed_args.config_file)
    print("done.")

    # Parse CSV using provided configuration
    print(
        "Parsing CSV rows and columns into model objects based on configuration file...",
        end=" ",
    )
    parsed = form_parser.parse_from_csv(
        parsed_args.csv_file, config.row_config, debug=debug
    )
    num_original = len(parsed)
    print(f"{num_original} rows parsed.")

    # Handle existing group matching, if present in configuration file.
    print("\n~~Matching~~")
    matched = []
    if "Existing" in config.constraints:
        if debug:
            print(f"Size before removing existing: {sum(x.size for x in parsed)}")
        print("Handling students requesting explicit groupings...", end=" ")
        existing = existing_groups.handle_existing(config, parsed, debug=debug)
        matched.extend(existing)
        print(
            f"formed {len(existing)} student-requested groups of {sum(x.node.size for x in existing)} students."
        )
        if debug:
            print(f"Size after removing existing: {sum(x.size for x in parsed)}")

    # Run multi-partitioning on parsed nodes
    print(
        "Executing multi-partitioning (DFS-based multi-splitting, winnowing, and bottom-up merging)...",
        end=" ",
    )
    subgroups = partitioning.run_multi_partitioning(config, parsed, debug=debug)
    num_subgroups = len(subgroups)
    print(
        f"partitioned {sum(sum(x.size for x in subgroup[2]) for subgroup in subgroups)} students into {num_subgroups} subgroups."
    )

    # Run custom post-processing function on partitions if requested in the configuration
    if config.postprocess_partitions:
        print(
            "Running partitioning post-processing code...",
            end=" ",
        )
        subgroups = config.postprocess_partitions(subgroups)
        print(f"transformed {num_subgroups} subgroups into {len(subgroups)} subgroups.")

    # Display debugging information and check for malformed subgroups if debug enabled
    if debug:
        subgroupsizes = [
            (elem[3], elem[0], elem[1], i) for (i, elem) in enumerate(subgroups)
        ]
        subgroupsizes = sorted(subgroupsizes, key=lambda x: x[0])
        print("*** Size debugging info ***\n")
        print([x[0] for x in subgroupsizes])
        print("\n".join(repr(x) for x in subgroupsizes))
        print(sum(x[0] for x in subgroupsizes))

    # Run best-effort matching on partitioned nodes
    print(f"Executing best-effort matching on each subgroup...", end=" ")
    mcts_matched = best_effort.run_best_effort(config, subgroups)
    matched.extend(mcts_matched)
    print(f"formed {len(mcts_matched)} groups from {num_subgroups} subgroups.")

    # Display all matches if debug information turned on.
    if debug:
        print("\n\n~~~~Final matches~~~~\n")
        for i, match in enumerate(matched):
            print(f"{i}: {match}")

    # Communicate matching status.
    print("\n~~Results~~")
    num_accounted_for = sum(x.size for x in matched)
    print(
        f"{num_accounted_for} of {num_original} students matched into {len(matched)} groups and"
        + f" accounted for in {round(1000 * (time.time() - start_time))} ms."
    )

    # Sanity checks.
    assert (
        num_accounted_for <= num_original
    ), f"Something went very wrong and we gained {num_accounted_for - num_original} student(s) somewhere!"
    assert (
        num_accounted_for >= num_original
    ), f"Something went very wrong and we lost {num_original - num_accounted_for} student(s) somewhere!"

    # Do any config-specific post-processing on matches.
    if config.post_processing:
        print("Running post-processing...", end=" ")
        config.post_processing(matched)
        print("done.")
    else:
        # If no post-processing specified, output matches to CSV of the form out-private-IDX.csv
        # where IDX chosen to be a unique filename
        df = pd.DataFrame(
            sum([match.to_json(group_num=i) for i, match in enumerate(matched)], [])
        )
        out_fname = "out-private.csv"
        out_fname_format = "out-private-{}.csv"
        if os.path.isfile(out_fname):
            i = 2
            while os.path.isfile(out_fname_format.format(i)):
                i += 1
            out_fname = out_fname_format.format(i)
        print(f"Outputting {num_accounted_for} students to '{out_fname}'.")
        df.to_csv(out_fname, encoding="utf-8", index=False)


if __name__ == "__main__":
    run()
