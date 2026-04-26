.PHONY: build publish publish-test clean-dist test

VENV := .venv
PYTHON := $(VENV)/bin/python
TWINE := $(VENV)/bin/twine

build: clean-dist
	$(PYTHON) -m build

publish-test: build
	$(TWINE) upload --repository testpypi dist/*

publish: build
	$(TWINE) upload dist/*

test:
	$(VENV)/bin/pytest tests/

clean-dist:
	rm -rf dist/
