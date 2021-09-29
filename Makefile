# A GNU Makefile to run various tasks - compatibility for us old-timers.

# Note: This makefile include remake-style target comments.
# These comments before the targets start with #:
# remake --tasks to shows the targets and the comments

PIP ?= pip3

#: default target
all: update install

#: update mathics-core
update:
	git submodule init
	git submodule update --recursive

#: install mathics-benchmark
install:
	$(PIP) install -e .

#: remove the reports and results
clean:
	rm reports/**/*.png results/**/*.json
