# -*- coding: utf-8 -*-
# suppress.py  --  Python 2.7
# Standard floating damage over tanks. In modern WoT/Lesta this is the
# "damage indicator" which can be toggled through the game settings the client
# reads. We disable it via the settings the DamageIndicatorPlugin consumes, and
# also try the vehicle-marker settings flag. Diagnostic logging included.

import sys
import logging

from .utils import override
from .settings.config import g_config

logger = logging.getLogger(__name__)


def installSuppression():
    if not g_config.hideStandard:
        logger.info('[FlyingDamage] suppression disabled')
        return

    _tryPluginByModuleScan()


def _tryPluginByModuleScan():
    """Find any battle plugin/component with a damage-icon method and hook it."""
    hooked = 0
    seenClasses = []

    for modName, mod in list(sys.modules.items()):
        if mod is None:
            continue
        low = modName.lower()
        # focus on battle marker / indicator plugin modules
        if 'markers2d' not in low and 'damage' not in low and 'indicator' not in low:
            continue
        for attr in dir(mod):
            cls = getattr(mod, attr, None)
            if not isinstance(cls, type):
                continue
            methods = dir(cls)
            for m in methods:
                ml = m.lower()
                # method that shows a damage icon/number
                if (('showdamage' in ml or 'adddamageicon' in ml or
                     'showdamageicon' in ml or '__showdamage' in ml or
                     'as_showdamage' in ml) and 'received' not in ml):
                    seenClasses.append('%s.%s.%s' % (modName, attr, m))
                    try:
                        def _suppressed(base, self, *a, **k):
                            if g_config.hideStandard:
                                return None
                            return base(self, *a, **k)
                        override(cls, m, _suppressed)
                        hooked += 1
                        logger.info('[FlyingDamage] suppressed %s.%s', attr, m)
                    except Exception:
                        logger.info('[FlyingDamage] suppress fail %s.%s', attr, m,
                                    exc_info=True)

    logger.info('[FlyingDamage] suppression: hooked=%d, matches=%s',
                hooked, seenClasses[:20])

    if hooked == 0:
        # Deep diagnostic: list every method containing 'damage' across battle
        # marker/indicator modules so we can pinpoint the exact draw call.
        _deepDump()


def _deepDump():
    dumped = 0
    for modName, mod in list(sys.modules.items()):
        if mod is None:
            continue
        low = modName.lower()
        if 'markers2d' not in low and 'battle' not in low:
            continue
        for attr in dir(mod):
            cls = getattr(mod, attr, None)
            if not isinstance(cls, type):
                continue
            dmg = [m for m in dir(cls) if 'damage' in m.lower()]
            if dmg:
                logger.info('[FlyingDamage] DUMP %s.%s damage-methods: %s',
                            modName.split('.')[-1], attr, dmg)
                dumped += 1
                if dumped > 30:
                    return
