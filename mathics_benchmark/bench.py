"""Runs a particular benchmark.

Example:
  python ./mathics_benchmark/bench.py -v bench-1565
"""

# Outside of this program: setup virtual environments to test Mathics on

from git import Repo
from typing import Optional

from pathlib import Path
import click
import os
import os.path as osp
import platform
import psutil
import sys
import timeit
import json
import yaml

from mathics.session import MathicsSession
from mathics.core.parser import parse, MathicsSingleLineFeeder


def dump_info(
    git_repo, timings: dict, verbose: int, output_path: Optional[str]
) -> None:
    """Write gathered data if `output_path` given. Otherwise if verbose > 0,
    just print out the gathered data.

    `timings`: a dictionary of timing information
    `git_repo`: the git repository for Mathics core.
    """
    dump_info = {"timings": timings, "info": get_info(git_repo)}
    if verbose:
        if output_path:
            print(f"Dumping information to file {output_path}")
        from pprint import pprint

        pprint(dump_info)
    if not output_path:
        return
    json.dump(dump_info, open(output_path, "w"))


def get_srcdir() -> str:
    """Retrieve the source directory of this program.
    We generally use that to find relative paths/parts of this code.
    """
    filename = osp.normcase(osp.dirname(osp.abspath(__file__)))
    return osp.realpath(filename)


def get_info(repo) -> dict:
    info = {
        "git SHA": repo.head.commit.hexsha[:6],
        "Memory Available": psutil.virtual_memory().available,
        "Platform": sys.platform,
        # "Mathics-version":  ???
        "Processor": platform.machine(),
        "System Memory": psutil.virtual_memory().total,
    }
    return info


@click.command()
@click.option(
    "-v",
    "--verbose",
    count=True,
    help="verbosity level in tracing.\n"
    "Can be supplied multiple times to increase verbosity.",
)
@click.option(
    "-p",
    "--pull",
    help="Update the Mathics repository",
    is_flag=True,
)
@click.argument("input", nargs=1, type=click.Path(readable=True), required=True)
@click.argument("head", nargs=1, type=click.Path(readable=True), required=False)
def main(verbose: int, pull: bool, input: str, head: Optional[str]):
    bench_data = yaml.load(
        open(f"benchmarks/{input}.yaml", "r"), Loader=yaml.FullLoader
    )
    repo = setup_git()

    repo.git.checkout("master")

    if pull:
        repo.remotes.origin.pull()

    if verbose:
        print(f"Mathics git repo {repo.working_dir} at {repo.head.commit.hexsha[:6]}")

    timings = run_benchmark(bench_data, verbose)
    dump_info(repo, timings, verbose, f"results/{input}.json")

    if head:
        repo.git.checkout(head)

        if verbose:
            print(
                f"Mathics git repo {repo.working_dir} at {repo.head.commit.hexsha[:6]}"
            )

        timings = run_benchmark(bench_data, verbose)
        dump_info(repo, timings, verbose, f"results/{input}_{head}.json")

        repo.git.checkout("master")


def run_benchmark(bench_data: dict, verbose: int) -> dict:
    """Runs the expressions in `bench_data` to get timings and return the
    timings and number of runs associated with the data in a
    dictionary.

    If `verbose` is set, show what's going on as it happens.
    """
    session = MathicsSession(add_builtin=True, catch_interrupt=False)

    default_iterations = bench_data.get("iterations", 50)
    timings = {}  # where we accumulate timings from the following loop..
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


default_git_repo = str(Path(get_srcdir()).parent / Path("Mathics"))


def setup_git(repo_path: str = default_git_repo):
    repo = Repo(repo_path)
    return repo


if __name__ == "__main__":
    main(sys.argv[1:])
