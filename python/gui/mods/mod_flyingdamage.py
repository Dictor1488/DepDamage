# -*- coding: utf-8 -*-
"""DepDamage entry point.

Python 2.7 client-side WoT mod entry.
"""

import logging

from flyingdamage import hooks

LOG = logging.getLogger('DepDamage')


def init():
    LOG.info('[DepDamage] init')
    hooks.init()


def fini():
    LOG.info('[DepDamage] fini')
    hooks.fini()
