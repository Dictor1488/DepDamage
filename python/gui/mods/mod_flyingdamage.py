# -*- coding: utf-8 -*-
# mod_flyingdamage.py  --  Python 2.7 entry point (Gameface renderer)

import logging

logger = logging.getLogger(__name__)
logger.info('[FlyingDamageGF] === module imported (Gameface renderer) ===')


def init():
    logger.info('[FlyingDamageGF] init() called')
    try:
        from flyingdamage import g_controller
        g_controller.init()
        logger.info('[FlyingDamageGF] init() OK')
    except Exception:
        logger.error('[FlyingDamageGF] init() CRASHED', exc_info=True)


def fini():
    logger.info('[FlyingDamageGF] fini() called')
    try:
        from flyingdamage import g_controller
        g_controller.fini()
    except Exception:
        logger.error('[FlyingDamageGF] fini() CRASHED', exc_info=True)
