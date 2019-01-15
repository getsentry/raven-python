bootstrap:
	pip install -e "file://`pwd`#egg=raven[tests]"
	make setup-git

test: bootstrap lint
	@echo "Running Python tests"
	py.test -f tests
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

clean:
	rm -rf dist build

publish: clean
	python setup.py sdist bdist_wheel upload

dist: clean
	python setup.py sdist bdist_wheel

install-zeus-cli:
	npm install -g @zeus-ci/cli

travis-upload-dist: dist install-zeus-cli
	zeus upload -t "application/zip+wheel" dist/* \
		|| [[ ! "$(TRAVIS_BRANCH)" =~ ^release/ ]]

update-ca:
	curl -sSL https://mkcert.org/generate/ -o raven/data/cacert.pem

.PHONY: bootstrap test lint coverage setup-git publish update-ca dist clean install-zeus-cli travis-upload-dist
