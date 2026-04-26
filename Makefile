.PHONY: build publish publish-test clean-dist test

VENV := .venv
PYTHON := $(VENV)/bin/python
TWINE := $(VENV)/bin/twine

build: clean-dist
	$(PYTHON) -m build

publish-test: build
	$(TWINE) upload --verbose --repository simplegalstest dist/*

publish: build
	$(TWINE) upload --verbose --repository simplegalsprod dist/*

test:
	$(VENV)/bin/pytest tests/

clean-dist:
	rm -rf dist/
