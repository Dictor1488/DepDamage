# -*- coding: utf-8 -*-
# suppress.py  --  Python 2.7
# Diagnostic: dump ALL methods of the vehicle-marker plugins + base classes so
# we can find the exact method that pushes the standard floating damage number.

import logging

from .utils import override
from .settings.config import g_config

logger = logging.getLogger(__name__)

_PLUGIN_MODULE = 'gui.Scaleform.daapi.view.battle.shared.markers2d.plugins'
_PLUGIN_CLASSES = [
    'VehicleMarkerTargetPlugin',
    'MarkerPlugin',
]

# Fragments likely to be the damage-display method (broadened).
_METHOD_HINTS = [
    'damage', 'health', 'hp', 'showdmg', 'senddmg', 'hit',
    'as_show', 'as_update', 'invoke', 'setdamage', 'updatemarker',
]

# Method names we must NOT hook (would break the marker entirely).
_SAFE_SKIP = ['__init__', 'start', 'stop', 'fini', 'init', 'destroy',
              'restartallmarkers']


def installSuppression():
    try:
        mod = __import__(_PLUGIN_MODULE, fromlist=['*'])
    except Exception:
        logger.error('[FlyingDamage] cannot import markers2d.plugins', exc_info=True)
        return

    for clsName in _PLUGIN_CLASSES:
        cls = getattr(mod, clsName, None)
        if not isinstance(cls, type):
            logger.info('[FlyingDamage] %s not found', clsName)
            continue

        # Dump the full method resolution: class + its base classes.
        chain = []
        for c in cls.__mro__:
            chain.append(c.__name__)
        logger.info('[FlyingDamage] %s MRO: %s', clsName, chain)

        methods = sorted([m for m in dir(cls) if not m.startswith('__')])
        logger.info('[FlyingDamage] %s ALL methods: %s', clsName, methods)

    if not g_config.hideStandard:
        return

    # Try to hook candidates (only after we know names; harmless if none match).
    hooked = 0
    for clsName in _PLUGIN_CLASSES:
        cls = getattr(mod, clsName, None)
        if not isinstance(cls, type):
            continue
        for m in dir(cls):
            ml = m.lower()
            if ml in _SAFE_SKIP:
                continue
            if any(h in ml for h in _METHOD_HINTS) and ('show' in ml or 'damage' in ml):
                try:
                    def _suppressed(base, self, *a, **k):
                        if g_config.hideStandard:
                            return None
                        return base(self, *a, **k)
                    override(cls, m, _suppressed)
                    hooked += 1
                    logger.info('[FlyingDamage] suppressed %s.%s', clsName, m)
                except Exception:
                    pass
    logger.info('[FlyingDamage] suppression hooks: %d', hooked)
