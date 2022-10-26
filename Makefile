OUTPUT_DIR ?= $(PWD)/tmp-dir

.PHONY: build
build:
	pipx install cibuildwheel
	rm -r ./dist || true
	pipx run build --sdist

.PHONY: clean
clean:
	rm -r ./tmp-dir

.PHONY: format
format:
	isort .
	black .

.PHONY: full-run
full-run:
	bin/full-run.sh \
		"$(PACKAGE_NAME)" \
		"$(OUTPUT_DIR)"

.PHONY: install
install:
	pipx install --force dist/*.tar.gz

.PHONY: lint
lint:
	shellcheck \
		--exclude=SC2002 \
		bin/*.sh
	black \
		--check \
		.
	flake8 .
	mypy .
	pylint ./src

.PHONY: smoke-tests
smoke-tests:
	OUTPUT_DIR="$(OUTPUT_DIR)" \
	bin/run-smoke-tests.sh

.PHONY: test-data
test-data:
	bash ./bin/create-test-data.sh

.PHONY: test
test:
	PYTHONPATH=src \
	pytest \
		--cov=src/pydistcheck \
		--cov-fail-under=100 \
		--cov-report="term" \
		--cov-report="html:htmlcov" \
		./tests
