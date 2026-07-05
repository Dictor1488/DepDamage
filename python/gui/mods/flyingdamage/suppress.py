# -*- coding: utf-8 -*-
# suppress.py  --  Python 2.7
# Standard floating damage is drawn by battleDamageIndicatorApp.swf, driven by a
# Python controller. We find that controller by scanning ALL loaded modules for
# a class named like a damage indicator, then hook its show method.

import sys
import logging

from .utils import override
from .settings.config import g_config

logger = logging.getLogger(__name__)

_SHOW_HINTS = ['showdamage', 'adddamage', 'updatedamage', 'as_showdamage',
               'as_adddamage', 'setdamage', '__showdamage', 'invoke']


def installSuppression():
    if not g_config.hideStandard:
        logger.info('[FlyingDamage] suppression disabled')
        return

    targets = _findDamageIndicatorClasses()
    if not targets:
        logger.warning('[FlyingDamage] no DamageIndicator class found in loaded modules')
        return

    hooked = 0
    for modName, clsName, cls in targets:
        logger.info('[FlyingDamage] candidate %s.%s methods: %s',
                    modName, clsName,
                    [m for m in dir(cls) if not m.startswith('__') and
                     ('amage' in m.lower() or 'show' in m.lower() or 'invoke' in m.lower())])
        for m in dir(cls):
            ml = m.lower()
            if any(h in ml for h in _SHOW_HINTS):
                try:
                    def _suppressed(base, self, *a, **k):
                        if g_config.hideStandard:
                            return None
                        return base(self, *a, **k)
                    override(cls, m, _suppressed)
                    hooked += 1
                    logger.info('[FlyingDamage] suppressed %s.%s', clsName, m)
                except Exception:
                    logger.info('[FlyingDamage] suppress fail %s.%s', clsName, m,
                                exc_info=True)

    logger.info('[FlyingDamage] suppression hooks installed: %d', hooked)


def _findDamageIndicatorClasses():
    """Scan loaded modules for classes named like a damage indicator."""
    found = []
    for modName, mod in list(sys.modules.items()):
        if mod is None:
            continue
        low = modName.lower()
        if 'damage_indicator' not in low and 'damageindicator' not in low:
            continue
        for attr in dir(mod):
            al = attr.lower()
            if 'damageindicator' in al or 'damage_indicator' in al:
                cls = getattr(mod, attr, None)
                if isinstance(cls, type):
                    found.append((modName, attr, cls))
    # Also log which damage_indicator modules exist, for visibility.
    mods = [m for m in sys.modules.keys()
            if 'damage_indicator' in m.lower() or 'damageindicator' in m.lower()]
    logger.info('[FlyingDamage] damage_indicator modules loaded: %s', mods)
    return found
