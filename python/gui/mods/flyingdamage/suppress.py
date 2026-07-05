# -*- coding: utf-8 -*-
# suppress.py  --  Python 2.7
# Standard floating damage over tanks is drawn by
#   VehicleMarkerPlugin.__showDamageIcon  (name-mangled: _VehicleMarkerPlugin__showDamageIcon)
# across all game modes. We suppress exactly that method, and NOTHING else.

import sys
import logging

from .utils import override
from .settings.config import g_config

logger = logging.getLogger(__name__)

# The exact (mangled) method that renders the standard damage number.
_TARGET_METHOD = '_VehicleMarkerPlugin__showDamageIcon'

# Only touch classes whose name ends with this. Never our own module, never
# Vehicle.*, never other mods' avatar hooks.
_TARGET_CLASS_SUFFIX = 'VehicleMarkerPlugin'

# Modules we must never patch into.
_SKIP_MODULE_FRAGMENTS = ('flyingdamage', 'mod_ibs', 'playerspaneldamage')


_installed = [False]


def installSuppression():
    if _installed[0]:
        return
    if not g_config.hideStandard:
        logger.info('[FlyingDamage] suppression disabled')
        return
    _installed[0] = True

    hooked = 0
    for modName, mod in list(sys.modules.items()):
        if mod is None:
            continue
        low = modName.lower()
        if any(frag in low for frag in _SKIP_MODULE_FRAGMENTS):
            continue
        # Only scan marker-plugin modules.
        if 'markers2d' not in low and 'marker' not in low:
            continue
        for attr in dir(mod):
            if not attr.endswith(_TARGET_CLASS_SUFFIX):
                continue
            cls = getattr(mod, attr, None)
            if not isinstance(cls, type):
                continue
            if _TARGET_METHOD not in cls.__dict__:
                # Only patch the class that actually DEFINES it (avoid double).
                continue
            try:
                def _suppressed(base, self, *a, **k):
                    if g_config.hideStandard:
                        return None
                    return base(self, *a, **k)
                override(cls, _TARGET_METHOD, _suppressed)
                hooked += 1
                logger.info('[FlyingDamage] suppressed %s.%s (%s)',
                            attr, _TARGET_METHOD, modName)
            except Exception:
                logger.info('[FlyingDamage] suppress fail %s', modName, exc_info=True)

    logger.info('[FlyingDamage] standard damage suppression: %d hooks', hooked)
    if hooked == 0:
        logger.warning('[FlyingDamage] no VehicleMarkerPlugin.__showDamageIcon found')
