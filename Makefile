bootstrap: bootstrap-tests
	pip install -e . --use-mirrors

bootstrap-tests:
	pip install -r test-requirements.txt --use-mirrors
	pip install "flake8>=1.6" --use-mirrors

test: lint
	@echo "Running Python tests"
	python runtests.py -x
	@echo ""

lint:
	@echo "Linting Python files"
	flake8 --exclude=migrations --ignore=E501,E225,E121,E123,E124,E125,E127,E128 raven || exit 1
	@echo ""

coverage:
	coverage run runtests.py --include=raven/* && \
	coverage html --omit=*/migrations/* -d cover
