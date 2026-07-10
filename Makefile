.PHONY: build publish publish-test clean-dist test lint security

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
	$(VENV)/bin/pytest -v --cov=simplegals --cov-report term-missing --cov-report term:skip-covered --cov-report xml:coverage.xml tests

lint:
	$(VENV)/bin/pycodestyle --max-line-length=120 simplegals/ tests/
	$(VENV)/bin/pylint simplegals/

security:
	$(VENV)/bin/bandit -r simplegals/
	# pillow CVEs are ignored here to mirror .github/workflows/sca.yml: term-image
	# caps pillow <12, below the 12.1.1+ fix. Drop these when term-image allows pillow>=12.
	$(VENV)/bin/pip-audit \
		--ignore-vuln PYSEC-2026-165 \
		--ignore-vuln CVE-2026-25990 \
		--ignore-vuln CVE-2026-40192 \
		--ignore-vuln CVE-2026-42309 \
		--ignore-vuln CVE-2026-42310 \
		--ignore-vuln CVE-2026-42311

clean-dist:
	rm -rf dist/
