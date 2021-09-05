#!/usr/bin/env python3

"""
Command-line program to run a benchmark suite from a YAML configuration file
on Mathics-core at a given git reference.

 Examples:
 - Run benchmark in master:
   python ./mathics_benchmark/bench.py bench-1565
 - Runs a benchmark in a specifc head:
   python ./mathics_benchmark/bench.py bench-1565 quickpatterntest2
 - Runs a benchmark with verbose output:
   python ./mathics_benchmark/bench.py -v bench-1565
 - Pull before running the benchmark:
   python ./mathics_benchmark/bench.py -p bench-1565
"""

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


def source_dir():
    return osp.dirname(__file__)


my_dir = source_dir()

# Stores __version__ in the current namespace. This can't be executed inside a function.
exec(
    compile(
        open(osp.join(my_dir, "Mathics", "mathics", "version.py")).read(),
        osp.join(my_dir, "Mathics", "mathics", "version.py"),
        "exec",
    )
)


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

        if verbose > 1:
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
        "Mathics-version": __version__,
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
@click.argument("config", nargs=1, type=click.Path(readable=True), required=True)
@click.argument("ref", nargs=1, type=click.Path(readable=True), required=False)
def main(verbose: int, pull: bool, config: str, ref: Optional[str]):
    """Runs benchmarks specified in CONFIG on Mathics core at git reference REF.

    CONFIG is either:

    A file path (relative or absolute) like "benchmarks/String_vs_StringQ.yaml".

    A short name under the "benchmarks" subdirectory of the installed
    package.  Here we will add the "yaml" extension if needed. So
    "String_vs_StringQ" refers to "benchmarks/String_vs_StringQ.yaml"
    in the package directory.

    REF is a git reference which can be a branch name, e.g. "master",
    a tag name like "4.0.0", or a short or long SHA1 like "d929af3b"
    or "d929af3b3ad1a5926942891ad98b17705d423bf2".

    REF defaults to "master".
    """

    for path in [
        config,
        osp.join(my_dir, "benchmarks", config),
        osp.join(my_dir, "benchmarks", config + ".yaml"),
    ]:
        if osp.isfile(path):
            break
    bench_data = yaml.load(open(path, "r"), Loader=yaml.FullLoader)
    repo = setup_git()

    repo.git.checkout("master")

    if pull:
        repo.remotes.origin.pull()

    if verbose:
        print(f"Mathics git repo {repo.working_dir} at {repo.head.commit.hexsha[:6]}")

    timings = run_benchmark(bench_data, verbose)

    results_dir = osp.join(my_dir, "..", "results")
    short_name = osp.basename(config)
    if short_name.endswith(".yaml"):
        short_name = short_name[: len(".yaml")]
    dump_info(repo, timings, verbose, osp.join(results_dir, short_name + ".json"))

    if ref:
        repo.git.checkout(ref)

        if verbose:
            print(
                f"Mathics git repo {repo.working_dir} at {repo.head.commit.hexsha[:6]}"
            )

        timings = run_benchmark(bench_data, verbose)
        dump_info(
            repo, timings, verbose, osp.join(results_dir, f"{short_name}_{ref}.json")
        )

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
