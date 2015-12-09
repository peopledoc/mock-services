all:

.PHONY: install
install:
	pip install -e .

.PHONY: develop
develop: install
	pip install -e ".[test]"

.PHONY: tests
tests:
	flake8 .
	python -m unittest discover tests/

.PHONY: release
release:
	pip install -e ".[release]"
	fullrelease
