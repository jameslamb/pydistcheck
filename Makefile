OUTPUT_DIR ?= $(PWD)/tmp-dir

.PHONY: clean
clean:
	rm -r ./tmp-dir

.PHONY: format
format:
	black .

.PHONY: full-run
full-run:
	bin/full-run.sh \
		"$(PACKAGE_NAME)" \
		"$(OUTPUT_DIR)/$(PACKAGE_NAME)"

.PHONY: lint
lint:
	shellcheck \
		--exclude=SC2002 \
		bin/*.sh
	black \
		--check \
		.
