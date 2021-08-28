"""Runs a particular benchmark."""

import click
import sys
import timeit
import json
import yaml

from mathics.session import MathicsSession
from mathics.core.parser import parse, MathicsSingleLineFeeder


@click.command()
@click.option(
    "-v",
    "--verbose",
    count=True,
    help="verbosity level in tracing.\n"
    "Can be supplied multiple times to increase verbosity.",
)
@click.argument("input", nargs=1, type=click.Path(readable=True), required=True)
@click.argument("output", nargs=1, type=click.Path(writable=True), required=False)
def main(verbose: int, input, output):
    bench_data = yaml.load(open(input, "r"), Loader=yaml.FullLoader)
    timings = run_benchmark(bench_data, verbose)

    if output:
        json.dump(timings, open(output, "w"))


def run_benchmark(bench_data: dict, verbose: int) -> dict:
    session = MathicsSession(add_builtin=True, catch_interrupt=False)

    if "iterations" in bench_data:
        default_iterations = bench_data.pop("iterations")
    else:
        default_iterations = 50

    timings = {}
    for category, value in bench_data["categories"].items():
        iterations = value.get("iterations", default_iterations)
        if verbose:
            print(f"{iterations} iterations of {category}...")
        group = timings[category] = {}
        for str_expr in value["exprs"]:
            expr = parse(session.definitions, MathicsSingleLineFeeder(str_expr))
            elapsed_time = timeit.timeit(
                lambda: expr.evaluate(session.evaluation), number=iterations
            )
            if verbose:
                print("  %1.6f secs for: %-40s" % (elapsed_time, str_expr))
            group[str_expr] = (iterations, elapsed_time)
        if verbose:
            print()
    return timings


if __name__ == "__main__":
    main(sys.argv[1:])
