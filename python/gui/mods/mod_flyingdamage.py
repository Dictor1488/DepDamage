# -*- coding: utf-8 -*-
# mod_flyingdamage.py  --  Python 2.7 entry point (SWF battle-view version)

import logging

logger = logging.getLogger(__name__)
logger.info('[FlyingDamage] === module imported (SWF view) ===')


def init():
    logger.info('[FlyingDamage] init() called')
    try:
        from flyingdamage import g_controller
        g_controller.init()
        logger.info('[FlyingDamage] init() OK')
    except Exception:
        logger.error('[FlyingDamage] init() CRASHED', exc_info=True)


def fini():
    logger.info('[FlyingDamage] fini() called')
    try:
        from flyingdamage import g_controller
        g_controller.fini()
    except Exception:
        logger.error('[FlyingDamage] fini() CRASHED', exc_info=True)
