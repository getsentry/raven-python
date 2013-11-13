bootstrap:
	pip install -e . --use-mirrors
	pip install "file://`pwd`#egg=raven[dev]" --use-mirrors
	pip install "file://`pwd`#egg=raven[tests]" --use-mirrors
	make setup-git

test: bootstrap lint
	@echo "Running Python tests"
	py.test -x tests
	@echo ""

lint:
	@echo "Linting Python files"
	PYFLAKES_NODOCTEST=1 flake8 raven || exit 1
	@echo ""

coverage:
	coverage run runtests.py --include=raven/* && \
	coverage html --omit=*/migrations/* -d cover

setup-git:
	git config branch.autosetuprebase always
	cd .git/hooks && ln -sf ../../hooks/* ./

publish:
	python setup.py sdist bdist_wheel upload

.PHONY: bootstrap test lint coverage setup-git publish
