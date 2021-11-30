#!/usr/bin/env python3

"""
Command-line program to run a benchmark suite from a YAML configuration file
on mathics-core at a given git reference.

 Examples:
 - Run benchmark in master:
   python ./mathics_benchmark/bench.py bench-1565
 - Runs a benchmark in a specifc head:
   python ./mathics_benchmark/bench.py bench-1565 quickpatterntest2
 - Runs a benchmark with verbose output:
   python ./mathics_benchmark/bench.py -v bench-1565
 - Pull before running the benchmark:
   python ./mathics_benchmark/bench.py -p bench-1565
 - Override the number of iterations:
   python ./mathics_benchmark/bench.py -i 10 bench-1565

If you installed mathics-benchmark, this file can be called as a binary, e.g.:
- mathics-bench ContinuedFraction
"""

from git import Repo
from typing import Optional

from pathlib import Path
import click
import importlib
import json
import mathics.session
import os
import os.path as osp
import platform
import psutil
import subprocess
import sys
import timeit
import yaml

from mathics.core.parser import parse, MathicsSingleLineFeeder


def source_dir():
    return osp.dirname(__file__)


my_dir = source_dir()


def dump_info(
    git_repo,
    cython: bool,
    timings: dict,
    verbose: int,
    output_path: Optional[str],
) -> None:
    """Write gathered data if `output_path` given. Otherwise if verbose > 0,
    just print out the gathered data.

    `timings`: a dictionary of timing information
    `git_repo`: the git repository for Mathics core.
    """
    dump_info = {"timings": timings, "info": get_info(git_repo, cython)}
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


def get_bench_data(config: str) -> dict:
    for path in [
        config,
        osp.join(my_dir, "benchmarks", config),
        osp.join(my_dir, "../", "benchmarks", config),
        osp.join(my_dir, "benchmarks", config + ".yaml"),
        osp.join(my_dir, "../", "benchmarks", config + ".yaml"),
    ]:
        if osp.isfile(path):
            break

    bench_data = yaml.load(open(path, "r"), Loader=yaml.FullLoader)

    if "includes" in bench_data:
        include_file: str

        if "categories" not in bench_data:
            # This allows files without categories, only includes.
            bench_data["categories"] = {}

        for include_file in bench_data["includes"]:
            # The line bellow is recursive.
            include_file_bench_data = get_bench_data(include_file)

            # If that file has a default iteration number we add that number to every category which don't have an iteration number.
            # If we don't do that, the main file iteration number will override the included file iteration number.
            if "interations" in include_file_bench_data:
                for category in include_file_bench_data["categories"]:
                    if "iterations" not in category:
                        category["iterations"] = include_file_bench_data["iterations"]

            bench_data["categories"].update(include_file_bench_data["categories"])

    return bench_data


def get_info(repo, cython: bool) -> dict:

    locals = {"__version__": "??"}
    exec(
        open(osp.join(my_dir, "../", "mathics-core", "mathics", "version.py")).read(),
        {},
        locals,
    )

    python_implementation: str = platform.python_implementation()
    python_version: str = ".".join(str(number) for number in sys.version_info[:3])

    info = {
        "Has Cython": "Yes" if cython else "No",
        "Git SHA": repo.head.commit.hexsha[:6],
        "Memory Available": psutil.virtual_memory().available,
        "Mathics-version": locals["__version__"],
        "Platform": sys.platform,
        "Processor": platform.machine(),
        "Python version": f"{python_implementation} {python_version}",
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
@click.argument("config", nargs=1, type=click.Path(readable=True), required=True)
@click.argument("ref", nargs=1, type=click.Path(readable=True), default="master")
def main(
    verbose: int,
    pull: bool,
    cython: bool,
    config: str,
    ref: str,
    iterations: Optional[int],
):
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

    bench_data = get_bench_data(config)
    repo = setup_git()
    results_dir = osp.join(my_dir, "..", "results")
    short_name = osp.basename(config)
    if short_name.endswith(".yaml"):
        short_name = short_name[: len(".yaml")]

    if pull:
        repo.remotes.origin.pull()

    repo.git.checkout(ref)

    if verbose:
        print(f"Mathics git repo {repo.working_dir} at {repo.head.commit.hexsha[:6]}")

    rc = setup_environment(verbose, cython)
    if rc != 0:
        return rc

    if ref != "master":
        try:
            os.mkdir(osp.join(results_dir, ref))
        except Exception:
            pass

    timings = run_benchmark(bench_data, verbose)
    dump_info(
        repo,
        cython,
        timings,
        verbose,
        osp.join(
            results_dir,
            f"{ref}/{short_name}.json" if ref != "master" else f"{short_name}.json",
        ),
    )

    repo.git.checkout("master")

    return 0


def setup_environment(verbose: int, cython: bool) -> int:
    """
    Make sure Mathics core is set to the right place.
    We will basically run "./setup.py develop".
    """
    command: list[str] = [sys.executable, "./setup.py", "develop"]
    mathics_dir = osp.join(my_dir, "../", "mathics-core")

    env: dict = {}
    if cython:
        subprocess.run(["make"], cwd=mathics_dir, capture_output=False)
    else:
        subprocess.run(["make", "clean-cython"], cwd=mathics_dir, capture_output=False)

        # If NO_CYTHON is set, Cython isn't used
        # Otherwise, it is used
        env["NO_CYTHON"] = "1"

    completed_process = subprocess.run(
        command, capture_output=True, cwd=mathics_dir, env=env
    )
    rc: int = completed_process.returncode
    if rc != 0:
        print(f"""Running '{" ".join(command)}' gave {rc} return code.""")
    if verbose > 1:
        print("Output was:")
        print(completed_process.stdout.decode("utf-8"))
    return rc


def run_benchmark(
    bench_data: dict, verbose: int, iterations: Optional[int] = None
) -> dict:
    """Runs the expressions in `bench_data` to get timings and return the
    timings and number of runs associated with the data in a
    dictionary.

    If `verbose` is set, show what's going on as it happens.
    """
    importlib.reload(mathics.session)
    session = mathics.session.MathicsSession(add_builtin=True, catch_interrupt=False)

    default_iterations = bench_data.get("iterations", 50)
    timings = {}  # where we accumulate timings from the following loop..
    for category, value in bench_data["categories"].items():
        iterations = (
            int(iterations)
            if iterations
            else value.get("iterations", default_iterations)
        )
        if verbose:
            print(f"{iterations} iterations of {category}...")
        group = timings[category] = {}

        if "setup_exprs" in value:
            for str_expr in value["setup_exprs"]:
                expr = parse(session.definitions, MathicsSingleLineFeeder(str_expr))
                expr.evaluate(session.evaluation)

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


default_git_repo = str(Path(get_srcdir()).parent / Path("mathics-core"))


def setup_git(repo_path: str = default_git_repo):
    repo = Repo(repo_path)
    return repo


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
