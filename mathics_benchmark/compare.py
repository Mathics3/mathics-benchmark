"""Generate a bar plot for a particular benchmark.

Example:
  python ./mathics_benchmark/bench.py calculator-fns quickpatterntest
  python ./mathics_benchmark/compare.py calculator-fns quickpatterntest
"""

import numpy as np
import matplotlib.pyplot as plt
import json
import click
import sys

@click.command()
@click.argument("input", nargs=1, type=click.Path(readable=True), required=True)
@click.argument("ref1", nargs=1, type=click.Path(readable=True), required=True)
@click.argument("ref2", nargs=1, type=click.Path(readable=True), default="master")
def main(input: str, ref1: str, ref2: str):
    sha_1: str
    sha_2: str

    names = []
    ref1_times = []
    ref2_times = []

    with open(f"results/{input}_{ref1}.json") as file:
        object = json.load(file)

        sha_1 = object['info']['git SHA']

        for group in object['timings']:
            for name in object['timings'][group]:
                ref1_times.append(object['timings'][group][name][1] / object['timings'][group][name][0])

    path = f"results/{input}.json" if ref2 == "master" else f"results/{input}_{ref2}.json"

    with open(path) as file:
        object = json.load(file)

        sha_2 = object['info']['git SHA']

        for group in object['timings']:
            for name in object['timings'][group]:
                names.append(name)
                ref2_times.append(object['timings'][group][name][1] / object['timings'][group][name][0])

    x = np.arange(len(names))  # the label locations
    width = 0.35  # the width of the bars

    fig, ax = plt.subplots()
    rects1 = ax.barh(x - width/2, ref1_times, width, label=f"{ref1} - {sha_1}")
    rects2 = ax.barh(x + width/2, ref2_times, width, label=f"{ref2} - {sha_2}")

    # Add some text for labels, title and custom x-axis tick labels, etc.
    ax.set_xlabel("seconds")
    ax.set_title(input)
    ax.set_yticks(x)
    ax.set_yticklabels(names)
    ax.legend()

    fig.tight_layout()

    plt.savefig("report.png")

if __name__ == "__main__":
    main(sys.argv[1:])
