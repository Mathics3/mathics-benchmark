"""Generate a bar plot for a particular benchmark.

Examples:
- Compare a head against master:
  python ./mathics_benchmark/compare.py calculator-fns quickpatterntest
- Compare two heads:
  python ./mathics_benchmark/compare.py calculator-fns quickpatterntest improve-rational-performance
- Compare specific group:
  python ./mathics_benchmark/compare.py calculator-fns quickpatterntest -g Power
- Compare without showing the percentage difference:
  python ./mathics_benchmark/compare.py calculator-fns quickpatterntest -c
- Pull before running the benchmark:
  python ./mathics_benchmark/compare.py calculator-fns quickpatterntest -p
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
    help="If passed generate the plot only for the queries in that group",
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
    input: str,
    ref1: str,
    ref2: str,
):
    if input == "run-all":
        import glob 
        inputs = glob.glob("benchmarks/*.yaml")
        for input in inputs:
            print(f"running {input[11:]}")
            worker(verbose, group, clean, pull, force, single, logarithmic, input[11:], ref1, ref2)    
    else:
        worker(verbose, group, clean, pull, force, single, logarithmic, input, ref1, ref2)    
        


def worker(
        verbose: int,
    group: Optional[str],
    clean: bool,
    pull: bool,
    force: bool,
    single: bool,
    logarithmic: bool,
    input: str,
    ref1: str,
    ref2: str,
):
    sha_1: str
    sha_2: str

    queries: list[float] = []
    ref1_times: list[float] = []
    ref2_times: list[float] = []

    if input[-5:] == ".yaml":
        input = input[:-5]
    path = (f"results/{ref1}/{input}.json")
    folder = f"{ref1}"
    try:
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

        try:
            bench.main(arguments)
        except SystemExit:
            print("... done")

    with open(path) as file:
        object = json.load(file)

        sha_1 = object["info"]["git SHA"]

        if group:
            for query in object["timings"][group]:
                queries.append(break_string(query, 25 if len(queries) <= 10 else 35))

                # The time diveded by the number of interations.
                ref1_times.append(
                    object["timings"][group][query][1]
                    / object["timings"][group][query][0]
                )
        else:
            for queries_group in object["timings"]:
                for query in object["timings"][queries_group]:
                    queries.append(
                        break_string(query, 25 if len(queries) <= 10 else 35)
                    )

                    # The time diveded by the number of interations.
                    ref1_times.append(
                        object["timings"][queries_group][query][1]
                        / object["timings"][queries_group][query][0]
                    )

    if not single:
        path = (
            f"results/{input}.json"
            if ref2 == "master"
            else f"results/{input}_{ref2}.json"
        )

        if not osp.isfile(path) or force:
            arguments = [input]

            if ref2 != "master":
                arguments.append(ref2)

            if pull:
                arguments.append("-p")

            bench.main(arguments)

        with open(path) as file:
            object = json.load(file)

            sha_2 = object["info"]["git SHA"]

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

    x = np.arange(len(queries))  # the label locations
    width = 0.35  # the width of the bars

    fig, ax = plt.subplots()
    if logarithmic:
        ax.set_xscale("log")

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

    # Add some text for labels, title and custom x-axis tick labels, etc.
    ax.set_xlabel("seconds")
    ax.set_title(input)
    ax.set_yticks(x)
    ax.set_yticklabels(
        queries,
        fontdict={
            "fontsize": "large" if len(queries) <= 5 else 6,
        },
    )
    ax.legend()

    if not clean:
        if single:
            ax.bar_label(rects1, padding=3)
        else:
            # The percentage dirrence between a and b is: (a - b) / b * 100

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

    fig.tight_layout()
    folder = f"{ref1}_vs_{ref2}" if ref2 != "master" else ref1
    try:
        os.mkdir(f"reports/{folder}")
    except:
        pass
    filename = f"reports/{folder}/report-{input}.png"
    plt.savefig(filename)


if __name__ == "__main__":
    main(sys.argv[1:])
