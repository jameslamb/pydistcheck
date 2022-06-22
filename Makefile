.PHONY: format
format:
	black .

.PHONY: lint
lint:
	shellcheck \
		--exclude=SC2002 \
		bin/*.sh && \
	black \
		--check \
		.
