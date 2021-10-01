"""
Generate a bar plot for a particular benchmark.

Examples:
- Compare the "calculator-fns" benchmark in git ref "quickpatterntest" to the master git branch:
  python ./mathics_benchmark/compare.py calculator-fns quickpatterntest

"calculator-fns" is a YAML file in the be "benchmarks" directory.
The example above will be called the "base example" in the examples below.

- Compare the "calculator-fns" benchmark in quickpatterntest in master in verbose mode:
  python ./mathics_benchmark/compare.py -v calculator-fns quickpatterntest

- Compare the calculator-fns benchmark in quickpatterntest versus the improve-rational-performance git reference:
  python ./mathics_benchmark/compare.py calculator-fns quickpatterntest improve-rational-performance

- Run the base example above, but only compare the group Power:
  python ./mathics_benchmark/compare.py calculator-fns quickpatterntest -g Power

- Run the base example above without showing the percentage difference:
  python ./mathics_benchmark/compare.py calculator-fns quickpatterntest -c

The 3 options bellow are only useful when the benchmarks' results doesn't exist or you are using --force
- Run the benchmarks with verbose output:
  python ./mathics_benchmark/compare.py calculator-fns quickpatterntest -v
- Git pull before running the example benchmark:
  python ./mathics_benchmark/compare.py calculator-fns quickpatterntest -p
- Override the number of iterations:
  python ./mathics_benchmark/compare.py calculator-fns quickpatterntest -i 10

- Run all benchmarks against the SHA1 indicated in verbose mode:
  python ./mathics_benchmark/compare.py -v run-all b2e237c0aafd6fad08defc029332b5e328857a81

If environment variable NO_CYTHON is set we skip running Cython in setting up mathics-core.
"""

import numpy as np
import matplotlib.pyplot as plt
import json
import click
import sys
import re
import os

import os.path as osp

from mathics_benchmark import bench
from typing import Optional


def break_string(string: str, number: int) -> str:
    return "\n".join(re.findall(".{1,%i}" % number, string))


@click.command()
@click.option(
    "-v",
    "--verbose",
    count=True,
    help="verbosity level in tracing.\n"
    "Can be supplied multiple times to increase verbosity.",
)
@click.option(
    "-g",
    "--group",
    help="If passed generate the plot only for the queries in that group. Overrides compare-groups if that is present in the YAML file",
)
@click.option(
    "-c",
    "--clean",
    help="Don't show the difference percentage",
    is_flag=True,
)
@click.option(
    "-p",
    "--pull",
    help="Update the mathics-core repository",
    is_flag=True,
)
@click.option(
    "-f",
    "--force",
    help="Run the benchmarks even if they already exist",
    is_flag=True,
)
@click.option(
    "-s",
    "--single",
    help="Show the benchmarks only for ref1",
    is_flag=True,
)
@click.option(
    "-l",
    "--logarithmic",
    help="Use logarithmic scale for times",
    is_flag=True,
)
@click.option(
    "--cython/--no-cython",
    help="Run Cython on setup. The default is don't run it.",
    default=False,
)
@click.option(
    "-i",
    "--iterations",
    help="Override the number of iterations",
)
@click.argument("input", nargs=1, type=click.Path(readable=True), required=True)
@click.argument("ref1", nargs=1, type=click.Path(readable=True), required=True)
@click.argument("ref2", nargs=1, type=click.Path(readable=True), default="master")
def main(
    verbose: int,
    group: Optional[str],
    clean: bool,
    pull: bool,
    force: bool,
    single: bool,
    logarithmic: bool,
    cython: bool,
    input: str,
    ref1: str,
    ref2: str,
    iterations: Optional[int],
):
    if input == "run-all":
        import glob

        inputs = glob.glob("benchmarks/*.yaml")
        for input in inputs:
            print(f"running {input[11:]}")
            worker(
                verbose,
                group,
                clean,
                pull,
                force,
                single,
                logarithmic,
                cython,
                input[11:],
                ref1,
                ref2,
                iterations,
            )
    else:
        worker(
            verbose,
            group,
            clean,
            pull,
            force,
            single,
            logarithmic,
            cython,
            input,
            ref1,
            ref2,
            iterations,
        )


def worker(
    verbose: int,
    group: Optional[str],
    clean: bool,
    pull: bool,
    force: bool,
    single: bool,
    logarithmic: bool,
    cython: bool,
    input: str,
    ref1: str,
    ref2: str,
    iterations: Optional[int],
):
    # The percentage diference between a and b is: (a - b) / b * 100

    sha_1: str
    sha_2: str

    queries: list[str] = []
    ref1_times: list[float] = []
    ref2_times: list[float] = []

    yaml_file = bench.get_bench_data(input)

    compare_groups = (
        "compare-groups" in yaml_file and yaml_file["compare-groups"] == True
    )

    # The variables bellow are only used if compare_groups is True
    compare_groups_times: list[list[float]] = []
    groups: list[str] = []

    if input[-5:] == ".yaml":
        input = input[:-5]

    path = (
        f"results/{input}.json" if ref1 == "master" else f"results/{ref1}/{input}.json"
    )
    try:
        if ref1 != "master":
            os.mkdir(f"results/{ref1}")
    except:
        pass

    if not osp.isfile(path) or force:
        arguments = [input]

        if ref1 != "master":
            arguments.append(ref1)

        if pull:
            arguments.append("-p")

        if verbose:
            arguments.append("-v")

        if cython:
            arguments.append("--cython")
        if iterations:
            arguments.append("-i")
            arguments.append(iterations)

        try:
            bench.main(arguments)
        except SystemExit:
            print("... done")

    with open(path) as file:
        object = json.load(file)

        sha_1 = object["info"]["Git SHA"]

        if group:
            for query in object["timings"][group]:
                queries.append(break_string(query, 25 if len(queries) <= 10 else 35))

                # The time diveded by the number of interations.
                ref1_times.append(
                    object["timings"][group][query][1]
                    / object["timings"][group][query][0]
                )
        else:
            for index, queries_group in enumerate(object["timings"]):
                if compare_groups:
                    groups.append(queries_group)
                    compare_groups_times.append([])

                for query in object["timings"][queries_group]:
                    queries.append(
                        break_string(query, 25 if len(queries) <= 10 else 35)
                    )

                    # The time diveded by the number of interations.
                    time = (
                        object["timings"][queries_group][query][1]
                        / object["timings"][queries_group][query][0]
                    )

                    if compare_groups:
                        compare_groups_times[index].append(time)
                    else:
                        ref1_times.append(time)

    if not single and not compare_groups:
        path = (
            f"results/{input}.json"
            if ref2 == "master"
            else f"results/{ref2}/{input}.json"
        )

        if not osp.isfile(path) or force:
            arguments = [input]

            if ref2 != "master":
                arguments.append(ref2)

            if pull:
                arguments.append("-p")

            if iterations:
                arguments.append("-i")
                arguments.append(iterations)

            bench.main(arguments)

        with open(path) as file:
            object = json.load(file)

            sha_2 = object["info"]["Git SHA"]

            if group:
                for query in object["timings"][group]:
                    # The time diveded by the number of interations.
                    ref2_times.append(
                        object["timings"][group][query][1]
                        / object["timings"][group][query][0]
                    )
            else:
                for queries_group in object["timings"]:
                    for query in object["timings"][queries_group]:
                        # The time diveded by the number of interations.
                        ref2_times.append(
                            object["timings"][queries_group][query][1]
                            / object["timings"][queries_group][query][0]
                        )

    x = np.arange(
        len(queries) / len(compare_groups_times) if compare_groups else len(queries)
    )  # label locations
    width = (
        0.3 / len(compare_groups_times) if compare_groups else 0.35
    )  # width of the bars

    fig, ax = plt.subplots()
    ax.set_xlabel("seconds")
    ax.set_title(input)
    ax.set_yticks(x)

    if logarithmic:
        ax.set_xscale("log")

    if compare_groups:
        rects = []

        for index, queries_group in enumerate(compare_groups_times):
            rects.append(
                ax.barh(
                    # The width multiplier starts negative.
                    # In matplotlib y=0 is the bottom of the plot.
                    x - (index - len(compare_groups_times) / 2) * width,
                    queries_group,
                    width,
                    label=f"{ref1} - {sha_1} - {groups[index]}",
                )
            )

        ax.set_yticklabels(
            [
                "\n".join(queries[j :: len(queries) // len(compare_groups_times)])
                for j in range(len(queries) // len(compare_groups_times))
            ],
            fontdict={
                "fontsize": "large" if len(queries) <= 10 else 6,
            },
        )

        # Only show the percentage difference if there are 2 groups
        if len(compare_groups_times) == 2:
            ax.bar_label(
                rects[1],
                labels=[
                    # Only shows the percentage of difference if the it is greater than 1% and is positive.
                    ""
                    if 0 <= (a - b) / b <= 0.01 or a - b < 0
                    else f"{(a - b) / b * 100:+.2f}%"
                    for a, b in zip(*compare_groups_times)
                ],
                color="red",
            )

            ax.bar_label(
                rects[0],
                labels=[
                    # Only shows the percentage of difference if the it is greater than 1% and is negative.
                    ""
                    if -0.01 <= (a - b) / b <= 0 or a - b > 0
                    else f"{(a - b) / b * 100:+.2f}%"
                    for a, b in zip(*compare_groups_times)
                ],
                color="green",
            )

        ax.legend()
    else:
        rects1 = ax.barh(
            x - width / 2,
            ref1_times,
            width,
            label=f"{ref1} - {sha_1}",
            color=("steelblue" if clean else "deepskyblue"),
        )

        if not single:
            ax.barh(
                x + width / 2,
                ref2_times,
                width,
                label=f"{ref2} - {sha_2}",
                color=("darkorange" if clean else "sandybrown"),
            )

        ax.set_yticklabels(
            queries,
            fontdict={
                "fontsize": "large" if len(queries) <= 10 else 6,
            },
        )

        if not clean:
            if single:
                ax.bar_label(rects1, padding=3)
            else:
                ax.bar_label(
                    rects1,
                    labels=[
                        # Only shows the percentage of difference if the it is greater than 1% and is positive.
                        ""
                        if 0 <= (a - b) / b <= 0.01 or a - b < 0
                        else f"{(a - b) / b * 100:+.2f}%"
                        for a, b in zip(ref1_times, ref2_times)
                    ],
                    color="red",
                )

                ax.bar_label(
                    rects1,
                    labels=[
                        # Only shows the percentage of difference if the it is greater than 1% and is negative.
                        ""
                        if -0.01 <= (a - b) / b <= 0 or a - b > 0
                        else f"{(a - b) / b * 100:+.2f}%"
                        for a, b in zip(ref1_times, ref2_times)
                    ],
                    color="green",
                )

    ax.legend()

    fig.tight_layout()

    folder: str
    if ref1 != "master":
        if ref2 != "master":
            folder = f"{ref1}_vs_{ref2}"
        else:
            folder = ref1
    else:
        folder = ref2

    try:
        os.mkdir(f"reports/{folder}")
    except:
        pass
    filename = f"reports/{folder}/report-{input}.png"
    plt.savefig(filename)


if __name__ == "__main__":
    main(sys.argv[1:])
