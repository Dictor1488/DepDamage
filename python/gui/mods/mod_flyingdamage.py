# -*- coding: utf-8 -*-
# mod_flyingdamage.py -- Python 2.7 entry point (AS3 marker-layer renderer)

import logging

logger = logging.getLogger(__name__)
logger.info('[FD_AS3] === module imported ===')


def init():
    logger.info('[FD_AS3] init() called')
    try:
        from flyingdamage import g_controller
        g_controller.init()
        logger.info('[FD_AS3] init() OK')
    except Exception:
        logger.error('[FD_AS3] init() CRASHED', exc_info=True)


def fini():
    logger.info('[FD_AS3] fini() called')
    try:
        from flyingdamage import g_controller
        g_controller.fini()
    except Exception:
        logger.error('[FD_AS3] fini() CRASHED', exc_info=True)
