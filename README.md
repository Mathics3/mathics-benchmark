# mathics-benchmark
Benchmark tools for [mathics-core](https://github.com/Mathics3/mathics-core)

## How to install mathics-benchmark
First you need to get the source code:
```console
$ git clone https://github.com/Mathics3/mathics-benchmark
Cloning into 'mathics-benchmark'...
...
```
Initialize [venv](https://docs.python.org/3/library/venv.html):
```console
$ make venv
...
```
Install mathics-benchmark and download mathics-core:
```console
make
```

## How to use
mathics-benchmark has 2 scripts:
- mathics-bench: this script is useful for low-level benchmarking. See more details in how to use it [here](https://github.com/Mathics3/mathics-benchmark/blob/master/mathics_benchmark/bench.py).
- mathics-bench-compare: this script generates plots from the benchmarks and if necessary, calls mathics-bench. See more details in how to use it [here](https://github.com/Mathics3/mathics-benchmark/blob/master/mathics_benchmark/compare.py).

Example plot from mathics-bench-compare:
![example plot](https://user-images.githubusercontent.com/62714153/139678542-c2fb17f4-b129-4f13-b24b-445d69d41fda.png)

## The YAML configuration files
See the [example YAML](https://github.com/Mathics3/mathics-benchmark/blob/master/benchmarks/example.yaml) for more information about how to make a configuration file.
