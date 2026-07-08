# -*- coding: utf-8 -*-
# mod_flyingdamage.py -- Python 2.7 entry point
# The mod now ships the provided battleVehicleMarkersApp.swf directly.
# No Python damage renderer, no overlay SWF, no damage suppression hook.

import logging

logger = logging.getLogger(__name__)
logger.info('[FlyingDamage] module imported: battleVehicleMarkersApp.swf resource patch only')


def init():
    logger.info('[FlyingDamage] init: no Python damage hooks; using provided battleVehicleMarkersApp.swf')


def fini():
    logger.info('[FlyingDamage] fini')
