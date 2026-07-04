# -*- coding: utf-8 -*-
# suppress.py  --  Python 2.7
# Suppresses the game's standard floating damage numbers above tanks so only
# our SWF numbers show. Hooks the markers2d damage plugin defensively:
# tries known class/method names and no-ops the damage-text output.

import logging

from .utils import override
from .settings.config import g_config

logger = logging.getLogger(__name__)

# Candidate (module, class, method) triples that draw standard floating damage.
# Different client versions expose slightly different names; we try each.
_CANDIDATES = [
    ('gui.Scaleform.daapi.view.battle.shared.markers2d.plugins',
     'DamageMarkersPlugin', '_DamageMarkersPlugin__showDamage'),
    ('gui.Scaleform.daapi.view.battle.shared.markers2d.plugins',
     'DamageMarkersPlugin', '_showDamage'),
    ('gui.Scaleform.daapi.view.battle.shared.markers2d.plugins',
     'DamageMarkersPlugin', 'showDamageIcon'),
    ('gui.Scaleform.daapi.view.battle.shared.markers2d.plugins',
     'DamageMarkersPlugin', '_addDamageMarkerToPool'),
]


def installSuppression():
    if not g_config.hideStandard:
        logger.info('[FlyingDamage] standard suppression disabled in settings')
        return

    hooked = 0
    for modName, clsName, methodName in _CANDIDATES:
        try:
            mod = __import__(modName, fromlist=[clsName])
            cls = getattr(mod, clsName, None)
            if cls is None:
                continue
            if not hasattr(cls, methodName):
                continue

            def _suppressed(base, self, *args, **kwargs):
                # Standard damage text suppressed; our SWF handles it.
                if g_config.hideStandard:
                    return None
                return base(self, *args, **kwargs)

            override(cls, methodName, _suppressed)
            hooked += 1
            logger.info('[FlyingDamage] suppressed standard damage: %s.%s',
                        clsName, methodName)
        except Exception:
            logger.info('[FlyingDamage] suppress candidate failed: %s.%s',
                        clsName, methodName, exc_info=True)

    if hooked == 0:
        logger.warning('[FlyingDamage] could NOT find standard damage plugin '
                       'to suppress (client layout differs). Listing plugins...')
        _dumpPluginMethods()


def _dumpPluginMethods():
    """Diagnostic: log the damage plugin's methods so we can find the right one."""
    try:
        mod = __import__(
            'gui.Scaleform.daapi.view.battle.shared.markers2d.plugins',
            fromlist=['DamageMarkersPlugin'])
        cls = getattr(mod, 'DamageMarkersPlugin', None)
        if cls is None:
            logger.warning('[FlyingDamage] DamageMarkersPlugin not present; '
                           'available: %s',
                           [n for n in dir(mod) if 'lugin' in n])
            return
        methods = [m for m in dir(cls) if not m.startswith('__')]
        logger.warning('[FlyingDamage] DamageMarkersPlugin methods: %s', methods)
    except Exception:
        logger.info('[FlyingDamage] dumpPluginMethods failed', exc_info=True)
