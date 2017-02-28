import logging

logger = logging.getLogger('app')


def home(request):
    logger.info('Doing some division')
    1 / 0
