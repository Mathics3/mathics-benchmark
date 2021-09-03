"""Generate a bar plot for a particular benchmark.

Examples:
- Compare a head against master:
  python ./mathics_benchmark/bench.py calculator-fns quickpatterntest
  python ./mathics_benchmark/compare.py calculator-fns quickpatterntest
- Compare two heads:
  python ./mathics_benchmark/bench.py calculator-fns quickpatterntest
  python ./mathics_benchmark/bench.py calculator-fns improve-rational-performance
  python ./mathics_benchmark/compare.py calculator-fns quickpatterntest improve-rational-performance
- Compare specific group:
  python ./mathics_benchmark/bench.py calculator-fns quickpatterntest
  python ./mathics_benchmark/compare.py calculator-fns quickpatterntest -g Power
"""

import numpy as np
import matplotlib.pyplot as plt
import json
import click
import sys

from typing import Optional


@click.command()
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
@click.argument("input", nargs=1, type=click.Path(readable=True), required=True)
@click.argument("ref1", nargs=1, type=click.Path(readable=True), required=True)
@click.argument("ref2", nargs=1, type=click.Path(readable=True), default="master")
def main(group: Optional[str], clean: bool, input: str, ref1: str, ref2: str):
    sha_1: str
    sha_2: str

    queries = []
    ref1_times = []
    ref2_times = []

    with open(f"results/{input}_{ref1}.json") as file:
        object = json.load(file)

        sha_1 = object["info"]["git SHA"]

        if group:
            for query in object["timings"][group]:
                queries.append(query)

                # The time diveded by the number of interations.
                ref1_times.append(
                    object["timings"][group][query][1]
                    / object["timings"][group][query][0]
                )
        else:
            for queries_group in object["timings"]:
                for query in object["timings"][queries_group]:
                    queries.append(query)

                    # The time diveded by the number of interations.
                    ref1_times.append(
                        object["timings"][queries_group][query][1]
                        / object["timings"][queries_group][query][0]
                    )

    path = (
        f"results/{input}.json" if ref2 == "master" else f"results/{input}_{ref2}.json"
    )

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
    rects1 = ax.barh(
        x - width / 2,
        ref1_times,
        width,
        label=f"{ref1} - {sha_1}",
        color=("steelblue" if clean else "deepskyblue"),
    )
    rects2 = ax.barh(
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
    ax.set_yticklabels(queries)
    ax.legend()

    if not clean:
        ax.bar_label(
            rects1,
            labels=[
                # Only shows the percentage of difference if the it isn't small and is positive.
                ""
                if 0 <= a - b <= 0.0001 or a - b < 0
                else f"{(a - b) / b * 100:+.2f}%"
                for a, b in zip(ref1_times, ref2_times)
            ],
            color="red",
        )

        ax.bar_label(
            rects1,
            labels=[
                # Only shows the percentage of difference if the it isn't small and is negative.
                ""
                if -0.0001 <= a - b <= 0 or a - b > 0
                else f"{(a - b) / b * 100:+.2f}%"
                for a, b in zip(ref1_times, ref2_times)
            ],
            color="green",
        )

    fig.tight_layout()

    plt.savefig("report.png")


if __name__ == "__main__":
    main(sys.argv[1:])
