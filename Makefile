test:
	coverage run runtests.py --include=raven/* && \
	coverage html --omit=*/migrations/* -d cover
