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
	black .

.PHONY: full-run
full-run:
	bin/full-run.sh \
		"$(PACKAGE_NAME)"

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

.PHONY: smoke-tests
smoke-tests: build install
	@echo "running smoke tests" && \
	mkdir -p ./smoke-tests
	# wheel-only package
	@echo "  - catboost" && \
	bin/full-run.sh \
		"catboost" \
		"$(OUTPUT_DIR)/catboost"
	# package where source distro is a .zip
	@echo "  - numpy" && \
	bin/full-run.sh \
		"numpy" \
		"$(OUTPUT_DIR)/numpy"
	# package with so many files that `find -exec du -ch` has to batch results
	@echo "  - tensorflow" && \
	bin/full-run.sh \
		"tensorflow" \
		"$(OUTPUT_DIR)/tensorflow"
	@echo "done running smoke tests"

.PHONY: test
test:
	py-artifact-linter check --help
	py-artifact-linter check \
		--max-allowed-files 4 \
		$$(pwd)/dist/py-artifact-linter*.tar.gz
	py-artifact-linter summarize \
		$$(pwd)/dist/py-artifact-linter*.tar.gz
