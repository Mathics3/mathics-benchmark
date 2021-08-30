PYTHON ?= python3
REPOSITORY ?= https://github.com/mathics/Mathics

all:
	$(PYTHON) ./setup.py

change-repo:
	echo -e ""