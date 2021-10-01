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
	git submodule update --remote

#: install mathics-benchmark
install:
	$(PIP) install -e .

#: remove the reports and results
clean:
	find reports -name "*.png" -delete
	find results -name "*.json" -delete

#: initialize venv
venv:
	chmod +x admin-tools/install-venv.sh
	./admin-tools/install-venv.sh
