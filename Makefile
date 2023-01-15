.PHONY: build
build:
	pipx install cibuildwheel
	rm -r ./dist || true
	pipx run build --sdist --wheel

.PHONY: check-test-packages
check-test-packages:
	docker run \
		--rm \
		-v "$${PWD}/tests/data":/opt/test-packages:ro \
		-v "$${PWD}/bin":/ci-scripts \
		--workdir /ci-scripts \
		-it python:3.11 \
		./check-test-packages.sh /opt/test-packages

.PHONY: clean
clean:
	rm -rf ./tmp-dir
	rm -rf ./tests/data/baseballmetrics/dist
	rm -rf ./tests/data/baseballmetrics/baseballmetrics.egg-info
	rm -rf ./tests/data/baseballmetrics/_skbuild

.PHONY: format
format:
	isort .
	black .

.PHONY: install
install:
	pipx install --force .

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

.PHONY: linux-wheel
linux-wheel:
	docker run \
		--rm \
		-v $$(pwd):/usr/local/src \
		--workdir /usr/local/src \
		--entrypoint="" \
		-it quay.io/pypa/manylinux_2_28_x86_64 \
		bin/create-test-data-bdist.sh

.PHONY: mac-wheel
mac-wheel:
	cd ./tests/data/baseballmetrics && \
	pip wheel -w ./dist . && \
	mv ./dist/baseballmetrics-0.1.0-py3-none-macosx_*.whl ../


.PHONY: smoke-tests
smoke-tests:
	@bash ./bin/run-smoke-tests.sh

.PHONY: test-data-sdist
test-data-sdist:
	docker run \
		--rm \
		-v $$(pwd):/usr/local/src \
		--workdir /usr/local/src \
		--entrypoint="" \
		-it python:3.10 \
		bash -c "apt-get update && apt-get install -y --no-install-recommends ca-certificates curl zip && bin/create-test-data.sh"

.PHONY: test-data-bdist
test-data-bdist: \
	linux-wheel \
	mac-wheel

.PHONY: test
test:
	PYTHONPATH=src \
	pytest \
		--cov=src/pydistcheck \
		--cov-fail-under=100 \
		--cov-report="term" \
		--cov-report="html:htmlcov" \
		./tests
