from models import *
import random

random.seed(100)

"""
This function is responsible for splitting up subgroups that have *already* been formed
via multi-partitioning. Uses what is effectively Monte Carlo Tree Search (MCTS) to split
up nodes of variable size (effectively, approximates a solution to the problem of: given
variable coin weights and amounts, split into amounts with value constrained by some
range -- in this case, the range being [config.min_group_size, config.max_group_size].
"""


def run_best_effort(config: Configuration, subgroups: list) -> list:
    hi, lo = config.max_group_size, config.min_group_size

    def sample_subgroup_split(nodes, path=[]):
        # Base case: no nodes left to pick, return our current path.
        if not nodes:
            return path

        # Compute how many nodes we have left to pick from and
        # return failure if we don't have enough.
        num_left = sum(x.size for x in nodes)
        if num_left < lo:
            if num_left and num_left == lo - 1:
                return path + [nodes]
            return None

        # If we have exactly enough, we're trivially done.
        if lo <= num_left <= hi:
            return path + [nodes]

        # Sampling-based DFS (effectively MTCS / Monte Carlo Tree Search)
        # to solve general, iterated change-making problem.
        # Basically, each subgroup node can have variable size, and yet we need
        # to group nodes together to achieve sizes tightly bounded by min
        # and max group sizes specified in the class config.
        num_samples = 0
        sample = nodes
        while num_samples <= 1000:
            num_samples += 1
            random.shuffle(sample)

            # Pick first i nodes until total size of first i is within desired range bound.
            cur_path = list(path)
            cur_sample = sample
            while cur_sample:
                i = 1
                while i <= len(cur_sample):
                    # Compute sum of first i nodes' sizes and stop looping
                    # if we have achieved our desired size.
                    at = sum(x.size for x in cur_sample[:i])
                    if lo <= at <= hi:
                        if (i + 1 <= len(cur_sample)) and (
                            at + sum(x.size for x in cur_sample[i : i + 1]) <= hi
                        ):
                            if random.choice((False, True)):
                                break
                        else:
                            break

                    # Check if we were not able to achieve the desired change
                    # and flag for re-sampling.
                    if at > hi:
                        i = -1
                        break

                    # Otherwise, continue looping.
                    i += 1
                    if i > len(cur_sample):
                        i -= 1
                        break

                # If sample did not succeed, re-loop.
                if i < 0 or at < lo:
                    cur_path = None
                    break

                cur_path.append(list(cur_sample[:i]))
                cur_sample = cur_sample[i:]

            if cur_path:
                return cur_path

        # If no valid split found in this recursion branch, signal failure.
        return None

    # For each subgroup, use sampling-based approach to compute split.
    out = []
    for subgroup in subgroups:
        split = [subgroup[2]]

        # Only use recursive method if we have enough nodes to even achieve a valid result.
        if subgroup[3] >= lo:
            split = sample_subgroup_split(subgroup[2], [])
            if not split:
                # Explain how to recover from this error state.
                print(
                    "Sampling-based subgroup splitting was unable to achieve a size result within bounds."
                )
                print(
                    "Try either (1) running again and changing the seed, (2) increasing the number of iterations,"
                    + " or (3) loosening the group range."
                )

                # Halt execution of program.
                raise RuntimeError(
                    f"Unable to compute subgroup split of size {subgroup[3]}"
                    + f" comprised of {len(subgroup[2])} nodes with num {sum(x.size for x in subgroup[2])} to achieve range"
                    + f" [{config.min_group_size}, {config.max_group_size}] inclusive."
                )

        # Combine the grouped subgroup nodes into Match objects, one per grouped subgroup.
        for group in split:
            group_num = sum(x.size for x in group)
            combined = Node(
                sum((x.props for x in group), []), size=group_num, assigned=True
            )
            out.append(Match(combined, source="path", path=subgroup[0]))

    # Return final matches.
    return out
