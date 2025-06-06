NUMPY_WIN_DEBUG_WHL=tests/data/numpy-1.26.3-cp310-cp310-win_amd64.whl

.PHONY: build
build:
	rm -r ./dist || true
	pipx run build --sdist --wheel

.PHONY: check-test-packages
check-test-packages:
	docker run \
		--rm \
		-v "$${PWD}/tests/data":/opt/test-packages:ro \
		-v "$${PWD}/bin":/ci-scripts \
		--workdir /ci-scripts \
		-it python:latest \
		./check-test-packages.sh /opt/test-packages

.PHONY: check-wheels
check-dists:
	gunzip -t dist/*.tar.gz
	zip -T dist/*.whl
	check-wheel-contents dist/*.whl
	# pyroma can be added again once https://github.com/regebro/pyroma/issues/93 is resolved
	# pyroma --min=10 dist/*.tar.gz
	twine check --strict dist/*

.PHONY: clean
clean:
	rm -rf ./tmp-dir
	rm -rf ./tests/data/baseballmetrics/dist
	rm -rf ./tests/data/baseballmetrics/baseballmetrics.egg-info
	rm -rf ./tests/data/baseballmetrics/_skbuild

.PHONY: install
install:
	pipx install --force '.[conda]'

.PHONY: lint
lint:
	pre-commit run --all-files

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
	bin/create-test-data-bdist.sh

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
		bash -c "apt-get update && apt-get install -y --no-install-recommends ca-certificates curl zip && bin/create-test-data-sdist.sh"

.PHONY: test-data-bdist
test-data-bdist: \
	linux-wheel \
	mac-wheel \
	test-data-macos-conda-tarbz2-packages \
	test-data-conda-dot-conda-packages

# NOTE: .bz2 packages were created with conda-build 3.27.0
.PHONY: test-data-conda-packages
test-data-macos-conda-tarbz2-packages:
	bin/create-test-data-conda.sh 'osx-64'

.PHONY: test-data-conda-dot-conda-packages
test-data-conda-dot-conda-packages:
	cph transmute \
		--out-folder ./tests/data \
		'./tests/data/*-0.tar.bz2' \
		'.conda'

$(NUMPY_WIN_DEBUG_WHL):
	curl \
		https://files.pythonhosted.org/packages/be/b0/611101990ddac767e54e2d27d1f4576ae1662cca64e2d55ef0e62558ec26/numpy-1.26.3-cp310-cp310-win_amd64.whl \
		-o $(NUMPY_WIN_DEBUG_WHL)

.PHONY: test
test: $(NUMPY_WIN_DEBUG_WHL)
	pytest \
		--cov pydistcheck \
		./tests

.PHONY: test-local
test-local: $(NUMPY_WIN_DEBUG_WHL)
	PYTHONPATH=src \
	pytest \
		--cov=src/pydistcheck \
		--cov-report="term" \
		--cov-report="html:htmlcov" \
		./tests
