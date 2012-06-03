test:
	pep8 --exclude=migrations --ignore=E501,E225,E121,E123,E124,E125,E127,E128 raven || exit 1
	pyflakes -x W raven || exit 1
	coverage run runtests.py --include=raven/* && \
	coverage html --omit=*/migrations/* -d cover
