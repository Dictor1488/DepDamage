# -*- coding: utf-8 -*-
import cPickle
import functools
import json
import logging
import os
import time
import zlib
from collections import deque

import weakref

import BigWorld
import constants
from Account import PlayerAccount
from CurrentVehicle import g_currentVehicle
from PlayerEvents import g_playerEvents
from gui.Scaleform.framework import g_entitiesFactories, ScopeTemplates, ViewSettings
from gui.Scaleform.framework.entities.View import View
from gui.Scaleform.framework.managers.loaders import SFViewLoadParams
from gui.Scaleform.lobby_entry import getLobbyStateMachine
from gui.shared.personality import ServicesLocator
from frameworks.wulf import WindowLayer
try:
    from frameworks.wulf import IWindowsManager as _IWindowsManager
except ImportError:
    _IWindowsManager = None

try:
    from messenger.proto.events import g_messengerEvents
except ImportError:
    g_messengerEvents = None

try:
    from messenger.formatters.service_channel import SYS_MESSAGE_TYPE
except ImportError:
    SYS_MESSAGE_TYPE = None

try:
    from gui.shared import g_eventBus, EVENT_BUS_SCOPE
except ImportError:
    g_eventBus = None
    EVENT_BUS_SCOPE = None

try:
    from gui.shared.events import GUICommonEvent, GameEvent, AppLifeCycleEvent
except ImportError:
    GUICommonEvent = None
    GameEvent = None
    AppLifeCycleEvent = None

try:
    from gui.app_loader.settings import APP_NAME_SPACE
except ImportError:
    APP_NAME_SPACE = None

try:
    from gui import g_guiResetters
except ImportError:
    g_guiResetters = None

try:
    from gui.battle_control import g_sessionProvider
except ImportError:
    g_sessionProvider = None

try:
    from gui.battle_control.battle_constants import FEEDBACK_EVENT_ID
except ImportError:
    FEEDBACK_EVENT_ID = None

try:
    from skeletons.gui.battle_session import IBattleSessionProvider
except ImportError:
    IBattleSessionProvider = None

try:
    from account_helpers import getAccountDatabaseID
except ImportError:
    getAccountDatabaseID = None

try:
    from items import vehicles as _vehiclesModule
except ImportError:
    _vehiclesModule = None

try:
    from helpers import dependency
except ImportError:
    dependency = None

try:
    from Vehicle import Vehicle as _VehicleClass
except ImportError:
    _VehicleClass = None

_DEBUG = os.path.isfile('.debug_mods')
logger = logging.getLogger('under_pressure.mastery')
logger.setLevel(logging.DEBUG if _DEBUG else logging.ERROR)

__version__ = '0.1.0'

_LINKAGE_HANGAR = 'MasteryPanelHangar'
_LINKAGE_BATTLE = 'MasteryPanelBattle'
_LINKAGE_RESULTS = 'MasteryPanelResults'
_SWF_HANGAR = 'MasteryPanelHangar.swf'
_SWF_BATTLE = 'MasteryPanelBattle.swf'
_SWF_RESULTS = 'MasteryPanelResults.swf'

_L10N_DIR = 'mods/under_pressure.mastery'
_L10N_FALLBACK = 'en'
_l10n = {}

_API_APP_ID = 'bce57ac20af6b67b08be09fd66847ed9'
_API_URL_TEMPLATE = (
    'https://api.worldoftanks.%s/wot/tanks/mastery/'
    '?application_id=' + _API_APP_ID +
    '&distribution=%s&percentile=%s&tank_id=%s'
)
_XP_PERCENTILES_QUERY = u'50%2C80%2C95%2C99'
_MOE_PERCENTILES_QUERY = u'20%2C40%2C55%2C65%2C75%2C85%2C95%2C100'
_PERCENTILE_TO_KEY = (
    (u'50', 'thirdClass'),
    (u'80', 'secondClass'),
    (u'95', 'firstClass'),
    (u'99', 'aceTanker'),
)
_MOE_PERCENTILE_TO_KEY = (
    (u'20',  'p20'),
    (u'40',  'p40'),
    (u'55',  'p55'),
    (u'65',  'p65'),
    (u'75',  'p75'),
    (u'85',  'p85'),
    (u'95',  'p95'),
    (u'100', 'p100'),
)
_MOE_REQUIREMENT_KEYS = (
    (20.0, 'p20'),
    (40.0, 'p40'),
    (55.0, 'p55'),
    (65.0, 'p65'),
    (75.0, 'p75'),
    (85.0, 'p85'),
    (95.0, 'p95'),
    (100.0, 'p100'),
)

_INJECT_RETRY_DELAY = 0.5
_INJECT_MAX_ATTEMPTS = 30
_API_TIMEOUT = 5.0
_API_MAX_ATTEMPTS = 3
_API_RETRY_BASE_DELAY = 2.0
_MAX_HISTORY = 200
_MIN_TANK_LEVEL = 5
_DEFAULT_VIEW_MODE = 0
_MOE_CALC_KOEFF = 2.0 / 101.0

_STRONGHOLD_WEB_MARKERS    = ('wgsh-', 'wgsh.', 'wgsh_', 'battlerooms')
_STRONGHOLD_MODE_MARKERS   = ('stronghold', 'sortie', 'fort', 'advance')
_STRONGHOLD_PRB_TYPE_NAMES = ('SORTIE', 'FORT_BATTLE', 'SORTIE_2', 'FORT_BATTLE_2')
_STRONGHOLD_BROWSER_UNKNOWN_ID = '__unknown__'
_GARAGE_ALLOWED_QUEUE_MODES    = (None, 'random', 'mapbox')

try:
    _prefsFilePath = BigWorld.wg_getPreferencesFilePath()
except AttributeError:
    _prefsFilePath = BigWorld.getPreferencesFilePath()

_CACHE_DIR = os.path.normpath(os.path.join(os.path.dirname(_prefsFilePath), 'mods', 'mastery'))
_CACHE_FILE = os.path.join(_CACHE_DIR, 'cache.dat')
_CONFIG_DIR = os.path.normpath(os.path.join(os.getcwd(), 'mods', 'configs', 'mastery'))
_CONFIG_FILE = os.path.join(_CONFIG_DIR, 'mastery.json')
_CACHE_VERSION = 10
_CACHE_TTL_SECONDS = 3 * 24 * 3600
_CACHE_SAVE_DEBOUNCE = 3.0
_CONFIG_DEFAULTS = {
    'mode': 'both',
    'modes': {
        'both': 'masters and mark badge',
        'mastery': 'masters only, mark badge off',
        'marks': 'mark badge only, masters off',
    },
    'badgeStyle': 'classic',
    'badgeStyles': {
        'classic': 'stars and value centered (original)',
        'compact': 'stars and bars on the left (screenshot layout)',
        'html': 'wide HTML-style gunmark badge',
    },
}
_CONFIG_MODES = {
    'both': 0,
    'mastery': 1,
    'masters': 1,
    'marks': 2,
    'mark': 2,
}
_CONFIG_BADGE_STYLES = {
    'classic': 0,
    'original': 0,
    'old': 0,
    'compact': 1,
    'new': 1,
    'left': 1,
    'html': 2,
    'wide': 2,
    'v3': 2,
    'third': 2,
}


def _cancelCallbackSafe(cbid):
    try:
        if cbid is not None:
            BigWorld.cancelCallback(cbid)
    except (AttributeError, ValueError):
        pass


def _isReplayPlaying():
    """True, СЏРєС‰Рѕ Р·Р°СЂР°Р· РІС–РґС‚РІРѕСЂСЋС”С‚СЊСЃСЏ СЂРµРїР»РµР№ вЂ” С‚РѕРґС– РјС–С‚РєСѓ РЅРµ РїРѕРєР°Р·СѓС”РјРѕ."""
    try:
        from BattleReplay import g_replayCtrl
        if g_replayCtrl is None:
            return False
        # isPlaying вЂ” СЃР°РјРµ РїСЂРѕРіСЂР°РІР°РЅРЅСЏ Р·Р°РїРёСЃР°РЅРѕРіРѕ Р±РѕСЋ
        if getattr(g_replayCtrl, 'isPlaying', False):
            return True
        # РґРµСЏРєС– РІРµСЂСЃС–С—: isReplayPlaying / replayFinished
        if getattr(g_replayCtrl, 'isReplayPlaying', False):
            return True
        return False
    except Exception:
        return False


def _safeLower(value):
    if value is None:
        return ''
    try:
        return unicode(value).lower()
    except Exception:
        try:
            return str(value).lower()
        except Exception:
            return ''


def _weakCallback(obj, methodName):
    ref = weakref.ref(obj)
    def _cb(*args, **kwargs):
        inst = ref()
        if inst is not None:
            getattr(inst, methodName)(*args, **kwargs)
    return _cb


def _browserKey(value):
    if value is None:
        return None
    try:
        hash(value)
        return value
    except Exception:
        return unicode(value)


def _ensureDir(path):
    if not os.path.isdir(path):
        try:
            os.makedirs(path)
        except OSError:
            pass


def _ensureCacheDir():
    _ensureDir(_CACHE_DIR)


def _ensureConfigDir():
    _ensureDir(_CONFIG_DIR)


def _loadConfigFile():
    _ensureConfigDir()
    loaded = {}
    changed = False
    if os.path.isfile(_CONFIG_FILE):
        try:
            with open(_CONFIG_FILE, 'rb') as fh:
                loaded = json.load(fh)
            if not isinstance(loaded, dict):
                loaded = {}
                changed = True
        except Exception:
            logger.exception('config: failed to load, using defaults')
            changed = True
    else:
        changed = True

    mode = _safeLower(loaded.get('mode'))
    if mode not in _CONFIG_MODES:
        mode = _CONFIG_DEFAULTS['mode']
        changed = True
    badgeStyle = _safeLower(loaded.get('badgeStyle'))
    if badgeStyle not in _CONFIG_BADGE_STYLES:
        badgeStyle = _CONFIG_DEFAULTS['badgeStyle']
        changed = True
    config = dict(_CONFIG_DEFAULTS)
    config['mode'] = mode
    config['badgeStyle'] = badgeStyle
    if loaded != config:
        changed = True

    if changed:
        try:
            with open(_CONFIG_FILE, 'wb') as fh:
                json.dump(config, fh, indent=4, sort_keys=True)
        except Exception:
            logger.exception('config: failed to write defaults')
    return config


def _isCloseBrowserMethod(methodName):
    text = _safeLower(methodName)
    return ('delete' in text or 'destroy' in text or 'close' in text or
            text.startswith('del') or text.endswith('delbrowser'))


def _isStrongholdGarageUrl(url):
    text = _safeLower(url)
    if not text:
        return False
    if any(marker in text for marker in _STRONGHOLD_WEB_MARKERS[:3]):
        return True
    return _STRONGHOLD_WEB_MARKERS[3] in text and any(marker in text for marker in _STRONGHOLD_MODE_MARKERS)


def _loadLocalization():
    global _l10n
    try:
        from helpers import getClientLanguage
        lang = getClientLanguage() or _L10N_FALLBACK
    except Exception:
        lang = _L10N_FALLBACK
    for tryLang in (lang, _L10N_FALLBACK):
        path = _L10N_DIR + '/' + tryLang + '.json'
        try:
            import ResMgr
            section = ResMgr.openSection(path)
            if section is not None:
                _l10n = json.loads(section.asBinary)
                logger.debug('l10n loaded: %s (%d keys)', tryLang, len(_l10n))
                return
        except Exception:
            logger.exception('l10n failed for %s', tryLang)
    logger.debug('l10n: no file found, using defaults')


def _tr(key, default=u''):
    return _l10n.get(key, default)


def _getDefaultHangarStateCls():
    try:
        from gui.impl.lobby.hangar.states import DefaultHangarState
        return DefaultHangarState
    except Exception:
        logger.exception('DefaultHangarState import failed')
        return None


def _getApiDomain():
    realm = unicode(getattr(constants, 'AUTH_REALM', u'EU')).upper()
    if 'NA' in realm:
        return 'com'
    if 'ASIA' in realm:
        return 'asia'
    return 'eu'


def _buildApiUrl(tankID, distribution, percentilesQuery):
    return _API_URL_TEMPLATE % (_getApiDomain(), distribution, percentilesQuery, tankID)


def _findTankRecord(container, tankID):
    if not isinstance(container, dict):
        return None
    for key in (tankID, str(tankID), unicode(tankID)):
        if key in container:
            return container.get(key)
    return None


def _extractPercentile(source, percentile):
    for key in (percentile, str(percentile)):
        if key in source:
            try:
                return int(source.get(key))
            except (TypeError, ValueError):
                return None
    return None


def _parseApiResponse(payload, tankID, mapping):
    if not isinstance(payload, dict):
        return None
    data = payload.get('data')
    if not isinstance(data, dict):
        return None
    distribution = data.get('distribution')
    if not isinstance(distribution, dict):
        distribution = data
    record = _findTankRecord(distribution, tankID)
    if not isinstance(record, dict):
        return None
    result = {}
    for percentile, key in mapping:
        result[key] = _extractPercentile(record, percentile)
    if all(v is None for v in result.itervalues()):
        return None
    return result


def _safeFloat(value):
    try:
        return float(value)
    except Exception:
        return None


def _tankKey(tankID):
    if tankID is None:
        return None
    try:
        return int(tankID)
    except (TypeError, ValueError):
        return tankID


def _dictGetTank(container, tankID, default=None):
    if not isinstance(container, dict):
        return default
    key = _tankKey(tankID)
    for candidate in (key, tankID, str(key), unicode(key)):
        try:
            if candidate in container:
                return container.get(candidate)
        except Exception:
            pass
    return default


def _dictPopTank(container, tankID, default=None):
    if not isinstance(container, dict):
        return default
    key = _tankKey(tankID)
    for candidate in (key, tankID, str(key), unicode(key)):
        try:
            if candidate in container:
                return container.pop(candidate)
        except Exception:
            pass
    return default


def _getVehicleDossier(tankID):
    if tankID is None:
        return None
    try:
        return ServicesLocator.itemsCache.items.getVehicleDossier(int(tankID))
    except Exception:
        return None
    return None


def _readMarkFromDossier(dossier, debug_tankID=None):
    if dossier is None:
        return None

    try:
        raw = dossier.getRecordValue('achievements', 'damageRating')
        if raw is not None:
            number = _safeFloat(raw)
            if number is not None and number >= 0.0:
                result = number / 100.0
                if 0.0 <= result <= 100.0:
                    logger.debug('mark: getRecordValue achievements.damageRating=%.2f', result)
                    return round(result, 2)
    except Exception:
        pass

    try:
        achievs = dossier.getAchievements()
        raw = getattr(achievs, 'damageRating', None)
        if raw is not None:
            number = _safeFloat(raw)
            if number is not None and number >= 0.0:
                result = number / 100.0
                if 0.0 <= result <= 100.0:
                    return round(result, 2)
    except Exception:
        pass

    return None


def _readBattlesCountFromDossier(dossier):
    if dossier is None:
        return 0
    for section in ('a15x15', 'a15x15_2', 'total', 'random'):
        try:
            val = dossier.getRecordValue(section, 'battlesCount')
            if val:
                return int(val)
        except Exception:
            pass
    try:
        rs = dossier.getRandomStats()
        if rs is not None:
            cnt = rs.getBattlesCount()
            if cnt is not None:
                return int(cnt)
    except Exception:
        pass
    return 0


def _readGunMarksFromDossier(dossier):
    if dossier is None:
        return -1
    try:
        raw = dossier.getRecordValue('achievements', 'marksOnGun')
        if raw is not None:
            value = int(raw)
            if 0 <= value <= 3:
                return value
    except Exception:
        pass
    try:
        achievs = dossier.getAchievements()
        raw = getattr(achievs, 'marksOnGun', None)
        if raw is not None:
            value = int(raw)
            if 0 <= value <= 3:
                return value
    except Exception:
        pass
    return -1


def _readGunMarksForTank(tankID):
    if tankID is None:
        return -1
    dossier = _getVehicleDossier(tankID)
    if dossier is not None:
        marks = _readGunMarksFromDossier(dossier)
        if marks >= 0:
            return marks
    return -1


def _readBattlesCountForTank(tankID):
    if tankID is None:
        return 0
    dossier = _getVehicleDossier(tankID)
    if dossier is not None:
        return _readBattlesCountFromDossier(dossier)
    return 0


def _readMarkAverageDamageFromDossier(dossier):
    if dossier is None:
        return 0
    try:
        val = dossier.getRecordValue('achievements', 'movingAvgDamage')
        if val is not None:
            found = _safeFloat(val)
            if found is not None and found > 0:
                logger.debug('mark-average: getRecordValue achievements.movingAvgDamage=%s', found)
                return int(round(found))
    except Exception:
        pass
    try:
        rs = dossier.getRandomStats()
        if rs is not None:
            found = _safeFloat(rs.getAvgDamage())
            if found is not None and found > 0:
                return int(round(found))
    except Exception:
        pass
    try:
        rs = dossier.getRandomStats()
        damage = _safeFloat(rs.getDamageDealt())
        battles = _safeFloat(rs.getBattlesCount())
        if damage is not None and battles is not None and battles > 0:
            return int(round(damage / battles))
    except Exception:
        pass
    return 0


def _readMarkAverageDamageForTank(tankID):
    if tankID is None:
        return 0
    dossier = _getVehicleDossier(tankID)
    if dossier is not None:
        value = _readMarkAverageDamageFromDossier(dossier)
        if value > 0:
            return value
    return 0


def _estimateMarkAverageDamage(mark, moe):
    if mark is None or not isinstance(moe, dict):
        return 0
    try:
        mark = float(mark)
    except (TypeError, ValueError):
        return 0
    points = [(pct, _safeFloat(moe.get(key))) for pct, key in _MOE_REQUIREMENT_KEYS]
    prevPct = 0.0
    prevValue = 0.0
    for pct, value in points:
        if value is None or value <= 0:
            continue
        if mark <= pct:
            span = pct - prevPct
            if span <= 0:
                return int(round(value))
            t = max(0.0, min(1.0, (mark - prevPct) / span))
            return int(round(prevValue + (value - prevValue) * t))
        prevPct = pct
        prevValue = value
    return int(round(prevValue))


def _getMoeRequirementPoints(moe):
    if not isinstance(moe, dict):
        return []
    points = []
    for pct, key in _MOE_REQUIREMENT_KEYS:
        value = _safeFloat(moe.get(key))
        if value is not None and value > 0:
            points.append((pct, value))
    return points


def _hasFullMoeRequirements(moe):
    if not isinstance(moe, dict):
        return False
    for _pct, key in _MOE_REQUIREMENT_KEYS:
        value = _safeFloat(moe.get(key))
        if value is None or value <= 0:
            return False
    return True


def _lerpPercentByDamage(value, fromDamage, toDamage, fromPercent, toPercent):
    damageSpan = float(toDamage) - float(fromDamage)
    if damageSpan <= 0.0:
        return float(fromPercent)
    progress = (float(value) - float(fromDamage)) / damageSpan
    return float(fromPercent) + (float(toPercent) - float(fromPercent)) * progress


def _estimateDamageRatingFromRequirements(movingAvgDamage, moe):
    if movingAvgDamage is None:
        return None
    points = _getMoeRequirementPoints(moe)
    if not points:
        return None
    try:
        movingAvgDamage = float(movingAvgDamage)
    except (TypeError, ValueError):
        return None
    firstPercent, firstDamage = points[0]
    if movingAvgDamage <= firstDamage:
        if firstDamage <= 0:
            return 0.0
        return max(0.0, min(firstPercent, firstPercent * movingAvgDamage / float(firstDamage)))
    for idx in xrange(1, len(points)):
        fromPercent, fromDamage = points[idx - 1]
        toPercent, toDamage = points[idx]
        if movingAvgDamage <= toDamage:
            return max(0.0, min(100.0, _lerpPercentByDamage(
                movingAvgDamage, fromDamage, toDamage, fromPercent, toPercent)))
    if len(points) == 1:
        return min(100.0, firstPercent)
    fromPercent, fromDamage = points[-2]
    toPercent, toDamage = points[-1]
    if toDamage <= fromDamage:
        return min(100.0, toPercent)
    return max(0.0, min(100.0, _lerpPercentByDamage(
        movingAvgDamage, fromDamage, toDamage, fromPercent, toPercent)))


def _estimateProjectedMark(baseAvgDamage, combinedDamage, moe, fallbackMark):
    try:
        baseAvgDamage = float(baseAvgDamage)
        combinedDamage = max(0.0, float(combinedDamage))
    except (TypeError, ValueError):
        return fallbackMark, 0
    if baseAvgDamage <= 0:
        return fallbackMark, 0
    projectedAvg = (baseAvgDamage * (1.0 - _MOE_CALC_KOEFF)
                    + combinedDamage * _MOE_CALC_KOEFF)
    projectedMark = _estimateDamageRatingFromRequirements(projectedAvg, moe)
    if projectedMark is None:
        projectedMark = fallbackMark
    return projectedMark, int(round(projectedAvg))


def _readMarkForTankID(tankID):
    if tankID is None:
        return None
    dossier = _getVehicleDossier(tankID)
    if dossier is not None:
        mark = _readMarkFromDossier(dossier, debug_tankID=tankID)
        if mark is not None:
            return mark
    return None


def _getTankLevelByCD(compactDescr):
    if _vehiclesModule is None or compactDescr is None:
        return 0
    try:
        _, nationID, innationID = _vehiclesModule.parseIntCompactDescr(int(compactDescr))
        return int(_vehiclesModule.g_cache.vehicle(nationID, innationID).level)
    except Exception:
        return 0


_NATION_TAGS = {
    'ussr':    u'SU',
    'germany': u'DE',
    'usa':     u'US',
    'china':   u'CN',
    'france':  u'FR',
    'uk':      u'UK',
    'japan':   u'JP',
    'czech':   u'CZ',
    'sweden':  u'SE',
    'poland':  u'PL',
    'italy':   u'IT',
}


def _getNationFlag(vehicleItem):
    if vehicleItem is None:
        return u''
    nationName = None
    try:
        nationName = getattr(vehicleItem, 'nationName', None)
    except Exception:
        nationName = None
    if not nationName and _vehiclesModule is not None:
        try:
            intCD = getattr(vehicleItem, 'intCD', None)
            if intCD is not None:
                _, nationID, _i = _vehiclesModule.parseIntCompactDescr(int(intCD))
                names = getattr(_vehiclesModule, 'nations', None)
                if names is None:
                    try:
                        import nations as _nations
                        names = _nations.NAMES
                    except Exception:
                        names = None
                if names and 0 <= nationID < len(names):
                    nationName = names[nationID]
        except Exception:
            nationName = None
    if not nationName:
        return u''
    return _NATION_TAGS.get(unicode(nationName).lower(), u'')


def _extractMapName(common):
    if not isinstance(common, dict):
        return u''
    arenaTypeID = common.get('arenaTypeID')
    if not arenaTypeID:
        return u''
    try:
        from gui.battle_control.arena_info.arena_vos import getArenaTypeName
        name = getArenaTypeName(arenaTypeID)
        if name:
            return unicode(name)
    except Exception:
        pass
    try:
        from ArenaType import g_cache as arenaCache
        arenaType = arenaCache.get(arenaTypeID)
        if arenaType is not None:
            raw = getattr(arenaType, 'name', None) or getattr(arenaType, 'geometryName', None)
            if raw:
                try:
                    from helpers import i18n
                    return unicode(i18n.makeString(raw))
                except Exception:
                    return unicode(raw)
    except Exception:
        pass
    return u''


_DIRECT_DAMAGE_KEYS = (
    'damageDealt', 'damage', 'damageDone', 'piercingDamage',
    'damageRamming', 'rammingDamage',
)
_FEEDBACK_AMOUNT_KEYS = (
    '_PlayerFeedbackEvent__count', '__count', 'count',
    '_DamageExtra__damage', '__damage', 'damage',
)
_ASSIST_SPOT_KEYS = (
    'damageAssistedRadio', 'damageAssistedSpot', 'damageAssistedByRadio',
    'damageAssistedSelf', 'damageAssisted',
    'damageAssistedRadioWhileInvisible', 'damageAssistedRadioWhileVisible',
    'radioAssist', 'radioAssistDamage', 'damageAssistedBySpotting',
    '_BattleSummaryFeedbackEvent__radioAssistDamage',
)
_ASSIST_TRACK_KEYS = (
    'damageAssistedTrack', 'damageAssistedByTrack', 'damageAssistedByTrackAndStun',
    'damageAssistedTracks', 'damageAssistedImmobilized',
    'trackAssist', 'trackAssistDamage', 'damageAssistedByTracking',
    '_BattleSummaryFeedbackEvent__trackAssistDamage',
)
_ASSIST_STUN_KEYS = (
    'damageAssistedStun', 'damageAssistedByStun', 'stunAssist',
    'stunAssistDamage', '_BattleSummaryFeedbackEvent__stunAssist',
)


def _readIntByKeys(source, keys):
    if not isinstance(source, dict):
        return 0
    for key in keys:
        try:
            value = int(source.get(key, 0) or 0)
            if value > 0:
                return value
        except (TypeError, ValueError):
            pass
    return 0


def _readMaxIntByKeysRecursive(source, keys, depth=0):
    if source is None or depth > 6:
        return 0
    best = 0
    try:
        if isinstance(source, dict):
            direct = _readIntByKeys(source, keys)
            if direct > best:
                best = direct
            for nested in source.itervalues():
                found = _readMaxIntByKeysRecursive(nested, keys, depth + 1)
                if found > best:
                    best = found
        elif isinstance(source, (list, tuple)):
            for nested in source:
                found = _readMaxIntByKeysRecursive(nested, keys, depth + 1)
                if found > best:
                    best = found
    except Exception:
        pass
    return best


def _hasKeyRecursive(source, keys, depth=0):
    if source is None or depth > 6:
        return False
    try:
        if isinstance(source, dict):
            for key in source.iterkeys():
                if key in keys:
                    return True
            for nested in source.itervalues():
                if _hasKeyRecursive(nested, keys, depth + 1):
                    return True
        elif isinstance(source, (list, tuple)):
            for nested in source:
                if _hasKeyRecursive(nested, keys, depth + 1):
                    return True
        else:
            raw = getattr(source, '__dict__', None)
            if isinstance(raw, dict):
                return _hasKeyRecursive(raw, keys, depth + 1)
    except Exception:
        pass
    return False


def _feedbackPayloads(source, depth=0):
    if source is None or depth > 4:
        return []
    payloads = [source]
    try:
        if isinstance(source, dict):
            for value in source.itervalues():
                payloads.extend(_feedbackPayloads(value, depth + 1))
        elif isinstance(source, (list, tuple, set)):
            for value in source:
                payloads.extend(_feedbackPayloads(value, depth + 1))
        else:
            for method in ('getExtra', 'getData', 'getDetails'):
                func = getattr(source, method, None)
                if callable(func):
                    try:
                        payloads.extend(_feedbackPayloads(func(), depth + 1))
                    except Exception:
                        pass
            raw = getattr(source, '__dict__', None)
            if isinstance(raw, dict):
                payloads.extend(_feedbackPayloads(raw, depth + 1))
    except Exception:
        pass
    return payloads


def _feedbackText(source):
    chunks = []
    try:
        chunks.append(source.__class__.__name__)
    except Exception:
        pass
    for attr in ('eventType', 'type', 'name', 'feedbackType'):
        try:
            chunks.append(unicode(getattr(source, attr)))
        except Exception:
            pass
    for method in ('getType', 'getName', 'getEventType', 'getBattleEventType'):
        func = getattr(source, method, None)
        if callable(func):
            try:
                chunks.append(unicode(func()))
            except Exception:
                pass
    return _safeLower(u' '.join(chunks))


def _iterFlatValues(source, depth=0):
    if source is None or depth > 5:
        return []
    values = [source]
    try:
        if isinstance(source, dict):
            for key, value in source.iteritems():
                values.extend(_iterFlatValues(key, depth + 1))
                values.extend(_iterFlatValues(value, depth + 1))
        elif isinstance(source, (list, tuple, set)):
            for value in source:
                values.extend(_iterFlatValues(value, depth + 1))
        else:
            raw = getattr(source, '__dict__', None)
            if isinstance(raw, dict):
                values.extend(_iterFlatValues(raw, depth + 1))
    except Exception:
        pass
    return values


def _feedbackEventNamesFromValue(value):
    names = []
    if FEEDBACK_EVENT_ID is None:
        return names
    try:
        valueInt = int(value)
    except (TypeError, ValueError):
        return names
    try:
        for name in dir(FEEDBACK_EVENT_ID):
            if name.startswith('_'):
                continue
            try:
                if int(getattr(FEEDBACK_EVENT_ID, name)) == valueInt:
                    names.append(name)
            except Exception:
                pass
    except Exception:
        pass
    return names


def _looksAssistFeedback(source):
    text = _feedbackText(source)
    if ('assist' in text or 'spot' in text or 'radio' in text or
            'track' in text or 'stun' in text or 'immobil' in text):
        return True
    if (_hasKeyRecursive(source, _ASSIST_SPOT_KEYS) or
            _hasKeyRecursive(source, _ASSIST_TRACK_KEYS) or
            _hasKeyRecursive(source, _ASSIST_STUN_KEYS)):
        return True
    for value in _iterFlatValues(source):
        for name in _feedbackEventNamesFromValue(value):
            lname = _safeLower(name)
            if ('assist' in lname or 'spot' in lname or 'radio' in lname or
                    'track' in lname or 'stun' in lname or 'immobil' in lname):
                return True
    return False


def _assistKindFromFeedback(source):
    text = _feedbackText(source)
    if 'track' in text or 'immobil' in text:
        return 'track'
    if 'stun' in text:
        return 'stun'
    if 'spot' in text or 'radio' in text:
        return 'spot'
    if _hasKeyRecursive(source, _ASSIST_TRACK_KEYS):
        return 'track'
    if _hasKeyRecursive(source, _ASSIST_STUN_KEYS):
        return 'stun'
    if _hasKeyRecursive(source, _ASSIST_SPOT_KEYS):
        return 'spot'
    for value in _iterFlatValues(source):
        for name in _feedbackEventNamesFromValue(value):
            lname = _safeLower(name)
            if 'track' in lname or 'immobil' in lname:
                return 'track'
            if 'stun' in lname:
                return 'stun'
            if 'spot' in lname or 'radio' in lname:
                return 'spot'
    return 'spot'


def _numericFeedbackAmount(source):
    best = 0
    for value in _iterFlatValues(source):
        try:
            number = int(value)
        except (TypeError, ValueError):
            continue
        if number <= 0:
            continue
        if _feedbackEventNamesFromValue(number):
            continue
        if number > best:
            best = number
    return best


def _feedbackAmount(source):
    amount = _readMaxIntByKeysRecursive(source, _FEEDBACK_AMOUNT_KEYS)
    for method in ('getCount', 'getDamage', 'getValue'):
        amount = max(amount, _callIntMethod(source, method))
    for payload in _feedbackPayloads(source):
        for method in ('getExtra', 'getData', 'getDetails'):
            func = getattr(payload, method, None)
            if callable(func):
                try:
                    amount = max(amount, _readMaxIntByKeysRecursive(func(), _FEEDBACK_AMOUNT_KEYS))
                except Exception:
                    pass
    if amount <= 0 or amount > 30000:
        return 0
    return int(amount)


def _callIntMethod(source, methodName):
    try:
        func = getattr(source, methodName, None)
        if callable(func):
            value = int(func() or 0)
            if value > 0:
                return value
    except Exception:
        pass
    return 0


def _readFeedbackSummary(source):
    direct = _callIntMethod(source, 'getTotalDamage')
    assist = _callIntMethod(source, 'getTotalAssistDamage')
    blocked = _callIntMethod(source, 'getTotalBlockedDamage')
    stun = _callIntMethod(source, 'getTotalStunDamage')
    if not any((direct, assist, blocked, stun)):
        return None
    # WoT getTotalDamage() РЅРµ РІРєР»СЋС‡Р°С” СЂР°РјС–РЅРі вЂ” С‡РёС‚Р°С”РјРѕ РѕРєСЂРµРјРѕ С– РґРѕРґР°С”РјРѕ
    ramming = _readMaxIntByKeysRecursive(source, ('damageRamming', 'rammingDamage'))
    return {
        'direct': direct + ramming,
        'spot': assist,
        'track': _readMaxIntByKeysRecursive(source, _ASSIST_TRACK_KEYS),
        'stun': max(stun, _readMaxIntByKeysRecursive(source, _ASSIST_STUN_KEYS)),
    }


def _extractMarkDamage(source):
    direct = _readMaxIntByKeysRecursive(source, _DIRECT_DAMAGE_KEYS)
    spot   = _readMaxIntByKeysRecursive(source, _ASSIST_SPOT_KEYS)
    track  = _readMaxIntByKeysRecursive(source, _ASSIST_TRACK_KEYS)
    stun   = _readMaxIntByKeysRecursive(source, _ASSIST_STUN_KEYS)
    assist = int(max(spot, track, stun))
    # WoT С„РѕСЂРјСѓР»Р° РґР»СЏ РјС–С‚РєРё: direct Р·Р°РІР¶РґРё + РЅР°Р№Р±С–Р»СЊС€РёР№ Р· С‚РёРїС–РІ Р°СЃРёСЃС‚Сѓ
    return int(direct + assist)


def _getActiveAccountDBID():
    if getAccountDatabaseID is not None:
        try:
            dbid = int(getAccountDatabaseID() or 0)
            if dbid:
                return dbid
        except Exception:
            pass
    try:
        player = BigWorld.player()
        dbid = int(getattr(player, 'databaseID', 0) or 0)
        if dbid:
            return dbid
    except Exception:
        pass
    return 0


class MasterySessionHistory(object):

    def __init__(self):
        self._preBattleSnapshot = {}

    def snapshotBeforeBattle(self, tankID, mark, mapName=None,
                             movingAvgDamage=None, marksOnGun=None):
        if tankID is None or mark is None:
            return
        try:
            markValue = float(mark)
        except (TypeError, ValueError):
            return
        snapshot = {
            'mark': markValue,
            'map': unicode(mapName) if mapName else u'',
        }
        if movingAvgDamage is not None:
            try:
                snapshot['movingAvgDamage'] = float(movingAvgDamage)
            except (TypeError, ValueError):
                pass
        if marksOnGun is not None:
            try:
                snapshot['marksOnGun'] = int(marksOnGun)
            except (TypeError, ValueError):
                pass
        self._preBattleSnapshot[int(tankID)] = snapshot
        logger.debug('session: snapshot tankID=%s mark=%.2f map=%s',
                     tankID, markValue, mapName)

    def overrideMapName(self, tankID, mapName):
        if tankID is None or not mapName:
            return
        snap = self._preBattleSnapshot.get(int(tankID))
        if snap is not None:
            snap['map'] = unicode(mapName)

    def consumeSnapshot(self, tankID):
        if tankID is None:
            return None
        return self._preBattleSnapshot.pop(int(tankID), None)

    def peekSnapshot(self, tankID):
        if tankID is None:
            return None
        try:
            return self._preBattleSnapshot.get(int(tankID))
        except (TypeError, ValueError):
            return None

    def reset(self):
        self._preBattleSnapshot.clear()


class MasteryPanelInjectorView(View):
    _g_controller = None
    _viewKind = 'hangar'

    def _populate(self):
        super(MasteryPanelInjectorView, self)._populate()
        if MasteryPanelInjectorView._g_controller:
            MasteryPanelInjectorView._g_controller._onInjectorReady(self)

    def _dispose(self):
        if MasteryPanelInjectorView._g_controller:
            MasteryPanelInjectorView._g_controller._onInjectorDisposed(self)
        super(MasteryPanelInjectorView, self)._dispose()

    def py_onDragEnd(self, offset):
        if MasteryPanelInjectorView._g_controller:
            MasteryPanelInjectorView._g_controller._onDragEnd(offset)

    def py_onPanelReady(self):
        if MasteryPanelInjectorView._g_controller:
            MasteryPanelInjectorView._g_controller._onPanelReady(self)

    def py_onViewModeChanged(self, mode):
        if MasteryPanelInjectorView._g_controller:
            MasteryPanelInjectorView._g_controller._onViewModeChanged(mode)

    def py_onExpandToggle(self):
        if MasteryPanelInjectorView._g_controller:
            MasteryPanelInjectorView._g_controller._onExpandToggle()

    def py_onMarkBadgeToggle(self, value):
        if MasteryPanelInjectorView._g_controller:
            MasteryPanelInjectorView._g_controller._onMarkBadgeToggle(value)

    def py_onMarkBadgeOffsetChanged(self, offset):
        if MasteryPanelInjectorView._g_controller:
            MasteryPanelInjectorView._g_controller._onMarkBadgeOffsetChanged(offset)

    def py_onBattleBadgeOffsetChanged(self, offset):
        if MasteryPanelInjectorView._g_controller:
            MasteryPanelInjectorView._g_controller._onBattleBadgeOffsetChanged(offset)


class MasteryPanelHangarView(MasteryPanelInjectorView):
    _viewKind = 'hangar'


class MasteryPanelBattleView(MasteryPanelInjectorView):
    _viewKind = 'battle'


class MasteryPanelResultsView(MasteryPanelInjectorView):
    _viewKind = 'results'


def _registerFlash():
    for linkage, viewCls, swf in (
            (_LINKAGE_HANGAR,  MasteryPanelHangarView,  _SWF_HANGAR),
            (_LINKAGE_BATTLE,  MasteryPanelBattleView,  _SWF_BATTLE),
            (_LINKAGE_RESULTS, MasteryPanelResultsView, _SWF_RESULTS)):
        g_entitiesFactories.addSettings(ViewSettings(
            linkage, viewCls, swf,
            WindowLayer.WINDOW, None, ScopeTemplates.GLOBAL_SCOPE
        ))


def _unregisterFlash():
    for linkage in (_LINKAGE_HANGAR, _LINKAGE_BATTLE, _LINKAGE_RESULTS):
        try:
            g_entitiesFactories.removeSettings(linkage)
        except Exception:
            pass


class MasteryController(object):

    def __init__(self, session=None):
        self._session       = session
        self._injectorView  = None
        self._panelReady    = False
        self._injectPending = False
        self._battleInjectorView = None
        self._battlePanelReady   = False
        self._resultInjectorView = None
        self._resultPanelReady   = False
        self._enabled       = False
        self._hangarVisible = False
        self._visibleByData = False
        self._scaleBound    = False
        self._guiResettersBound = False
        self._refreshCallbackId = None
        self._garageVehicleRetryAttempt = 0
        self._position      = [100, 100]
        self._viewMode      = _DEFAULT_VIEW_MODE
        self._xpCache       = {}
        self._moeCache      = {}
        self._xpCacheTs     = {}
        self._moeCacheTs    = {}
        self._pendingXp     = set()
        self._pendingMoe    = set()
        self._markHistory   = {}
        self._lastKnownMark = {}
        self._lastKnownMarkStats = {}
        self._currentAccountDBID = 0
        self._saveRev       = 0
        self._saveCallbackId = None
        self._markRetryCallbackId = None
        self._detailOpen    = False
        self._markBadgeOpen = True
        self._markBadgeOffset = [-1, -1]
        self._battleBadgeOffset = [-1, -1]
        self._pendingBaseline = {}
        self._modsSettingsOpen     = False
        self._queueModeAllowed     = True
        self._strongholdScreenOpen = False
        self._strongholdBrowserIDs = set()
        self._prbDispatcherBound   = False
        self._lastVisibleState     = None
        self._lastBattleVisibleState = None
        self._userHidden           = False
        self._battleBadgeEnabled   = True
        self._battleHiddenReasons  = set()
        self._battleGuiEventsBound = False
        self._battleKillCamBound   = False
        self._battleKillCamCtrl    = None
        self._battleResultsOpen    = False
        self._pendingBattleResultProgress = None
        self._battleMode           = False
        self._battleTankID         = None
        self._battleLiveDamage     = 0
        self._battleDirectDamage   = 0
        self._battleAssistSpotDamage = 0
        self._battleAssistTrackDamage = 0
        self._battleAssistStunDamage = 0
        self._battleBaseAvgDamage  = 0
        self._battleBaselineMark    = None
        self._overlayWindowCount   = 0
        self._battleMarksOnGun      = -1
        self._battleStatsPollCallbackId = None
        self._battleFeedback = None
        self._battleFeedbackEventName = None
        self._battleFeedbackEvents = []
        self._battleFeedbackBindCallbackId = None
        self._battleBadgeShowCallbackId = None
        self._battlePeriodPollCallbackId = None
        self._ctrlN_held = False
        self._configEnabled = True
        self._configMarkBadge = True
        self._configPanelBodyVisible = True
        self._configGaragePanelMode = _DEFAULT_VIEW_MODE
        self._configBadgeStyle = 0
        self._cachedBadgeStyle = None
        self._loadCache()
        self._loadConfig()

    def setActiveAccount(self, accountDBID):
        try:
            accountDBID = int(accountDBID or 0)
        except (TypeError, ValueError):
            return
        if not accountDBID:
            return
        if self._currentAccountDBID != accountDBID:
            self._currentAccountDBID = accountDBID
            logger.debug('controller: active account set to %s', accountDBID)
            if self._enabled and self._panelReady:
                self._refresh()

    def clearActiveAccount(self):
        self._currentAccountDBID = 0

    def _getHistoryForTank(self, tankID):
        if not self._currentAccountDBID or tankID is None:
            return []
        bucket = self._markHistory.get(self._currentAccountDBID)
        if not bucket:
            return []
        return _dictGetTank(bucket, tankID, [])

    def _getLastKnownMark(self, tankID):
        if not self._currentAccountDBID or tankID is None:
            return None
        bucket = self._lastKnownMark.get(self._currentAccountDBID)
        if not bucket:
            return None
        return _dictGetTank(bucket, tankID)

    def _ensureActiveAccount(self):
        if self._currentAccountDBID:
            return self._currentAccountDBID
        dbid = _getActiveAccountDBID()
        if dbid:
            self._currentAccountDBID = dbid
        return self._currentAccountDBID

    def _getLastKnownStats(self, tankID):
        if tankID is None or not self._ensureActiveAccount():
            return {}
        bucket = self._lastKnownMarkStats.get(self._currentAccountDBID)
        if not bucket:
            return {}
        stats = _dictGetTank(bucket, tankID)
        if isinstance(stats, dict):
            return dict(stats)
        return {}

    def _updateLastKnownStats(self, tankID, mark=None, movingAvgDamage=None,
                              marksOnGun=None, force=False):
        if tankID is None or not self._ensureActiveAccount():
            return {}
        key = _tankKey(tankID)
        bucket = self._lastKnownMarkStats.setdefault(self._currentAccountDBID, {})
        stats = dict(_dictGetTank(bucket, key, {}) or {})
        changed = False

        if mark is not None:
            try:
                mark = float(mark)
                if force or mark > 0.0 or 'damageRating' not in stats:
                    prevRating = _safeFloat(stats.get('damageRating'))
                    if force or prevRating is None or abs(prevRating - mark) > 0.0001:
                        stats['damageRating'] = mark
                        changed = True
                markBucket = self._lastKnownMark.setdefault(self._currentAccountDBID, {})
                prev = _dictGetTank(markBucket, key)
                if force or prev is None or abs(float(prev) - mark) > 0.0001:
                    markBucket[key] = mark
                    changed = True
            except (TypeError, ValueError):
                pass

        if movingAvgDamage is not None:
            try:
                movingAvgDamage = float(movingAvgDamage)
                if movingAvgDamage > 0.0:
                    prevAvg = _safeFloat(stats.get('movingAvgDamage'))
                    if prevAvg is None or abs(prevAvg - movingAvgDamage) > 0.0001:
                        stats['movingAvgDamage'] = movingAvgDamage
                        changed = True
            except (TypeError, ValueError):
                pass

        if marksOnGun is not None:
            try:
                marksOnGun = int(marksOnGun)
                if marksOnGun >= 0 and stats.get('marksOnGun') != marksOnGun:
                    stats['marksOnGun'] = marksOnGun
                    changed = True
            except (TypeError, ValueError):
                pass

        if stats:
            bucket[key] = stats
        if changed:
            self._scheduleSaveCache()
        return stats

    def _capturePreBattleStats(self, tankID):
        stats = self._getLastKnownStats(tankID)
        mark = self._readLiveMarkForTank(tankID)
        if mark is None:
            mark = stats.get('damageRating')
        if mark is None:
            mark = self._getLastKnownMark(tankID)

        movingAvg = _readMarkAverageDamageForTank(tankID)
        if movingAvg <= 0:
            try:
                movingAvg = int(round(float(stats.get('movingAvgDamage') or 0)))
            except (TypeError, ValueError):
                movingAvg = 0

        marks = _readGunMarksForTank(tankID)
        if marks < 0:
            try:
                marks = int(stats.get('marksOnGun', -1))
            except (TypeError, ValueError):
                marks = -1
        # dossier РјРѕР¶Рµ РїРѕРІРµСЂС‚Р°С‚Рё 0 (РЅРµ РѕРЅРѕРІР»РµРЅРёР№ РїС–СЃР»СЏ РїРѕРїРµСЂРµРґРЅСЊРѕРіРѕ Р±РѕСЋ)
        # СЏРєС‰Рѕ РєРµС€ РјР°С” РєСЂР°С‰Рµ Р·РЅР°С‡РµРЅРЅСЏ вЂ” Р·Р±РµСЂС–РіР°С”РјРѕ Р№РѕРіРѕ
        cached_marks = self._getCachedMarksOnGun(tankID)
        if cached_marks > marks:
            marks = cached_marks
        logger.debug('capturePreBattle: tankID=%s marks=%d (dossier=%d cached=%d)',
                     tankID, marks, _readGunMarksForTank(tankID), cached_marks)

        return self._updateLastKnownStats(
            tankID, mark=mark, movingAvgDamage=movingAvg,
            marksOnGun=marks, force=False)

    def _getCachedMovingAvg(self, tankID):
        stats = self._getLastKnownStats(tankID)
        try:
            value = float(stats.get('movingAvgDamage') or 0)
            if value > 0:
                return value
        except (TypeError, ValueError):
            pass
        return 0.0

    def _getCachedMarksOnGun(self, tankID):
        stats = self._getLastKnownStats(tankID)
        try:
            return int(stats.get('marksOnGun', -1))
        except (TypeError, ValueError):
            return -1

    def _getPendingSnapshot(self, tankID):
        if self._session is None:
            return None
        try:
            return self._session.peekSnapshot(tankID)
        except Exception:
            return None

    def _hasPendingSnapshot(self, tankID):
        return self._getPendingSnapshot(tankID) is not None

    def _getBaselineHint(self, tankID, arenaID=None):
        if arenaID is not None and self._currentAccountDBID:
            try:
                history = _dictGetTank(self._markHistory.get(self._currentAccountDBID, {}), tankID, [])
                for entry in reversed(history):
                    if isinstance(entry, dict) and entry.get('arenaID') == arenaID:
                        baseline = entry.get('baseline')
                        if baseline is not None:
                            return float(baseline)
            except Exception:
                pass
        snap = self._getPendingSnapshot(tankID)
        if snap is not None:
            try:
                return float(snap.get('mark'))
            except (TypeError, ValueError):
                pass
        try:
            tankIDInt = _tankKey(tankID)
        except (TypeError, ValueError):
            tankIDInt = None
        if tankIDInt is not None and _dictGetTank(self._pendingBaseline, tankIDInt) is not None:
            try:
                return float(_dictGetTank(self._pendingBaseline, tankIDInt))
            except (TypeError, ValueError):
                pass
        stats = self._getLastKnownStats(tankID)
        try:
            mark = stats.get('damageRating')
            if mark is not None:
                return float(mark)
        except (TypeError, ValueError):
            pass
        return self._getLastKnownMark(tankID)

    def _setLastKnownMark(self, tankID, mark, force=False):
        if not self._currentAccountDBID or tankID is None or mark is None:
            return
        key = _tankKey(tankID)
        bucket = self._lastKnownMark.setdefault(self._currentAccountDBID, {})
        prev = _dictGetTank(bucket, key)
        if force or prev is None or abs(float(prev) - float(mark)) > 0.0001:
            bucket[key] = float(mark)
            self._scheduleSaveCache()
        self._updateLastKnownStats(tankID, mark=mark, force=force)

    def _scheduleMarkRetry(self, attempt=0):
        _cancelCallbackSafe(self._markRetryCallbackId)
        if attempt >= 30:
            logger.debug('mark retry: gave up after %d attempts', attempt)
            return
        if attempt < 5:
            delay = 0.3
        else:
            delay = 0.5 + (attempt - 5) * 0.5
        self._markRetryCallbackId = BigWorld.callback(
            delay, lambda: self._markRetryTick(attempt + 1))

    def _markRetryTick(self, attempt):
        self._markRetryCallbackId = None
        if not self._enabled:
            return
        if not g_currentVehicle.isPresent():
            return
        tankID = getattr(g_currentVehicle.item, 'intCD', None)
        if tankID is None:
            return
        mark = self._readLiveMarkForTank(tankID)
        if mark is None:
            logger.debug('mark retry: attempt %d, still no mark for tankID=%s', attempt, tankID)
            self._scheduleMarkRetry(attempt)
            return
        logger.debug('mark retry: got mark=%.2f for tankID=%s on attempt %d', mark, tankID, attempt)
        if not self._hasPendingSnapshot(tankID):
            self._setLastKnownMark(tankID, mark)
            self._capturePreBattleStats(tankID)
        else:
            logger.debug('mark retry: keep pre-battle baseline for tankID=%s until results', tankID)
        self._refresh()
        if self._battleResultsOpen:
            self._syncBattleResultProgress()
        if self._battleMode and self._battleTankID == tankID:
            self._pushBattleBadge()
        if attempt < 8:
            self._scheduleMarkRetry(attempt)

    def _onItemsCacheSynced(self, *_):
        try:
            ServicesLocator.itemsCache.onSyncCompleted -= self._onItemsCacheSynced
        except Exception:
            pass
        logger.debug('itemsCache synced, refreshing mark')
        self._captureCurrentMarkSample()
        self._scheduleRefresh(0.1)

    def enable(self):
        if self._enabled:
            lsm = getLobbyStateMachine()
            if lsm is not None:
                try:
                    routeInfo = lsm.visibleRouteInfo
                    self._hangarVisible = (self._isHangarState(routeInfo.state)
                                           or self._routeLooksHangar(routeInfo))
                except Exception:
                    self._hangarVisible = False
            if self._hangarVisible:
                if self._injectorView is None:
                    self._injectFlash()
                elif self._panelReady:
                    self._refresh()
            return
        self._enabled = True
        self._visibleByData = False
        g_currentVehicle.onChanged += self._onVehicleChanged
        try:
            ServicesLocator.settingsCore.interfaceScale.onScaleChanged += self._onScaleChanged
            self._scaleBound = True
        except Exception:
            self._scaleBound = False
        if g_guiResetters is not None and not self._guiResettersBound:
            try:
                g_guiResetters.add(self._onRecreateDevice)
                self._guiResettersBound = True
            except Exception:
                self._guiResettersBound = False
        lsm = getLobbyStateMachine()
        if lsm is not None:
            lsm.onVisibleRouteChanged += self._onVisibleRouteChanged
            try:
                routeInfo = lsm.visibleRouteInfo
                self._hangarVisible = (self._isHangarState(routeInfo.state)
                                       or self._routeLooksHangar(routeInfo))
            except Exception:
                self._hangarVisible = False
        else:
            self._hangarVisible = False
        # Subscribe to window open/close events to detect postBattleResults
        self._subscribeWindowEvents()
        if self._hangarVisible:
            if self._injectorView is None:
                self._injectFlash()
            else:
                self._refresh()
        try:
            if g_currentVehicle.isPresent():
                    _curTankID = getattr(g_currentVehicle.item, 'intCD', None)
                    if _curTankID is not None:
                        _baseline = self._getLastKnownMark(_curTankID)
                        if _baseline is not None:
                            self._pendingBaseline[_tankKey(_curTankID)] = float(_baseline)
                            self._capturePreBattleStats(_curTankID)
                            logger.debug('baseline captured: tankID=%s mark=%.2f',
                                         _curTankID, float(_baseline))
        except Exception:
            logger.exception('baseline capture failed')

        try:
            if not ServicesLocator.itemsCache.isSynced():
                ServicesLocator.itemsCache.onSyncCompleted += self._onItemsCacheSynced
        except Exception:
            pass
        self._scheduleMarkRetry()
        self._bindPrbDispatcher()
        logger.debug('enabled, hangarVisible=%s', self._hangarVisible)

    def disable(self):
        if not self._enabled:
            return
        self._closeDetailIfOpen()
        self._enabled = False
        try:
            g_currentVehicle.onChanged -= self._onVehicleChanged
        except Exception:
            pass
        try:
            ServicesLocator.itemsCache.onSyncCompleted -= self._onItemsCacheSynced
        except Exception:
            pass
        _cancelCallbackSafe(self._refreshCallbackId)
        self._refreshCallbackId = None
        _cancelCallbackSafe(self._markRetryCallbackId)
        self._markRetryCallbackId = None
        _cancelCallbackSafe(self._battlePeriodPollCallbackId)
        self._battlePeriodPollCallbackId = None
        self._unbindBattleGUIEvents()
        self._unbindBattleKillCam()
        if self._scaleBound:
            try:
                ServicesLocator.settingsCore.interfaceScale.onScaleChanged -= self._onScaleChanged
            except Exception:
                pass
            self._scaleBound = False
        if self._guiResettersBound and g_guiResetters is not None:
            try:
                g_guiResetters.remove(self._onRecreateDevice)
            except Exception:
                pass
            self._guiResettersBound = False
        self._unbindPrbDispatcher()
        lsm = getLobbyStateMachine()
        if lsm:
            try:
                lsm.onVisibleRouteChanged -= self._onVisibleRouteChanged
            except Exception:
                pass
        self._unsubscribeWindowEvents()
        if self._panelReady and self._injectorView is not None:
            try:
                self._injectorView.flashObject.as_setVisible(False)
                self._injectorView.flashObject.as_setBattleBadgeVisible(False)
            except Exception:
                pass
        self._hangarVisible        = False
        self._visibleByData        = False
        self._modsSettingsOpen     = False
        self._queueModeAllowed     = True
        self._strongholdScreenOpen = False
        self._battleMode           = False
        self._battleTankID         = None
        self._battleBaseAvgDamage  = 0
        self._battleMarksOnGun     = -1
        self._battleHiddenReasons.clear()
        self._lastBattleVisibleState = None
        self._strongholdBrowserIDs.clear()
        self._lastVisibleState     = None
        logger.debug('disabled')

    def toggleUserHidden(self):
        if self._battleMode:
            if not (self._configEnabled and self._configMarkBadge):
                logger.debug('toggleBattleBadge ignored by config')
                return
            self._battleBadgeEnabled = not self._battleBadgeEnabled
            self._lastBattleVisibleState = None
            self._updateBattleVisibility()
            self._scheduleSaveCache()
            logger.debug('toggleBattleBadge: enabled=%s', self._battleBadgeEnabled)
            return
        self._userHidden = not self._userHidden
        self._lastVisibleState = None
        self._updateVisibility()
        logger.debug('toggleUserHidden: hidden=%s', self._userHidden)

    def setMarkBadgeControlVisible(self, visible):
        if not (self._panelReady and self._injectorView):
            return
        try:
            self._injectorView.flashObject.as_setMarkBadgeControlVisible(bool(visible))
        except Exception:
            logger.debug('as_setMarkBadgeControlVisible not supported by SWF, skipping')

    def _onScaleChanged(self, scale):
        if self._panelReady and self._injectorView:
            try:
                self._injectorView.flashObject.as_setPosition(self._position)
            except Exception:
                logger.exception('as_setPosition on scale change failed')
        self._refresh()

    def _onRecreateDevice(self):
        if not (self._panelReady and self._injectorView):
            return
        logger.debug('device recreated вЂ” reapplying panel position/visibility')
        try:
            self._injectorView.flashObject.as_setPosition(self._position)
        except Exception:
            logger.exception('as_setPosition on device reset failed')
        self._lastVisibleState = None
        self._updateVisibility()

    @staticmethod
    def _isHangarState(state):
        cls = _getDefaultHangarStateCls()
        if cls is None or state is None:
            return False
        lsm = getLobbyStateMachine()
        if lsm is None:
            return False
        try:
            return state == lsm.getStateByCls(cls)
        except Exception:
            return False

    @staticmethod
    def _routeText(routeInfo):
        parts = []
        for value in (routeInfo, getattr(routeInfo, 'state', None),
                      getattr(routeInfo, 'name', None), getattr(routeInfo, 'path', None)):
            if value is None:
                continue
            try:
                parts.append(str(value).lower())
                parts.append(value.__class__.__name__.lower())
            except Exception:
                pass
        return ' '.join(parts)

    @staticmethod
    def _routeLooksNonHangar(routeInfo):
        """РџРѕРІРµСЂС‚Р°С” True СЏРєС‰Рѕ route РІРєР°Р·СѓС” РЅР° РїС–РґРµРєСЂР°РЅ (РЅРµ РѕСЃРЅРѕРІРЅРёР№ РіР°СЂР°Р¶)."""
        if routeInfo is None:
            return False
        parts = []
        for value in (getattr(routeInfo, 'name', None), getattr(routeInfo, 'path', None)):
            if value is None:
                continue
            try:
                parts.append(str(value).lower())
            except Exception:
                pass
        text = ' '.join(parts)
        _NON_HANGAR = ('quest', 'task', 'mission', 'battle_pass', 'battlepass',
                       'store', 'shop', 'crew', 'research', 'tech_tree', 'techtree',
                       'clan', 'rating', 'event', 'blueprint', 'ranked', 'collection',
                       'advent', 'marathon', 'lootbox', 'season', 'postbattle',
                       'post_battle', 'result', 'achievement', 'award')
        return any(x in text for x in _NON_HANGAR)

    @staticmethod
    def _routeLooksHangar(routeInfo):
        if routeInfo is None:
            return False
        parts = []
        for value in (routeInfo, getattr(routeInfo, 'state', None),
                      getattr(routeInfo, 'name', None), getattr(routeInfo, 'path', None)):
            if value is None:
                continue
            try:
                parts.append(str(value).lower())
                parts.append(value.__class__.__name__.lower())
            except Exception:
                pass
        text = ' '.join(parts)
        # РЇРІРЅРѕ РІРёРєР»СЋС‡Р°С”РјРѕ РІСЃС– РїС–РґРµРєСЂР°РЅРё РґРµ РїР°РЅРµР»СЊ РЅРµ РїРѕС‚СЂС–Р±РЅР°
        _EXCLUDE = ('postbattle', 'post_battle', 'quest', 'task', 'mission',
                    'battle_pass', 'battlepass', 'store', 'shop', 'crew',
                    'research', 'tech_tree', 'techtree', 'clan', 'rating',
                    'event', 'blueprint', 'ranked', 'collection', 'advent',
                    'marathon', 'lootbox', 'season')
        if any(x in text for x in _EXCLUDE):
            return False
        return 'hangar' in text or 'garage' in text

    def _onVisibleRouteChanged(self, routeInfo):
        state = getattr(routeInfo, 'state', None)
        routeText = self._routeText(routeInfo)
        isPostBattle = 'postbattle' in routeText or 'post_battle' in routeText
        # Р”РµС‚Р°Р»СЊРЅРёР№ Р»РѕРі РґР»СЏ РґС–Р°РіРЅРѕСЃС‚РёРєРё РїС–РґРµРєСЂР°РЅС–РІ
        logger.debug('visibleRouteChanged: state=%s name=%s path=%s text=%s',
                     state,
                     getattr(routeInfo, 'name', None),
                     getattr(routeInfo, 'path', None),
                     routeText[:120])
        self._hangarVisible = (not isPostBattle and
                               (self._isHangarState(state)
                                or self._routeLooksHangar(routeInfo)))
        logger.debug('visibleRouteChanged: hangarVisible=%s postBattle=%s route=%s',
                     self._hangarVisible, isPostBattle, routeInfo)
        if isPostBattle:
            if not self._battleResultsOpen:
                self._onBattleResultsWindowChanged(True)
        else:
            if self._battleResultsOpen:
                self._onBattleResultsWindowChanged(False)
        if self._hangarVisible and not self._panelReady and not self._injectorView:
            self._injectFlash()
        self._updateVisibility()

    def _updateVisibility(self):
        if not (self._panelReady and self._injectorView):
            return
        # РџРµСЂРµРІС–СЂСЏС”РјРѕ РїРѕС‚РѕС‡РЅРёР№ route вЂ” РїРѕРєР°Р·СѓС”РјРѕ РўР†Р›Р¬РљР СЏРєС‰Рѕ С†Рµ РѕСЃРЅРѕРІРЅРёР№ РіР°СЂР°Р¶
        hangarCheck = self._hangarVisible
        if hangarCheck:
            try:
                lsm = getLobbyStateMachine()
                if lsm is not None:
                    routeInfo = lsm.visibleRouteInfo
                    hangarCheck = self._isHangarState(routeInfo.state)
            except Exception:
                pass
        visible = bool(self._configEnabled
                       and hangarCheck and self._visibleByData
                       and not self._modsSettingsOpen
                       and self._queueModeAllowed
                       and not self._strongholdScreenOpen
                       and not self._userHidden)
        logger.debug('updateVisibility: visible=%s hangar=%s data=%s mods=%s queue=%s sh=%s',
                     visible, self._hangarVisible, self._visibleByData,
                     self._modsSettingsOpen, self._queueModeAllowed,
                     self._strongholdScreenOpen)
        if self._lastVisibleState == visible:
            return
        self._lastVisibleState = visible
        try:
            self._injectorView.flashObject.as_setVisible(visible)
        except Exception:
            logger.exception('as_setVisible failed')

    def _setBattleHidden(self, reason, hidden):
        wasHidden = reason in self._battleHiddenReasons
        if hidden:
            self._battleHiddenReasons.add(reason)
        else:
            self._battleHiddenReasons.discard(reason)
        if wasHidden != hidden:
            self._updateBattleVisibility()

    def _updateBattleVisibility(self):
        if not (self._battlePanelReady and self._battleInjectorView):
            return
        visible = bool(self._configEnabled
                       and self._configMarkBadge
                       and self._battleMode and self._battleTankID is not None
                       and self._battleBadgeEnabled
                       and not self._battleHiddenReasons
                       and not _isReplayPlaying()
                       and self._battleBadgeShowCallbackId is None)
        logger.debug('battle visibility: visible=%s mode=%s tankID=%s hidden=%s',
                     visible, self._battleMode, self._battleTankID,
                     sorted(self._battleHiddenReasons))
        if self._lastBattleVisibleState == visible:
            return
        self._lastBattleVisibleState = visible
        try:
            self._battleInjectorView.flashObject.as_setVisible(False)
            self._battleInjectorView.flashObject.as_setBattleBadgeVisible(visible)
        except Exception:
            logger.exception('as_setBattleBadgeVisible failed')

    def _isBattleActuallyLive(self):
        try:
            player = BigWorld.player()
            arena = getattr(player, 'arena', None)
            if arena is None:
                return False
            period = getattr(arena, 'period', None)
            arenaPeriod = getattr(constants, 'ARENA_PERIOD', None)
            battlePeriod = getattr(arenaPeriod, 'BATTLE', None) if arenaPeriod is not None else None
            if period is None or battlePeriod is None:
                return True
            return period == battlePeriod
        except Exception:
            return True

    def _startBattlePeriodPolling(self):
        _cancelCallbackSafe(self._battlePeriodPollCallbackId)
        self._battlePeriodPollCallbackId = BigWorld.callback(0.5, self._pollBattlePeriod)

    def _pollBattlePeriod(self):
        self._battlePeriodPollCallbackId = None
        if not self._battleMode:
            return
        self._lastBattleVisibleState = None
        self._updateBattleVisibility()
        self._startBattlePeriodPolling()

    def _bindBattleGUIEvents(self):
        if self._battleGuiEventsBound:
            return
        if g_eventBus is None or GameEvent is None or EVENT_BUS_SCOPE is None:
            logger.debug('battle gui events: API unavailable')
            return
        self._battleGuiEventsBound = True
        try:
            g_eventBus.addListener(getattr(GameEvent, 'GUI_VISIBILITY'),
                                   self._onBattleGUIVisibility,
                                   scope=EVENT_BUS_SCOPE.BATTLE)
            for eventName in ('FULL_STATS', 'FULL_STATS_QUEST_PROGRESS',
                              'FULL_STATS_PERSONAL_RESERVES', 'EVENT_STATS'):
                if hasattr(GameEvent, eventName):
                    g_eventBus.addListener(getattr(GameEvent, eventName),
                                           self._onBattleStatsToggle,
                                           scope=EVENT_BUS_SCOPE.BATTLE)
        except Exception:
            self._unbindBattleGUIEvents()
            logger.exception('battle gui events: subscribe failed')

    def _unbindBattleGUIEvents(self):
        if not self._battleGuiEventsBound:
            return
        self._battleGuiEventsBound = False
        if g_eventBus is None or GameEvent is None or EVENT_BUS_SCOPE is None:
            return
        try:
            if hasattr(GameEvent, 'GUI_VISIBILITY'):
                g_eventBus.removeListener(GameEvent.GUI_VISIBILITY,
                                          self._onBattleGUIVisibility,
                                          scope=EVENT_BUS_SCOPE.BATTLE)
            for eventName in ('FULL_STATS', 'FULL_STATS_QUEST_PROGRESS',
                              'FULL_STATS_PERSONAL_RESERVES', 'EVENT_STATS'):
                if hasattr(GameEvent, eventName):
                    g_eventBus.removeListener(getattr(GameEvent, eventName),
                                              self._onBattleStatsToggle,
                                              scope=EVENT_BUS_SCOPE.BATTLE)
        except Exception:
            pass

    def _onBattleGUIVisibility(self, event):
        try:
            visible = bool(event.ctx.get('visible', True))
        except Exception:
            visible = True
        self._setBattleHidden('ui', not visible)

    def _onBattleStatsToggle(self, event):
        try:
            hidden = bool(event.ctx.get('isDown', False))
        except Exception:
            hidden = False
        self._setBattleHidden('stats', hidden)
        # Alt Р·Р°С‚РёСЃРЅРµРЅРёР№ вЂ” СЂРѕР·РєСЂРёРІР°С”РјРѕ badge Р· РЅР°Р№Р±Р»РёР¶С‡РѕСЋ РїР»Р°РЅРєРѕСЋ
        try:
            if self._battleInjectorView:
                self._battleInjectorView.flashObject.as_setBattleBadgeExpanded(hidden)
        except Exception:
            pass

    def onShowExtendedInfo(self, isShown):
        """РҐСѓРє РЅР° AvatarInputHandler.showExtendedInfo вЂ” Alt РІ Р±РѕСЋ."""
        try:
            if self._battleInjectorView:
                self._battleInjectorView.flashObject.as_setBattleBadgeExpanded(bool(isShown))
                logger.debug('showExtendedInfo: expanded=%s', isShown)
        except Exception:
            pass

    def _installInputHandlerHook(self):
        """РҐСѓРєР°С”РјРѕ handleKeyEvent С‡РµСЂРµР· player().inputHandler РґР»СЏ Alt РІ Р±РѕСЋ."""
        global _ORIG_SHOW_EXTENDED_INFO
        try:
            player = BigWorld.player()
            handler = getattr(player, 'inputHandler', None)
            if handler is None:
                BigWorld.callback(0.5, self._installInputHandlerHook)
                return
            cls = type(handler)
            orig = getattr(cls, 'handleKeyEvent', None)
            if orig is None:
                logger.debug('inputHandler: handleKeyEvent not found')
                return
            if getattr(orig, '_mastery_hooked', False):
                return
            _ORIG_SHOW_EXTENDED_INFO = orig
            ctrl = weakref.ref(self)
            import Keys
            ALT_KEYS = set()
            for attr in ('KEY_LALT', 'KEY_RALT', 'KEY_LEFTALT', 'KEY_RIGHTALT'):
                v = getattr(Keys, attr, None)
                if v is not None:
                    ALT_KEYS.add(v)
            if not ALT_KEYS:
                ALT_KEYS = {56}  # fallback: WoT keycode РґР»СЏ Alt
            logger.debug('inputHandler: Alt keys=%s', ALT_KEYS)
            def _hooked(self_h, event, *args, **kwargs):
                try:
                    evKey = getattr(event, 'key', None)
                    if evKey is None:
                        evKey = getattr(event, 'keyCode', None)
                    if ALT_KEYS and evKey in ALT_KEYS:
                        c = ctrl()
                        if c is not None:
                            c.onShowExtendedInfo(bool(event.isKeyDown()))
                except Exception:
                    pass
                return orig(self_h, event, *args, **kwargs)
            _hooked._mastery_hooked = True
            setattr(cls, 'handleKeyEvent', _hooked)
            logger.debug('inputHandler: hooked handleKeyEvent for Alt expand')
        except Exception as e:
            logger.debug('inputHandler hook failed: %s', e)

    def _bindBattleKillCam(self):
        if self._battleKillCamBound:
            return
        try:
            player = BigWorld.player()
            sessionProvider = getattr(player, 'guiSessionProvider', None)
            shared = getattr(sessionProvider, 'shared', None) if sessionProvider else None
            killCamCtrl = getattr(shared, 'killCamCtrl', None) if shared else None
            if killCamCtrl is None:
                return
            killCamCtrl.onKillCamModeStateChanged += self._onBattleKillCamStateChanged
            self._battleKillCamCtrl = killCamCtrl
            self._battleKillCamBound = True
        except Exception:
            logger.exception('battle killcam: subscribe failed')

    def _unbindBattleKillCam(self):
        if not self._battleKillCamBound:
            return
        try:
            if self._battleKillCamCtrl is not None:
                self._battleKillCamCtrl.onKillCamModeStateChanged -= self._onBattleKillCamStateChanged
        except Exception:
            pass
        self._battleKillCamCtrl = None
        self._battleKillCamBound = False
        self._setBattleHidden('killcam', False)

    def _onBattleKillCamStateChanged(self, state, *args, **kwargs):
        try:
            from gui.shared.events import DeathCamEvent
            deathState = DeathCamEvent.State
            hidden = ((deathState.STARTING.value <= state.value)
                      and (state.value < deathState.FINISHED.value))
        except Exception:
            hidden = False
        self._setBattleHidden('killcam', hidden)

    def _onVehicleChanged(self):
        logger.debug('vehicle changed')
        self._closeDetailIfOpen()
        self._captureCurrentMarkSample()
        self._garageVehicleRetryAttempt = 0
        self._lastVisibleState = None
        if self._injectorView:
            try:
                self._injectorView.flashObject.as_clearData()
            except Exception:
                pass
        # РЇРєС‰Рѕ РїС–СЃР»СЏ Р±РѕСЋ _hangarVisible=False Р°Р»Рµ РјРё РІР¶Рµ РІ РіР°СЂР°Р¶С– вЂ” РІС–РґРЅРѕРІР»СЋС”РјРѕ
        if not self._hangarVisible and not self._battleMode:
            try:
                lsm = getLobbyStateMachine()
                if lsm is not None:
                    routeInfo = lsm.visibleRouteInfo
                    if (self._isHangarState(routeInfo.state)
                            or self._routeLooksHangar(routeInfo)):
                        self._hangarVisible = True
                        logger.debug('vehicle changed: restoring hangarVisible from route')
            except Exception:
                pass
        self._scheduleRefresh(0.2)

    def _closeDetailIfOpen(self):
        if not self._detailOpen:
            return
        self._detailOpen = False
        if self._injectorView:
            try:
                self._injectorView.flashObject.as_showDetail(False)
            except Exception:
                pass

    def _readLiveMarkForTank(self, tankID):
        if tankID is None:
            return None
        try:
            if g_currentVehicle.isPresent():
                if getattr(g_currentVehicle.item, 'intCD', None) == tankID:
                    mark = _readMarkFromDossier(g_currentVehicle.getDossier(), debug_tankID=tankID)
                    if mark is not None:
                        return mark
        except Exception:
            logger.exception('livefix: g_currentVehicle.getDossier() failed')
        try:
            mark = _readMarkForTankID(tankID)
            if mark is not None:
                return mark
        except Exception:
            logger.exception('livefix: itemsCache mark read failed')
        return None

    def _getCurrentMarkDamage(self, tankID, mark=None):
        cached = self._getCachedMovingAvg(tankID)
        if self._battleMode and self._battleTankID == tankID and cached > 0:
            return int(round(cached))
        value = _readMarkAverageDamageForTank(tankID)
        if value > 0:
            self._updateLastKnownStats(tankID, movingAvgDamage=value)
            return int(value)
        if cached > 0:
            return int(round(cached))
        if mark is None:
            mark = self._readLiveMarkForTank(tankID)
        if mark is None:
            mark = self._getLastKnownMark(tankID)
        return _estimateMarkAverageDamage(mark, _dictGetTank(self._moeCache, tankID))

    def _captureCurrentMarkSample(self):
        try:
            if not g_currentVehicle.isPresent():
                return
            vehicle = g_currentVehicle.item
            tankID = getattr(vehicle, 'intCD', None)
            if tankID is None:
                return
            mark = self._readLiveMarkForTank(tankID)
            if mark is None:
                self._scheduleMarkRetry()
                return
            _cancelCallbackSafe(self._markRetryCallbackId)
            self._markRetryCallbackId = None
            if not self._hasPendingSnapshot(tankID):
                self._setLastKnownMark(tankID, mark)
                self._capturePreBattleStats(tankID)
            else:
                logger.debug('livefix: keep pre-battle baseline for tankID=%s until results', tankID)
        except Exception:
            logger.exception('livefix: capture current mark failed')

    def _onBattleProcessed(self, tankID, newMark, mapName=None, damage=0,
                           preMarkHint=None, arenaID=None, provisional=False):
        try:
            value = float(newMark)
        except (TypeError, ValueError):
            return
        try:
            damage = int(damage or 0)
        except (TypeError, ValueError):
            damage = 0
        if not self._currentAccountDBID:
            logger.debug('battle: skip, no active account (tankID=%s)', tankID)
            return

        entryMap = unicode(mapName) if mapName else u''
        try:
            tankIDInt = _tankKey(tankID)
        except (TypeError, ValueError):
            tankIDInt = None

        historyBucket = self._markHistory.setdefault(self._currentAccountDBID, {})
        tankKey = _tankKey(tankID)
        history = _dictGetTank(historyBucket, tankKey)
        if history is None:
            history = []
            historyBucket[tankKey] = history
        existing = None
        if arenaID is not None:
            for candidate in reversed(history):
                if isinstance(candidate, dict) and candidate.get('arenaID') == arenaID:
                    existing = candidate
                    break

        preMark = None
        preMovingAvg = None
        preMarksOnGun = None
        if existing is not None:
            try:
                preMark = float(existing.get('baseline'))
            except (TypeError, ValueError):
                preMark = None
            try:
                preMovingAvg = float(existing.get('baselineMovingAvg'))
            except (TypeError, ValueError):
                preMovingAvg = None
            if not entryMap:
                entryMap = unicode(existing.get('map', u'') or u'')
        if preMark is None and self._session is not None and existing is None:
            snap = self._session.consumeSnapshot(tankID)
            if snap is not None:
                try:
                    preMark = float(snap.get('mark'))
                except (TypeError, ValueError):
                    preMark = None
                try:
                    preMovingAvg = float(snap.get('movingAvgDamage'))
                except (TypeError, ValueError):
                    preMovingAvg = None
                try:
                    preMarksOnGun = int(snap.get('marksOnGun'))
                except (TypeError, ValueError):
                    preMarksOnGun = None
                if not entryMap:
                    entryMap = unicode(snap.get('map', u'') or u'')
                if tankIDInt is not None:
                    _dictPopTank(self._pendingBaseline, tankIDInt, None)
        if preMark is None and tankIDInt is not None and _dictGetTank(self._pendingBaseline, tankIDInt) is not None:
            preMark = float(_dictPopTank(self._pendingBaseline, tankIDInt))
            logger.debug('battle: using pendingBaseline=%.2f for tankID=%s',
                         preMark, tankID)
        if preMark is None and preMarkHint is not None:
            try:
                preMark = float(preMarkHint)
            except (TypeError, ValueError):
                preMark = None
        if preMark is None:
            fallback = self._getLastKnownMark(tankID)
            if fallback is not None:
                try:
                    preMark = float(fallback)
                except (TypeError, ValueError):
                    preMark = None
        if preMovingAvg is None:
            stats = self._getLastKnownStats(tankID)
            try:
                preMovingAvg = float(stats.get('movingAvgDamage'))
            except (TypeError, ValueError):
                preMovingAvg = None
            if preMarksOnGun is None:
                try:
                    preMarksOnGun = int(stats.get('marksOnGun'))
                except (TypeError, ValueError):
                    preMarksOnGun = None
        delta = (value - preMark) if preMark is not None else 0.0
        newMovingAvg = None
        if preMovingAvg is not None and preMovingAvg > 0 and damage > 0:
            newMovingAvg = (float(preMovingAvg) * (1.0 - _MOE_CALC_KOEFF)
                            + float(damage) * _MOE_CALC_KOEFF)

        entry = {
            'value':  value,
            'map':    entryMap,
            'delta':  float(delta),
            'damage': damage,
            'ts':     int(time.time()),
            'baseline': preMark,
            'baselineMovingAvg': preMovingAvg,
            'provisional': bool(provisional),
        }
        if newMovingAvg is not None:
            entry['movingAvgDamage'] = newMovingAvg
        if arenaID is not None:
            entry['arenaID'] = arenaID
        battleNum = _readBattlesCountForTank(tankID)
        if battleNum > 0:
            entry['num'] = battleNum
        if existing is None:
            history.append(entry)
        else:
            existing.update(entry)
        if len(history) > _MAX_HISTORY:
            del history[:-_MAX_HISTORY]

        if not provisional:
            self._updateLastKnownStats(
                tankID, mark=value, movingAvgDamage=newMovingAvg,
                marksOnGun=preMarksOnGun, force=True)
        self._scheduleSaveCache()
        logger.debug('battle: account=%s tankID=%s mark=%.2f delta=%+.2f dmg=%d map=%s history=%d update=%s',
                     self._currentAccountDBID, tankID, value, delta, damage, entryMap,
                     len(history), existing is not None)
        if not provisional:
            self._pushBattleResultProgress(value, delta)
        if (self._enabled and self._panelReady
                and g_currentVehicle.isPresent()
                and getattr(g_currentVehicle.item, 'intCD', None) == tankID):
            self._refresh()
            if self._detailOpen:
                self._pushDetail()

    def _pushBattleResultProgress(self, currentMark, delta):
        self._pendingBattleResultProgress = (float(currentMark), float(delta))
        logger.debug('battle result progress queued: mark=%.2f delta=%+.2f open=%s',
                     currentMark, delta, self._battleResultsOpen)
        if self._battleResultsOpen:
            self._syncBattleResultProgress()

    def _syncBattleResultProgress(self):
        pass  # РІРёРјРєРЅРµРЅРѕ

    def _subscribeWindowEvents(self):
        try:
            if _IWindowsManager is None:
                return
            wm = ServicesLocator.appControllersManager.getControllersMap().get(_IWindowsManager)
            if wm is None:
                return
            wm.onWindowStatusChanged += self._onWindowStatusChanged
        except Exception:
            pass

    def _unsubscribeWindowEvents(self):
        try:
            if _IWindowsManager is None:
                return
            wm = ServicesLocator.appControllersManager.getControllersMap().get(_IWindowsManager)
            if wm is None:
                return
            wm.onWindowStatusChanged -= self._onWindowStatusChanged
        except Exception:
            pass

    def _onWindowStatusChanged(self, uniqueID, flags):
        try:
            if _IWindowsManager is None:
                return
            wm = ServicesLocator.appControllersManager.getControllersMap().get(_IWindowsManager)
            if wm is None:
                return
            window = wm.findWindowById(uniqueID)
            if window is None:
                return
            view = getattr(window, 'content', None)
            if view is None:
                return
            name = _safeLower(getattr(view, 'uniqueName', None) or
                              type(view).__name__)
            from frameworks.wulf import WindowStatus
            isOpen = (flags & int(getattr(WindowStatus, 'LOADED', 2))) != 0

            # Р РµР·СѓР»СЊС‚Р°С‚Рё Р±РѕСЋ
            isResultsWindow = ('postbattle' in name or 'battleresult' in name or
                               'battle_result' in name or 'afterbattle' in name)
            if isResultsWindow:
                logger.debug('window status: name=%s isOpen=%s flags=%s', name, isOpen, flags)
                if isOpen != self._battleResultsOpen:
                    self._onBattleResultsWindowChanged(isOpen)
                return

            # Р‘СѓРґСЊ-СЏРєРµ С–РЅС€Рµ overlay С‰Рѕ РїРµСЂРµРєСЂРёРІР°С” РіР°СЂР°Р¶
            # Р†РіРЅРѕСЂСѓС”РјРѕ РЅР°С€ РІР»Р°СЃРЅРёР№ injector С‚Р° РґСЂС–Р±РЅС– popup-Рё
            _OWN = ('masterypanel', 'under_pressure')
            _IGNORE = ('tooltip', 'hint', 'cursor', 'bubble', 'notification',
                       'alert', 'tutorial', 'loading')
            if any(x in name for x in _OWN + _IGNORE):
                return
            # РўС–Р»СЊРєРё СЏРєС‰Рѕ РїР°РЅРµР»СЊ РІРёРґРёРјР° С– РјРё РІ РіР°СЂР°Р¶С–
            if not self._hangarVisible:
                return
            logger.debug('overlay window: name=%s isOpen=%s', name, isOpen)
            if isOpen:
                self._overlayWindowCount += 1
                if self._overlayWindowCount == 1:
                    self._hangarVisible = False
                    self._updateVisibility()
            else:
                self._overlayWindowCount = max(0, self._overlayWindowCount - 1)
                if self._overlayWindowCount == 0:
                    # РџРµСЂРµРІС–СЂСЏС”РјРѕ route С– РІС–РґРЅРѕРІР»СЋС”РјРѕ
                    try:
                        lsm = getLobbyStateMachine()
                        if lsm is not None:
                            routeInfo = lsm.visibleRouteInfo
                            if (self._isHangarState(routeInfo.state)
                                    or self._routeLooksHangar(routeInfo)):
                                self._hangarVisible = True
                                self._updateVisibility()
                    except Exception:
                        pass
        except Exception:
            pass

    def _onBattleResultsWindowChanged(self, isOpen):
        self._battleResultsOpen = bool(isOpen)
        logger.debug('battle results window: isOpen=%s', isOpen)
        if isOpen:
            self._hangarVisible = False
            self._lastVisibleState = None
            self._updateVisibility()
            self._syncBattleResultProgress()
        else:
            self._pendingBattleResultProgress = None
            if self._resultInjectorView:
                try:
                    self._resultInjectorView.flashObject.as_setBattleResultProgressVisible(False)
                except Exception:
                    pass
            BigWorld.callback(0.3, self._restoreHangarPanelAfterResults)

    def _restoreHangarPanelAfterResults(self):
        if not self._enabled or self._battleMode:
            return
        self._garageVehicleRetryAttempt = 0
        self._battleResultsOpen = False
        self._modsSettingsOpen = False
        self._queueModeAllowed = True
        self._strongholdScreenOpen = False
        # РџРµСЂРµРІС–СЂСЏС”РјРѕ РїРѕС‚РѕС‡РЅРёР№ route вЂ” СЏРєС‰Рѕ РіР°СЂР°Р¶, РїРѕРєР°Р·СѓС”РјРѕ РїР°РЅРµР»СЊ
        try:
            lsm = getLobbyStateMachine()
            if lsm is not None:
                routeInfo = lsm.visibleRouteInfo
                self._hangarVisible = (self._isHangarState(routeInfo.state)
                                       or self._routeLooksHangar(routeInfo))
        except Exception:
            pass
        # РЇРєС‰Рѕ route РЅРµ РІРёР·РЅР°С‡РёРІ вЂ” РїРѕРєР»Р°РґР°С”РјРѕСЃСЊ РЅР° РЅР°СЃС‚СѓРїРЅРёР№ visibleRouteChanged
        if not self._hangarVisible:
            return
        if self._injectorView is None or not self._panelReady:
            self._injectFlash()
            return
        if self._panelReady:
            self._lastVisibleState = None
            self._scheduleRefresh(0.1)

    def enterBattle(self, tankID):
        try:
            tankID = int(tankID)
        except (TypeError, ValueError):
            return
        if not self._currentAccountDBID:
            dbid = _getActiveAccountDBID()
            if dbid:
                self._currentAccountDBID = dbid
                logger.debug('enterBattle: accountDBID set to %s', dbid)
        self._hangarVisible = False
        self._visibleByData = False
        self._garageVehicleRetryAttempt = 0
        self._lastVisibleState = None
        if self._injectorView:
            try:
                self._injectorView.flashObject.as_setVisible(False)
                self._injectorView.flashObject.as_setBattleBadgeVisible(False)
                self._injectorView.flashObject.as_showDetail(False)
            except Exception:
                pass
        self._injectorView = None
        self._panelReady = False
        self._injectPending = False
        self._battleMode = True
        self._battleTankID = tankID
        self._battleLiveDamage = 0
        self._battleDirectDamage = 0
        self._battleAssistSpotDamage = 0
        self._battleAssistTrackDamage = 0
        self._battleAssistStunDamage = 0
        stats = self._capturePreBattleStats(tankID)
        current = stats.get('damageRating')
        if current is None:
            current = self._getBaselineHint(tankID)
        if current is None:
            current = self._getLastKnownMark(tankID)
        self._battleBaselineMark = current
        try:
            self._battleBaseAvgDamage = int(round(float(stats.get('movingAvgDamage') or 0)))
        except (TypeError, ValueError):
            self._battleBaseAvgDamage = 0
        if self._battleBaseAvgDamage <= 0:
            self._battleBaseAvgDamage = int(self._getCurrentMarkDamage(tankID, current))
        try:
            self._battleMarksOnGun = int(stats.get('marksOnGun', -1))
        except (TypeError, ValueError):
            self._battleMarksOnGun = -1
        self._enabled = True
        self._battlePanelReady = False
        self._battleInjectorView = None
        self._battleHiddenReasons.clear()
        self._lastBattleVisibleState = None
        self._bindBattleGUIEvents()
        self._injectBattleFlash()
        self._bindBattleKillCam()
        self._bindBattleFeedback()
        logger.debug('enterBattle: tankID=%s baseline=%.2f avgDmg=%d',
                     tankID, current or 0.0, self._battleBaseAvgDamage)
        # РҐСѓРєР°С”РјРѕ showExtendedInfo С‡РµСЂРµР· inputHandler (Alt РІ Р±РѕСЋ)
        self._installInputHandlerHook()

    def leaveBattle(self):
        _cancelCallbackSafe(self._battleStatsPollCallbackId)
        self._battleStatsPollCallbackId = None
        _cancelCallbackSafe(self._battleFeedbackBindCallbackId)
        self._battleFeedbackBindCallbackId = None
        _cancelCallbackSafe(self._battleBadgeShowCallbackId)
        self._battleBadgeShowCallbackId = None
        _cancelCallbackSafe(self._battlePeriodPollCallbackId)
        self._battlePeriodPollCallbackId = None
        self._unbindBattleGUIEvents()
        self._unbindBattleKillCam()
        self._unbindBattleFeedback()
        if self._battleInjectorView:
            try:
                self._battleInjectorView.flashObject.as_setBattleBadgeVisible(False)
            except Exception:
                pass
        self._battleMode = False
        self._battleTankID = None
        self._battleLiveDamage = 0
        self._battleDirectDamage = 0
        self._battleAssistSpotDamage = 0
        self._battleAssistTrackDamage = 0
        self._battleAssistStunDamage = 0
        self._battleBaseAvgDamage = 0
        self._battleBaselineMark = None
        self._battleMarksOnGun = -1
        self._battleHiddenReasons.clear()
        self._lastBattleVisibleState = None
        self._battlePanelReady = False
        self._overlayWindowCount = 0
        self._battleInjectorView = None
        self._queueModeAllowed = True
        self._lastVisibleState = None
        # Resubscribe to vehicle change вЂ” the event object may have been reset
        # during the battle session, causing _onVehicleChanged to stop firing.
        try:
            g_currentVehicle.onChanged -= self._onVehicleChanged
        except Exception:
            pass
        try:
            g_currentVehicle.onChanged += self._onVehicleChanged
        except Exception:
            pass
        BigWorld.callback(0.5, self._restoreHangarPanelAfterResults)

    def _injectBattleFlash(self, attempt=0):
        if not self._battleMode:
            return
        try:
            app = ServicesLocator.appLoader.getDefBattleApp()
            if app and app.initialized:
                app.loadView(SFViewLoadParams(_LINKAGE_BATTLE))
                return
        except Exception:
            logger.exception('battle inject failed (attempt=%d)', attempt)
        if attempt < _INJECT_MAX_ATTEMPTS:
            BigWorld.callback(_INJECT_RETRY_DELAY, lambda: self._injectBattleFlash(attempt + 1))

    def _injectResultsFlash(self, attempt=0):
        pass  # РІРёРјРєРЅРµРЅРѕ

    def _injectFlash(self, attempt=0):
        if not self._enabled or self._battleMode:
            return
        if self._injectorView is not None or (self._injectPending and attempt == 0):
            return
        self._injectPending = True
        try:
            app = ServicesLocator.appLoader.getDefLobbyApp()
            if app and app.initialized:
                app.loadView(SFViewLoadParams(_LINKAGE_HANGAR))
                return
        except Exception:
            logger.exception('inject failed (attempt=%d)', attempt)
        if attempt < _INJECT_MAX_ATTEMPTS:
            BigWorld.callback(_INJECT_RETRY_DELAY, lambda: self._injectFlash(attempt + 1))
        else:
            self._injectPending = False

    def _onInjectorReady(self, view):
        kind = getattr(view, '_viewKind', 'hangar')
        if kind == 'battle':
            self._battleInjectorView = view
            self._battlePanelReady = False
            logger.debug('battle injector ready')
        elif kind == 'results':
            self._resultInjectorView = view
            self._resultPanelReady = False
            logger.debug('results injector ready')
        else:
            self._injectorView = view
            self._panelReady = False
            self._injectPending = False
            logger.debug('lobby injector ready')

    def _onInjectorDisposed(self, view=None):
        if view is not None and view == self._battleInjectorView:
            self._battleInjectorView = None
            self._battlePanelReady = False
            self._lastBattleVisibleState = None
        elif view is not None and view == self._resultInjectorView:
            self._resultInjectorView = None
            self._resultPanelReady = False
        elif view is not None and view == self._injectorView:
            self._injectorView = None
            self._panelReady = False
            self._injectPending = False
            self._lastVisibleState = None
        elif view is None:
            self._injectorView = None
            self._panelReady = False
            self._injectPending = False
            self._battleInjectorView = None
            self._battlePanelReady = False
            self._lastBattleVisibleState = None
            self._resultInjectorView = None
            self._resultPanelReady = False
            self._lastVisibleState = None
        else:
            logger.debug('injector disposed: ignoring orphan view')

    def _onPanelReady(self, view=None):
        if view is not None and view == self._battleInjectorView:
            self._battlePanelReady = True
            logger.debug('battle panel ready')
            try:
                self._battleInjectorView.flashObject.as_setBattleBadgeOffset(self._battleBadgeOffset)
            except Exception:
                logger.exception('as_setBattleBadgeOffset failed')
            try:
                self._battleInjectorView.flashObject.as_setBattleBadgeStyle(int(self._configBadgeStyle))
            except Exception:
                logger.debug('as_setBattleBadgeStyle not supported by SWF, skipping')
            self._lastBattleVisibleState = None
            # Short delay lets the SWF finish layout, but still shows during countdown.
            _cancelCallbackSafe(self._battleBadgeShowCallbackId)
            self._battleBadgeShowCallbackId = BigWorld.callback(
                2.0, self._onBattleBadgeDelayedShow)
            return
        if view is not None and view == self._resultInjectorView:
            self._resultPanelReady = True
            logger.debug('results panel ready')
            try:
                self._resultInjectorView.flashObject.as_setLocalization({
                    'battleResultProgress': _tr('battleResultProgress', u'Marks progress'),
                })
                self._resultInjectorView.flashObject.as_setVisible(False)
            except Exception:
                logger.exception('results panel init calls failed')
            self._syncBattleResultProgress()
            return
 
        if view is not None and view is not self._injectorView:
            logger.debug('panel ready: ignoring orphan hangar view')
            return
        self._panelReady = True
        self._lastVisibleState = None
        logger.debug('panel ready pos=%s mode=%s', self._position, self._viewMode)
        if self._injectorView:
            try:
                self._injectorView.flashObject.as_setLocalization({
                    'loading':    _tr('loading',    u'...'),
                    'noData':     _tr('noData',     u'N/A'),
                    'lastBattle': _tr('lastBattle', u'Last battle'),
                    'bestBattle': _tr('bestBattle', u'Best battle'),
                    'dynamics':   _tr('dynamics',   u'Battle dynamics'),
                    'record':     _tr('record',     u'RECORD'),
                    'last10':     _tr('last10',     u'Last 10'),
                    'last25':     _tr('last25',     u'Last 25'),
                    'progress':   _tr('progress',   u'Marks progress'),
                    'battles':    _tr('battles',    u'Battles'),
                    'battleResultProgress': _tr('battleResultProgress', u'Marks progress'),
                })
                self._injectorView.flashObject.as_setPosition(self._position)
                self._injectorView.flashObject.as_setViewMode(int(self._viewMode))
                self._injectorView.flashObject.as_setPanelBodyVisible(
                    bool(self._configPanelBodyVisible))
                self._injectorView.flashObject.as_setMarkBadgeEnabled(bool(self._configMarkBadge))
                try:
                    self._injectorView.flashObject.as_setMarkBadgeStyle(int(self._configBadgeStyle))
                except Exception:
                    logger.debug('as_setMarkBadgeStyle not supported by SWF, skipping')
                self._injectorView.flashObject.as_setMarkBadgeOffset(self._markBadgeOffset)
                self._injectorView.flashObject.as_setMarkBadgeOpen(
                    bool(self._markBadgeOpen and self._configMarkBadge))
                self._injectorView.flashObject.as_setVisible(False)
                self._lastVisibleState = None
            except Exception:
                logger.exception('panel init calls failed')
        self._refresh()
        if self._battleResultsOpen:
            self._syncBattleResultProgress()
        # РЇРєС‰Рѕ _hangarVisible=False РїС–СЃР»СЏ РїРµСЂРµР·Р°РІР°РЅС‚Р°Р¶РµРЅРЅСЏ (РЅР°РїСЂ. РїС–СЃР»СЏ Р±РѕСЋ),
        # РїРµСЂРµРІС–СЂСЏС”РјРѕ РїРѕС‚РѕС‡РЅРёР№ route С– РІС–РґРЅРѕРІР»СЋС”РјРѕ РІРёРґРёРјС–СЃС‚СЊ
        if not self._hangarVisible and not self._battleMode:
            try:
                lsm = getLobbyStateMachine()
                if lsm is not None:
                    routeInfo = lsm.visibleRouteInfo
                    if (self._isHangarState(routeInfo.state)
                            or self._routeLooksHangar(routeInfo)):
                        self._hangarVisible = True
                        logger.debug('panel ready: restoring hangarVisible from route')
                        self._updateVisibility()
            except Exception:
                pass
        # Р—Р°РїСѓСЃРєР°С”РјРѕ polling РґР»СЏ РІС–РґСЃС‚РµР¶РµРЅРЅСЏ overlay-РµРєСЂР°РЅС–РІ
        self._startRoutePolling()

    def _onBattleBadgeDelayedShow(self):
        self._battleBadgeShowCallbackId = None
        if not (self._battlePanelReady and self._battleInjectorView and self._battleMode):
            return
        logger.debug('battle badge: delayed show')
        self._updateBattleVisibility()
        self._pushBattleBadge()

    def _pushBattleBadge(self):
        if not (self._battlePanelReady and self._battleInjectorView and self._battleMode and self._battleTankID is not None):
            return
        tankID = self._battleTankID
        moe = _dictGetTank(self._moeCache, tankID)
        if moe is None:
            self._requestDistribution(tankID, 'damage')
            moe = self._EMPTY_MOE
        current = self._getBaselineHint(tankID)
        if current is None:
            current = self._battleBaselineMark
        if current is None:
            current = self._getLastKnownMark(tankID)
        if current is None:
            current = 0.0
            logger.debug('battle badge: no baseline mark, showing fallback 0.00')
        self._battleBaselineMark = current
        if self._battleBaseAvgDamage <= 0:
            self._battleBaseAvgDamage = int(self._getCurrentMarkDamage(tankID, current))
        projectedMark, projectedAvg = _estimateProjectedMark(
            self._battleBaseAvgDamage, self._battleLiveDamage, moe, float(current))
        stars = self._battleMarksOnGun
        if stars <= 0:
            stars = self._getCachedMarksOnGun(tankID)
        if stars <= 0:
            stars = _readGunMarksForTank(tankID)
        if stars <= 0:
            stars = -1  # РЅРµРІС–РґРѕРјРѕ вЂ” AS3 РїРѕРєР°Р¶Рµ СЃС–СЂС– Р·С–СЂРєРё
        logger.debug('battle badge: stars resolved=%d (battleMarksOnGun=%d)',
                     stars, self._battleMarksOnGun)
        try:
            logger.debug('battle badge: pushing data mark=%.2f p65=%d p85=%d p95=%d dmg=%d base=%d stars=%d proj=%.2f',
                         current,
                         int(moe.get('p65') or 0), int(moe.get('p85') or 0),
                         int(moe.get('p95') or 0),
                         int(self._battleLiveDamage), int(self._battleBaseAvgDamage),
                         int(stars), float(projectedMark))
            try:
                self._battleInjectorView.flashObject.as_setBattleBadgeData(
                    float(current),
                    int(moe.get('p65') or 0),
                    int(moe.get('p85') or 0),
                    int(moe.get('p95') or 0),
                    int(moe.get('p100') or 0),
                    int(self._battleLiveDamage),
                    int(self._battleBaseAvgDamage),
                    int(stars),
                    float(projectedMark),
                    int(projectedAvg)
                )
                logger.debug('battle badge: as_setBattleBadgeData OK (10 args)')
            except TypeError:
                logger.debug('battle badge: old SWF signature, falling back to 8 args')
                self._battleInjectorView.flashObject.as_setBattleBadgeData(
                    float(current),
                    int(moe.get('p65') or 0),
                    int(moe.get('p85') or 0),
                    int(moe.get('p95') or 0),
                    int(moe.get('p100') or 0),
                    int(self._battleLiveDamage),
                    int(self._battleBaseAvgDamage),
                    int(stars)
                )
                logger.debug('battle badge: as_setBattleBadgeData OK (8 args)')
            self._updateBattleVisibility()
        except Exception:
            logger.exception('as_setBattleBadgeData failed')

    def _getBattleFeedbackSources(self):

        try:
            if g_sessionProvider is not None:
                shared = getattr(g_sessionProvider, 'shared', None)
                feedback = getattr(shared, 'feedback', None) if shared is not None else None
                if feedback is not None:
                    return [feedback]
        except Exception:
            pass
        try:
            if dependency is not None and IBattleSessionProvider is not None:
                provider = dependency.instance(IBattleSessionProvider)
                shared = getattr(provider, 'shared', None)
                feedback = getattr(shared, 'feedback', None) if shared is not None else None
                if feedback is not None:
                    return [feedback]
        except Exception:
            pass
        return []

    def _bindBattleFeedback(self, attempt=0):
        self._unbindBattleFeedback()
        bound = 0
        try:
            for feedback in self._getBattleFeedbackSources():
                for eventName in ('onPlayerFeedbackReceived',
                                  'onFeedbackReceived',
                                  'onBattleFeedbackReceived',
                                  'onDamageLogFeedbackReceived'):
                    event = getattr(feedback, eventName, None)
                    if event is None:
                        continue
                    try:
                        event += self._onBattlePerEventFeedback
                        self._battleFeedbackEvents.append((feedback, eventName, 'per'))
                        bound += 1
                        logger.debug('battle per-event feedback bound: %s', eventName)
                    except Exception:
                        pass
                for eventName in ('onPlayerSummaryFeedbackReceived',
                                  'onPostmortemSummaryReceived',
                                  'onMinimapFeedbackReceived'):
                    event = getattr(feedback, eventName, None)
                    if event is None:
                        continue
                    try:
                        event += self._onBattleSummaryFeedback
                        self._battleFeedbackEvents.append((feedback, eventName, 'summary'))
                        self._battleFeedback = feedback
                        self._battleFeedbackEventName = eventName
                        bound += 1
                        logger.debug('battle summary feedback bound: %s', eventName)
                    except Exception:
                        pass
        except Exception:
            logger.exception('battle feedback bind failed')
        if bound > 0:
            return
        if self._battleMode and attempt < 20:
            _cancelCallbackSafe(self._battleFeedbackBindCallbackId)
            self._battleFeedbackBindCallbackId = BigWorld.callback(
                0.5, lambda: self._bindBattleFeedback(attempt + 1))

    def _unbindBattleFeedback(self):
        if self._battleFeedbackEvents:
            for record in list(self._battleFeedbackEvents):
                feedback, eventName = record[0], record[1]
                kind = record[2] if len(record) > 2 else 'per'
                handler = self._onBattleSummaryFeedback if kind == 'summary' else self._onBattlePerEventFeedback
                try:
                    event = getattr(feedback, eventName, None)
                    if event is not None:
                        event -= handler
                except Exception:
                    pass
            self._battleFeedbackEvents = []
            self._battleFeedback = None
            self._battleFeedbackEventName = None

    def _onBattlePerEventFeedback(self, *args):
        if not (self._battleMode and self._battleTankID is not None):
            return
        events = args[0] if args else None
        if not events:
            return
        try:
            if isinstance(events, (list, tuple)):
                for event in events:
                    self._applyPerEvent(event)
            else:
                self._applyPerEvent(events)
        except Exception:
            logger.exception('per-event feedback handling failed')

    def _applyPerEvent(self, event):
        if event is None:
            return
        try:
            feedbackType = None
            fn = getattr(event, 'getType', None)
            if callable(fn):
                feedbackType = fn()
            battleType = None
            fn = getattr(event, 'getBattleEventType', None)
            if callable(fn):
                battleType = fn()

            damage = 0
            extra = None
            fn = getattr(event, 'getExtra', None)
            if callable(fn):
                extra = fn()
            if extra is not None:
                fn = getattr(extra, 'getDamage', None)
                if callable(fn):
                    try:
                        damage = int(fn() or 0)
                    except Exception:
                        damage = 0
                if damage <= 0:
                    try:
                        damage = int(extra or 0)
                    except Exception:
                        damage = 0
            if damage <= 0:
                fn = getattr(event, 'getCount', None)
                if callable(fn):
                    try:
                        damage = int(fn() or 0)
                    except Exception:
                        damage = 0

            if feedbackType is not None and FEEDBACK_EVENT_ID is not None:
                if feedbackType == getattr(FEEDBACK_EVENT_ID, 'PLAYER_DAMAGED_HP_ENEMY', None):
                    if damage > 0:
                        logger.debug('perEvent: DAMAGED_HP_ENEMY +%d (total direct=%d)',
                                     damage, self._battleDirectDamage + damage)
                        self.addBattleLiveDamage(damage)
                    return
                assistID = getattr(FEEDBACK_EVENT_ID, 'PLAYER_ASSIST_TO_KILL_ENEMY', None)
                if feedbackType == assistID and damage > 0:
                    try:
                        from BattleFeedbackCommon import BATTLE_EVENT_TYPE as _BET
                        if battleType == getattr(_BET, 'TRACK_ASSIST', None):
                            logger.debug('perEvent: ASSIST(track) +%d', damage)
                            self._battleAssistTrackDamage += damage
                        elif battleType == getattr(_BET, 'RADIO_ASSIST', None):
                            logger.debug('perEvent: ASSIST(spot) +%d', damage)
                            self._battleAssistSpotDamage += damage
                        else:
                            logger.debug('perEvent: ASSIST(generic) +%d', damage)
                            self._battleAssistSpotDamage += damage
                        self._syncBattleLiveDamage()
                    except Exception:
                        self._battleAssistSpotDamage += damage
                        self._syncBattleLiveDamage()
                    return
                stunID = getattr(FEEDBACK_EVENT_ID, 'PLAYER_ASSIST_TO_STUN_ENEMY', None)
                if feedbackType == stunID and damage > 0:
                    logger.debug('perEvent: ASSIST(stun) +%d', damage)
                    self._battleAssistStunDamage += damage
                    self._syncBattleLiveDamage()
                    return
            # Fallback: СЏРєС‰Рѕ feedbackType РЅРµ СЂРѕР·РїС–Р·РЅР°РЅРѕ вЂ” СЃРїСЂРѕР±СѓС”РјРѕ С‡РµСЂРµР· СЃС‚СЂСѓРєС‚СѓСЂСѓ РїРѕРґС–С—
            if damage > 0 and _looksAssistFeedback(event):
                kind = _assistKindFromFeedback(event)
                logger.debug('perEvent: fallback ASSIST(%s) +%d', kind, damage)
                if kind == 'track':
                    self._battleAssistTrackDamage += damage
                elif kind == 'stun':
                    self._battleAssistStunDamage += damage
                else:
                    self._battleAssistSpotDamage += damage
                self._syncBattleLiveDamage()
        except Exception:
            logger.exception('applyPerEvent failed')

    def _onBattleSummaryFeedback(self, *args):
        if not (self._battleMode and self._battleTankID is not None):
            return
        summaryEvent = args[0] if args else None
        if summaryEvent is None:
            return
        try:
            fn = getattr(summaryEvent, 'getTotalDamage', None)
            if callable(fn):
                val = int(fn() or 0)
                if val > 0:
                    # WoT getTotalDamage() РјРѕР¶Рµ РЅРµ РІРєР»СЋС‡Р°С‚Рё СЂР°РјС–РЅРі вЂ” С‡РёС‚Р°С”РјРѕ РѕРєСЂРµРјРѕ
                    ramming = _readMaxIntByKeysRecursive(summaryEvent, ('damageRamming', 'rammingDamage'))
                    val += ramming
                    logger.debug('summaryFeedback: getTotalDamage=%d (incl ramming=%d)', val, ramming)
                    self._battleDirectDamage = max(self._battleDirectDamage, val)
            # spot assist
            for method in ('getRadioAssistDamage', 'getTotalRadioAssistDamage',
                           'getSpotAssistDamage', 'getTotalSpotAssistDamage'):
                fn = getattr(summaryEvent, method, None)
                if callable(fn):
                    val = int(fn() or 0)
                    if val > 0:
                        logger.debug('summaryFeedback: %s=%d', method, val)
                        self._battleAssistSpotDamage = max(self._battleAssistSpotDamage, val)
                        break
            # track assist
            for method in ('getTrackAssistDamage', 'getTotalTrackAssistDamage',
                           'getImmobilizeAssistDamage'):
                fn = getattr(summaryEvent, method, None)
                if callable(fn):
                    val = int(fn() or 0)
                    if val > 0:
                        logger.debug('summaryFeedback: %s=%d', method, val)
                        self._battleAssistTrackDamage = max(self._battleAssistTrackDamage, val)
                        break
            # stun assist
            for method in ('getTotalStunDamage', 'getStunAssistDamage'):
                fn = getattr(summaryEvent, method, None)
                if callable(fn):
                    val = int(fn() or 0)
                    if val > 0:
                        logger.debug('summaryFeedback: %s=%d', method, val)
                        self._battleAssistStunDamage = max(self._battleAssistStunDamage, val)
                        break
            self._syncBattleLiveDamage()
        except Exception:
            logger.exception('summary feedback handling failed')

    def _onBattleFeedbackReceived(self, *args, **kwargs):
        if not (self._battleMode and self._battleTankID is not None):
            return
        try:
            sources = list(args)
            if kwargs:
                sources.append(kwargs)
            seenPayloads = set()
            for source in sources:
                self._processBattleFeedbackSource(source, seenPayloads)
        except Exception:
            logger.exception('battle feedback handling failed')

    def _processBattleFeedbackSource(self, source, seenPayloads=None):
        for payload in _feedbackPayloads(source):
            if seenPayloads is not None:
                marker = id(payload)
                if marker in seenPayloads:
                    continue
                seenPayloads.add(marker)

            directHandled = False
            try:
                fn = getattr(payload, 'getTotalDamage', None)
                if callable(fn):
                    val = int(fn() or 0)
                    if val > 0:
                        self.setBattleDirectDamage(val)
                        directHandled = True
            except Exception:
                pass
            try:
                fn = getattr(payload, 'getTotalStunDamage', None)
                if callable(fn):
                    val = int(fn() or 0)
                    if val > 0:
                        self.setBattleAssistDamage('stun', val)
                        directHandled = True
            except Exception:
                pass
            for attrName, kind in (('trackAssist', 'track'), ('radioAssist', 'spot')):
                try:
                    val = getattr(payload, attrName, None)
                    if val is None:
                        fn = getattr(payload, 'get' + attrName[0].upper() + attrName[1:], None)
                        if callable(fn):
                            val = fn()
                    if val is not None:
                        ival = int(val or 0)
                        if ival > 0:
                            self.setBattleAssistDamage(kind, ival)
                            directHandled = True
                except Exception:
                    pass
            if directHandled:
                continue

            summary = _readFeedbackSummary(payload)
            if summary is not None:
                self.setBattleDirectDamage(summary.get('direct', 0))
                self.setBattleAssistDamage('spot', summary.get('spot', 0))
                self.setBattleAssistDamage('track', summary.get('track', 0))
                self.setBattleAssistDamage('stun', summary.get('stun', 0))
                continue
            if _looksAssistFeedback(payload):
                spot = _readMaxIntByKeysRecursive(payload, _ASSIST_SPOT_KEYS)
                track = _readMaxIntByKeysRecursive(payload, _ASSIST_TRACK_KEYS)
                stun = _readMaxIntByKeysRecursive(payload, _ASSIST_STUN_KEYS)
                generic = _feedbackAmount(payload)
                kind = _assistKindFromFeedback(payload)
                if kind == 'track':
                    amount = track if track > 0 else generic
                elif kind == 'stun':
                    amount = stun if stun > 0 else generic
                else:
                    amount = spot if spot > 0 else generic
                if amount > 0:
                    self.setBattleAssistDamage(kind, amount)

    def _scheduleBattleStatsPoll(self):
        _cancelCallbackSafe(self._battleStatsPollCallbackId)
        self._battleStatsPollCallbackId = None
        return

    def _pollBattleStats(self):
        self._battleStatsPollCallbackId = None
        if not (self._battleMode and self._battleTankID is not None):
            return
        try:
            damage = self._readBattleStatsDamage()
            if damage > 0:
                self.setBattleLiveDamage(damage)
        except Exception:
            logger.exception('battle live stats poll failed')
        self._scheduleBattleStatsPoll()

    def _readBattleStatsDamage(self):
        try:
            player = BigWorld.player()
            arena = getattr(player, 'arena', None)
            playerVID = int(getattr(player, 'playerVehicleID', 0) or 0)
            accountDBID = int(getattr(player, 'databaseID', 0) or 0)
        except Exception:
            return 0
        if arena is None or not playerVID:
            return 0
        candidates = []
        for attr in ('statistics', 'vehicleStatistics', 'stats'):
            try:
                value = getattr(arena, attr, None)
                if value is not None:
                    candidates.append(value)
            except Exception:
                pass
        best = 0
        for source in candidates:
            try:
                if isinstance(source, dict):
                    for key in (playerVID, str(playerVID)):
                        if key in source:
                            value = _extractMarkDamage(source.get(key))
                            if value > best:
                                best = value
                    if best <= 0:
                        for value in source.itervalues():
                            vehicleID = 0
                            ownerDBID = 0
                            if isinstance(value, dict):
                                try:
                                    vehicleID = int(value.get('vehicleID', value.get('vehID', 0)) or 0)
                                except Exception:
                                    vehicleID = 0
                                try:
                                    ownerDBID = int(value.get('accountDBID', value.get('accountDBId', 0)) or 0)
                                except Exception:
                                    ownerDBID = 0
                            if vehicleID == playerVID or (accountDBID and ownerDBID == accountDBID):
                                damage = _extractMarkDamage(value)
                                if damage > best:
                                    best = damage
            except Exception:
                pass
        return int(best)

    def setBattleLiveDamage(self, damage):
        if not (self._battleMode and self._battleTankID is not None):
            return
        try:
            damage = int(damage or 0)
        except (TypeError, ValueError):
            return
        if damage <= self._battleLiveDamage:
            return
        self._battleLiveDamage = damage
        if self._battlePanelReady and self._battleInjectorView:
            self._pushBattleBadge()

    def setBattleDirectDamage(self, damage):
        if not (self._battleMode and self._battleTankID is not None):
            return
        try:
            damage = int(damage or 0)
        except (TypeError, ValueError):
            return
        if damage <= self._battleDirectDamage:
            return
        self._battleDirectDamage = damage
        self._syncBattleLiveDamage()

    def _syncBattleLiveDamage(self):
        # WoT С„РѕСЂРјСѓР»Р° РґР»СЏ РјС–С‚РєРё: direct + РЅР°Р№Р±С–Р»СЊС€РёР№ Р· С‚РёРїС–РІ Р°СЃРёСЃС‚Сѓ
        direct = int(self._battleDirectDamage)
        assist = int(max(
            self._battleAssistSpotDamage,
            self._battleAssistTrackDamage,
            self._battleAssistStunDamage
        ))
        total = int(direct + assist)
        self.setBattleLiveDamage(total)

    def setBattleAssistDamage(self, kind, damage):
        if not (self._battleMode and self._battleTankID is not None):
            return
        try:
            damage = int(damage or 0)
        except (TypeError, ValueError):
            return
        if damage <= 0:
            return
        if kind == 'track':
            if damage <= self._battleAssistTrackDamage:
                return
            self._battleAssistTrackDamage = damage
        elif kind == 'stun':
            if damage <= self._battleAssistStunDamage:
                return
            self._battleAssistStunDamage = damage
        else:
            if damage <= self._battleAssistSpotDamage:
                return
            self._battleAssistSpotDamage = damage
        self._syncBattleLiveDamage()

    def addBattleAssistDamage(self, kind, damage):
        self.setBattleAssistDamage(kind, damage)

    def _processBattleSummaryData(self, summaryData):
        """РћР±СЂРѕР±Р»СЏС” РїС–РґСЃСѓРјРєРѕРІС– РґР°РЅС– Р±РѕСЋ Р· С…СѓРєР° handleBattleEventsSummary.
        Summary РґР°РЅС– Р°РІС‚РѕСЂРёС‚РµС‚РЅС– вЂ” РїРµСЂРµР·Р°РїРёСЃСѓС”РјРѕ Р°РєСѓРјСѓР»СЏС‚РѕСЂРё."""
        if not (self._battleMode and self._battleTankID is not None):
            return
        if not isinstance(summaryData, dict):
            return
        damage = summaryData.get('damage', 0)
        if damage > 0:
            self._battleDirectDamage = max(self._battleDirectDamage, int(damage))
        track = summaryData.get('trackAssist', 0)
        if track > 0:
            self._battleAssistTrackDamage = max(self._battleAssistTrackDamage, int(track))
        spot = summaryData.get('radioAssist', 0)
        if spot > 0:
            self._battleAssistSpotDamage = max(self._battleAssistSpotDamage, int(spot))
        stun = summaryData.get('stunAssist', 0)
        if stun > 0:
            self._battleAssistStunDamage = max(self._battleAssistStunDamage, int(stun))
        self._syncBattleLiveDamage()
        logger.debug('battle summary hook: damage=%d track=%d spot=%d stun=%d total=%d',
                     damage, track, spot, stun, self._battleLiveDamage)

    def addBattleLiveDamage(self, damage):
        if not (self._battleMode and self._battleTankID is not None):
            return
        try:
            damage = int(damage or 0)
        except (TypeError, ValueError):
            return
        if damage <= 0:
            return
        self._battleDirectDamage += damage
        self._syncBattleLiveDamage()

    def _onViewModeChanged(self, mode):
        try:
            self._viewMode = int(mode)
            self._scheduleSaveCache()
            logger.debug('view mode changed: %s', self._viewMode)
        except Exception:
            self._viewMode = _DEFAULT_VIEW_MODE

    def _onExpandToggle(self):
        self._detailOpen = not self._detailOpen
        logger.debug('detail toggle -> %s', self._detailOpen)
        if self._detailOpen:
            self._pushDetail()
        if self._injectorView:
            try:
                self._injectorView.flashObject.as_showDetail(bool(self._detailOpen))
            except Exception:
                logger.exception('as_showDetail failed')

    def _onMarkBadgeToggle(self, value):
        self._markBadgeOpen = bool(value)
        self._scheduleSaveCache()
        logger.debug('mark badge toggle -> %s', self._markBadgeOpen)

    def _onMarkBadgeOffsetChanged(self, offset):
        try:
            self._markBadgeOffset = [int(offset[0]), int(offset[1])]
            self._scheduleSaveCache()
            logger.debug('mark badge offset -> %s', self._markBadgeOffset)
        except Exception:
            logger.exception('mark badge offset save failed')

    def _onBattleBadgeOffsetChanged(self, offset):
        try:
            self._battleBadgeOffset = [int(offset[0]), int(offset[1])]
            self._scheduleSaveCache()
            logger.debug('battle badge offset -> %s', self._battleBadgeOffset)
        except Exception:
            logger.exception('battle badge offset save failed')

    def _pushDetail(self):
        if not (self._panelReady and self._injectorView):
            return
        if not g_currentVehicle.isPresent():
            return

        tankID = getattr(g_currentVehicle.item, 'intCD', None)
        if tankID is None:
            return
        
        tankName = u''
        try:
            tankName = unicode(getattr(g_currentVehicle.item, 'shortUserName', None)
                               or getattr(g_currentVehicle.item, 'userName', None)
                               or u'')
        except Exception:
            tankName = u''

        flag = _getNationFlag(g_currentVehicle.item)

        currentMark = self._readLiveMarkForTank(tankID)
        if currentMark is None:
            currentMark = self._getLastKnownMark(tankID)
        if currentMark is None:
            currentMark = 0.0
        try:
            currentMark = float(currentMark)
        except (TypeError, ValueError):
            currentMark = 0.0
            
        stars = 0
        if currentMark >= 95.0:
            stars = 3
        elif currentMark >= 85.0:
            stars = 2
        elif currentMark >= 65.0:
            stars = 1

        history = self._getHistoryForTank(tankID)
        windowed = history[-_MAX_HISTORY:]
        n = len(windowed)
        totalBattles = _readBattlesCountForTank(tankID)
        if totalBattles <= 0:
            totalBattles = n

        entries = []
        for i, entry in enumerate(windowed):
            battleNum = totalBattles - (n - 1 - i)
            if battleNum < 1:
                battleNum = i + 1
            if not isinstance(entry, dict):
                try:
                    val = float(entry)
                except (TypeError, ValueError):
                    continue
                entries.append({
                    'value': val,
                    'dmg':   -1,
                    'delta': 0.0,
                    'num':   battleNum,
                })
                continue
            if entry.get('provisional'):
                continue
            try:
                val = float(entry.get('value', 0.0))
            except (TypeError, ValueError):
                continue
            try:
                delta = float(entry.get('delta', 0.0))
            except (TypeError, ValueError):
                delta = 0.0
            try:
                battleNum = int(entry.get('num', battleNum) or battleNum)
            except (TypeError, ValueError):
                pass
            dmg_raw = entry.get('damage', entry.get('dmg', None))
            try:
                dmg = int(dmg_raw) if dmg_raw is not None else -1
            except (TypeError, ValueError):
                dmg = -1
            entries.append({
                'value': val,
                'dmg':   dmg,
                'delta': delta,
                'num':   battleNum,
            })

        try:
            self._injectorView.flashObject.as_setDetailTankInfo(
                tankName, flag, int(stars), float(currentMark))
            self._injectorView.flashObject.as_setDetailBattles(entries)
        except Exception:
            logger.exception('push detail failed')

    _EMPTY_XP  = {'thirdClass': 0, 'secondClass': 0, 'firstClass': 0, 'aceTanker': 0}
    _EMPTY_MOE = {
        'p20': 0, 'p40': 0, 'p55': 0, 'p65': 0,
        'p75': 0, 'p85': 0, 'p95': 0, 'p100': 0,
    }

    def _loadCache(self):
        _ensureCacheDir()
        if not os.path.isfile(_CACHE_FILE):
            return
        try:
            with open(_CACHE_FILE, 'rb') as fh:
                raw = fh.read()
                cached, version = cPickle.loads(zlib.decompress(raw))
                if not isinstance(cached, dict):
                    logger.debug('cache: bad payload type, discarding')
                    return
                if version == _CACHE_VERSION:
                    self._xpCache    = cached.get('xp',    {}) or {}
                    self._moeCache   = cached.get('moe',   {}) or {}
                    self._xpCacheTs  = cached.get('xpTs',  {}) or {}
                    self._moeCacheTs = cached.get('moeTs', {}) or {}
                    pos = cached.get('position')
                    if isinstance(pos, (list, tuple)) and len(pos) >= 2:
                        try:
                            self._position = [int(pos[0]), int(pos[1])]
                        except (TypeError, ValueError):
                            pass
                    try:
                        self._viewMode = int(cached.get('viewMode', _DEFAULT_VIEW_MODE))
                    except (TypeError, ValueError):
                        self._viewMode = _DEFAULT_VIEW_MODE
                    self._markBadgeOpen = bool(cached.get('markBadgeOpen', True))
                    self._battleBadgeEnabled = bool(cached.get('battleBadgeEnabled', True))
                    self._cachedBadgeStyle = cached.get('badgeStyle')
                    badgePos = cached.get('markBadgeOffset')
                    if isinstance(badgePos, (list, tuple)) and len(badgePos) >= 2:
                        try:
                            ox, oy = int(badgePos[0]), int(badgePos[1])
                            if ox >= 0 or oy >= 0:
                                self._markBadgeOffset = [ox, oy]
                        except (TypeError, ValueError):
                            pass
                    battleBadgePos = cached.get('battleBadgeOffset')
                    if isinstance(battleBadgePos, (list, tuple)) and len(battleBadgePos) >= 2:
                        try:
                            ox, oy = int(battleBadgePos[0]), int(battleBadgePos[1])
                            if ox >= 0 or oy >= 0:
                                self._battleBadgeOffset = [ox, oy]
                        except (TypeError, ValueError):
                            pass
                    self._markHistory   = cached.get('markHistory',   {}) or {}
                    self._lastKnownMark = cached.get('lastKnownMark', {}) or {}
                    self._lastKnownMarkStats = cached.get('lastKnownMarkStats', {}) or {}
                    logger.debug('cache loaded v%s: %d xp, %d moe, mode=%s, pos=%s, history-accounts=%d',
                                 version, len(self._xpCache), len(self._moeCache),
                                 self._viewMode, self._position, len(self._markHistory))
                else:
                    self._xpCache    = cached.get('xp',    {}) or {}
                    self._moeCache   = cached.get('moe',   {}) or {}
                    self._xpCacheTs  = cached.get('xpTs',  {}) or {}
                    self._moeCacheTs = cached.get('moeTs', {}) or {}
                    pos = cached.get('position')
                    if isinstance(pos, (list, tuple)) and len(pos) >= 2:
                        try:
                            self._position = [int(pos[0]), int(pos[1])]
                        except (TypeError, ValueError):
                            pass
                    self._viewMode = _DEFAULT_VIEW_MODE
                    self._markBadgeOpen = bool(cached.get('markBadgeOpen', True))
                    self._battleBadgeEnabled = bool(cached.get('battleBadgeEnabled', True))
                    self._cachedBadgeStyle = cached.get('badgeStyle')
                    badgePos = cached.get('markBadgeOffset')
                    if isinstance(badgePos, (list, tuple)) and len(badgePos) >= 2:
                        try:
                            ox, oy = int(badgePos[0]), int(badgePos[1])
                            if ox >= 0 or oy >= 0:
                                self._markBadgeOffset = [ox, oy]
                        except (TypeError, ValueError):
                            pass
                    battleBadgePos = cached.get('battleBadgeOffset')
                    if isinstance(battleBadgePos, (list, tuple)) and len(battleBadgePos) >= 2:
                        try:
                            ox, oy = int(battleBadgePos[0]), int(battleBadgePos[1])
                            if ox >= 0 or oy >= 0:
                                self._battleBadgeOffset = [ox, oy]
                        except (TypeError, ValueError):
                            pass
                    self._markHistory   = cached.get('markHistory',   {}) or {}
                    self._lastKnownMark = cached.get('lastKnownMark', {}) or {}
                    self._lastKnownMarkStats = cached.get('lastKnownMarkStats', {}) or {}
                    logger.debug('cache: migrated v%s -> v%s, kept %d xp/%d moe and %d history accounts',
                                 version, _CACHE_VERSION, len(self._xpCache), len(self._moeCache),
                                 len(self._markHistory))
        except Exception:
            logger.exception('cache: failed to load')

    def _loadConfig(self):
        config = _loadConfigFile()
        modeName = _safeLower(config.get('mode'))
        if modeName not in _CONFIG_MODES:
            modeName = _CONFIG_DEFAULTS['mode']
        self._configEnabled = True
        self._configGaragePanelMode = int(_CONFIG_MODES.get(modeName, _DEFAULT_VIEW_MODE))
        self._configMarkBadge = (modeName in ('both', 'marks', 'mark'))
        self._configPanelBodyVisible = (modeName not in ('marks', 'mark'))
        self._viewMode = self._configGaragePanelMode
        styleName = _safeLower(config.get('badgeStyle'))
        if styleName not in _CONFIG_BADGE_STYLES:
            styleName = _CONFIG_DEFAULTS['badgeStyle']
        self._configBadgeStyle = int(_CONFIG_BADGE_STYLES.get(styleName, 0))
        try:
            cachedBadgeStyle = int(self._cachedBadgeStyle)
        except (TypeError, ValueError):
            cachedBadgeStyle = None
        if cachedBadgeStyle != self._configBadgeStyle:
            self._markBadgeOpen = True
            self._battleBadgeEnabled = True
            self._cachedBadgeStyle = self._configBadgeStyle
        logger.debug('config loaded: mode=%s viewMode=%s panelBody=%s markBadge=%s badgeStyle=%s(%d)',
                     modeName, self._viewMode,
                     self._configPanelBodyVisible, self._configMarkBadge,
                     styleName, self._configBadgeStyle)

    def _scheduleSaveCache(self):
        self._saveRev += 1
        rev = self._saveRev
        _cancelCallbackSafe(self._saveCallbackId)
        self._saveCallbackId = BigWorld.callback(_CACHE_SAVE_DEBOUNCE, lambda: self._saveCache(rev))

    def _saveCache(self, rev=None):
        self._saveCallbackId = None
        if rev is not None and rev != self._saveRev:
            return
        try:
            if not os.path.isdir(_CACHE_DIR):
                os.makedirs(_CACHE_DIR)
            payload = {
                'xp':            self._xpCache,
                'moe':           self._moeCache,
                'xpTs':          self._xpCacheTs,
                'moeTs':         self._moeCacheTs,
                'position':      list(self._position),
                'viewMode':      self._viewMode,
                'badgeStyle':    int(self._configBadgeStyle),
                'markBadgeOpen': self._markBadgeOpen,
                'battleBadgeEnabled': self._battleBadgeEnabled,
                'markBadgeOffset': list(self._markBadgeOffset),
                'battleBadgeOffset': list(self._battleBadgeOffset),
                'markHistory':   self._markHistory,
                'lastKnownMark': self._lastKnownMark,
                'lastKnownMarkStats': self._lastKnownMarkStats,
            }
            raw = zlib.compress(cPickle.dumps((payload, _CACHE_VERSION), cPickle.HIGHEST_PROTOCOL), 1)
            with open(_CACHE_FILE, 'wb') as fh:
                fh.write(raw)
            logger.debug('cache saved: %d xp, %d moe, mode=%s',
                         len(self._xpCache), len(self._moeCache), self._viewMode)
        except Exception:
            logger.exception('cache: failed to save')

    def _isFresh(self, tankID, distribution):
        tsMap = self._xpCacheTs if distribution == 'xp' else self._moeCacheTs
        if distribution != 'xp':
            moe = _dictGetTank(self._moeCache, tankID)
            if moe is not None and not _hasFullMoeRequirements(moe):
                return False
        ts = _dictGetTank(tsMap, tankID, 0)
        try:
            return (time.time() - float(ts)) < _CACHE_TTL_SECONDS
        except (TypeError, ValueError):
            return False

    def _scheduleRefresh(self, delay=0.5):
        """РџР»Р°РЅСѓС” РѕРґРёРЅ РІС–РґРєР»Р°РґРµРЅРёР№ _refresh, СЃРєР°СЃРѕРІСѓСЋС‡Рё РїРѕРїРµСЂРµРґРЅС–Р№.
        Р—Р°РїРѕР±С–РіР°С” С€С‚РѕСЂРјСѓ РІРёРєР»РёРєС–РІ РєРѕР»Рё РєС–Р»СЊРєР° РґР¶РµСЂРµР» РѕРґРЅРѕС‡Р°СЃРЅРѕ РїР»Р°РЅСѓСЋС‚СЊ refresh."""
        _cancelCallbackSafe(self._refreshCallbackId)
        self._refreshCallbackId = BigWorld.callback(delay, self._doScheduledRefresh)

    def _doScheduledRefresh(self):
        self._refreshCallbackId = None
        self._refresh()

    def _startRoutePolling(self):
        """Р—Р°РїСѓСЃРєР°С” polling route РєРѕР¶РЅС– 0.5СЃ С‰РѕР± С…РѕРІР°С‚Рё РїР°РЅРµР»СЊ РїСЂРё overlay-РµРєСЂР°РЅР°С…."""
        _cancelCallbackSafe(getattr(self, '_routePollCallbackId', None))
        self._routePollCallbackId = BigWorld.callback(0.3, self._pollRoute)

    def _pollRoute(self):
        self._routePollCallbackId = None
        if not (self._enabled and not self._battleMode and self._panelReady):
            return
        try:
            lsm = getLobbyStateMachine()
            if lsm is not None:
                routeInfo = lsm.visibleRouteInfo
                routeText = self._routeText(routeInfo)
                isPostBattle = 'postbattle' in routeText or 'post_battle' in routeText
                isHangar = (not isPostBattle and self._isHangarState(routeInfo.state))
                if isHangar != self._hangarVisible:
                    self._hangarVisible = isHangar
                    self._lastVisibleState = None
                    self._updateVisibility()
        except Exception:
            pass
        # РџСЂРѕРґРѕРІР¶СѓС”РјРѕ polling РїРѕРєРё РІ Р»РѕР±С–
        self._startRoutePolling()

    def _scheduleGarageVehicleRetry(self):
        if not (self._enabled and self._hangarVisible and not self._battleMode):
            return
        if self._garageVehicleRetryAttempt >= 40:
            logger.debug('refresh retry: gave up waiting for current vehicle')
            return
        self._garageVehicleRetryAttempt += 1
        delay = 0.25 if self._garageVehicleRetryAttempt < 8 else 0.75
        logger.debug('refresh retry: current vehicle not ready, attempt=%d delay=%.2f',
                     self._garageVehicleRetryAttempt, delay)
        self._scheduleRefresh(delay)

    def _refresh(self):
        if not (self._panelReady and self._injectorView):
            return

        if not g_currentVehicle.isPresent():
            logger.debug('refresh: current vehicle is not ready')
            self._visibleByData = False
            self._updateVisibility()
            try:
                self._injectorView.flashObject.as_clearData()
            except Exception:
                pass
            self._scheduleGarageVehicleRetry()
            return
        tankID = _tankKey(getattr(g_currentVehicle.item, 'intCD', None))
        if tankID is None:
            logger.debug('refresh: current vehicle has no intCD')
            self._visibleByData = False
            self._updateVisibility()
            try:
                self._injectorView.flashObject.as_clearData()
            except Exception:
                pass
            self._scheduleGarageVehicleRetry()
            return
        self._garageVehicleRetryAttempt = 0
        tankLevel = 0
        try:
            tankLevel = getattr(g_currentVehicle.item, 'level', 0)
        except Exception:
            pass
        if not tankLevel:
            tankLevel = _getTankLevelByCD(tankID)

        if tankLevel and tankLevel < _MIN_TANK_LEVEL:
            logger.debug('refresh: hiding panel, tank level %d < %d', tankLevel, _MIN_TANK_LEVEL)
            self._visibleByData = False
            self._updateVisibility()
            try:
                self._injectorView.flashObject.as_clearData()
            except Exception:
                pass
            return

        self._visibleByData = True
        self._updateVisibility()
        logger.debug('refresh: tankID=%s visibleByData=True hangarVisible=%s',
                     tankID, self._hangarVisible)
        self._capturePreBattleStats(tankID)

        xp  = _dictGetTank(self._xpCache, tankID)
        moe = _dictGetTank(self._moeCache, tankID)
        xpFresh  = xp  is not None and self._isFresh(tankID, 'xp')
        moeFresh = moe is not None and self._isFresh(tankID, 'damage')
        if xp is None and moe is None:
            try:
                self._injectorView.flashObject.as_setLoading()
            except Exception:
                pass
        if xp is not None:
            self._pushMastery(xp)
        if not xpFresh:
            self._requestDistribution(tankID, 'xp')
        if moe is not None:
            self._pushMoe(moe)
        if not moeFresh:
            self._requestDistribution(tankID, 'damage')
        self._pushHistory(tankID)

    def _pushMastery(self, xp):
        if not self._injectorView:
            return
        try:
            self._injectorView.flashObject.as_setMasteryData(
                int(xp.get('thirdClass')  or 0),
                int(xp.get('secondClass') or 0),
                int(xp.get('firstClass')  or 0),
                int(xp.get('aceTanker')   or 0),
            )
        except Exception:
            logger.exception('as_setMasteryData failed')

    def _pushMoe(self, moe):
        if not self._injectorView:
            return
        try:
            self._injectorView.flashObject.as_setMoeData(
                int(moe.get('p65')  or 0),
                int(moe.get('p85')  or 0),
                int(moe.get('p95')  or 0),
                int(moe.get('p100') or 0),
            )
        except Exception:
            logger.exception('as_setMoeData failed')

    def _pushHistory(self, tankID):
        if not self._injectorView:
            return

        values = []
        try:
            history = self._getHistoryForTank(tankID)[-_MAX_HISTORY:]
        except Exception:
            history = []

        for entry in history:
            if isinstance(entry, dict):
                if entry.get('provisional'):
                    continue
                try:
                    values.append(float(entry.get('value', 0.0)))
                except (TypeError, ValueError):
                    continue
            else:
                try:
                    values.append(float(entry))
                except (TypeError, ValueError):
                    continue

        current = self._readLiveMarkForTank(tankID)

        if current is None:
            current = self._getLastKnownMark(tankID)

        if current is not None:
            try:
                current_f = float(current)
                if not self._hasPendingSnapshot(tankID):
                    self._setLastKnownMark(tankID, current_f)
                if not values or abs(values[-1] - current_f) > 0.0001:
                    values.append(current_f)
                current = current_f
            except (TypeError, ValueError):
                current = None

        try:
            self._injectorView.flashObject.as_setBattleHistory(
                values,
                float(current if current is not None else 0.0)
            )
            self._injectorView.flashObject.as_setLastBattleDamage(
                int(self._getCurrentMarkDamage(tankID, current))
            )
            # РўРѕР№ СЃР°РјРёР№ fallback-Р»Р°РЅС†СЋР¶РѕРє С‰Рѕ С– РІ _pushBattleBadge
            _marks = _readGunMarksForTank(tankID)
            if _marks < 0:
                _marks = self._getCachedMarksOnGun(tankID)
            if _marks < 0:
                _mark_val = float(current if current is not None else 0.0)
                _marks = 3 if _mark_val >= 95.0 else (2 if _mark_val >= 85.0 else (1 if _mark_val >= 65.0 else 0))
            self._injectorView.flashObject.as_setMarkBadgeStars(
                int(_marks)
            )
        except Exception:
            logger.exception('as_setBattleHistory failed')

    def _requestDistribution(self, tankID, distribution, attempt=1):
        isXp    = (distribution == 'xp')
        pending = self._pendingXp if isXp else self._pendingMoe
        if attempt == 1:
            if tankID in pending:
                return
            pending.add(tankID)
        query = _XP_PERCENTILES_QUERY if isXp else _MOE_PERCENTILES_QUERY
        url   = _buildApiUrl(tankID, distribution, query)
        logger.debug('api request tankID=%s dist=%s attempt=%d url=%s',
                     tankID, distribution, attempt, url)
        try:
            BigWorld.fetchURL(
                url,
                lambda response, t=tankID, d=distribution, a=attempt: self._onApiResponse(t, d, response, a),
                None, _API_TIMEOUT, 'GET', None,
            )
        except Exception:
            logger.exception('fetchURL failed tankID=%s dist=%s attempt=%d',
                             tankID, distribution, attempt)
            self._handleApiFailure(tankID, distribution, attempt)

    def _retryRequest(self, tankID, distribution, attempt):
        if not self._enabled:
            pending = self._pendingXp if distribution == 'xp' else self._pendingMoe
            pending.discard(tankID)
            return
        self._requestDistribution(tankID, distribution, attempt)

    def _handleApiFailure(self, tankID, distribution, attempt):
        isXp    = (distribution == 'xp')
        pending = self._pendingXp if isXp else self._pendingMoe
        if attempt < _API_MAX_ATTEMPTS:
            delay = _API_RETRY_BASE_DELAY * (2 ** (attempt - 1))
            nextAttempt = attempt + 1
            logger.debug('api retry tankID=%s dist=%s in %.1fs (next attempt=%d)',
                         tankID, distribution, delay, nextAttempt)
            BigWorld.callback(delay, lambda: self._retryRequest(tankID, distribution, nextAttempt))
            return
        pending.discard(tankID)
        logger.debug('api: gave up tankID=%s dist=%s after %d attempts',
                     tankID, distribution, attempt)
        current = g_currentVehicle.item if g_currentVehicle.isPresent() else None
        isCurrent = current is not None and getattr(current, 'intCD', None) == tankID
        if isCurrent and _dictGetTank(self._xpCache, tankID) is None and _dictGetTank(self._moeCache, tankID) is None:
            empty = self._EMPTY_XP if isXp else self._EMPTY_MOE
            (self._pushMastery if isXp else self._pushMoe)(empty)

    def _onApiResponse(self, tankID, distribution, response, attempt=1):
        isXp    = (distribution == 'xp')
        mapping = _PERCENTILE_TO_KEY if isXp else _MOE_PERCENTILE_TO_KEY
        pending = self._pendingXp if isXp else self._pendingMoe
        parsed = None
        status = 0
        try:
            body = getattr(response, 'body', None)
            status = getattr(response, 'responseCode', 0)
            if body and status and status < 400:
                payload = json.loads(body)
                parsed = _parseApiResponse(payload, tankID, mapping)
        except Exception:
            logger.exception('api parse failed tankID=%s dist=%s attempt=%d',
                             tankID, distribution, attempt)
        if parsed is None:
            isTransient = (not status) or status >= 500 or status == 429
            if isTransient and attempt < _API_MAX_ATTEMPTS:
                self._handleApiFailure(tankID, distribution, attempt)
                return
            pending.discard(tankID)
            logger.debug('api: no data tankID=%s dist=%s status=%s', tankID, distribution, status)
            current = g_currentVehicle.item if g_currentVehicle.isPresent() else None
            isCurrent = current is not None and getattr(current, 'intCD', None) == tankID
            if isCurrent and _dictGetTank(self._xpCache, tankID) is None and _dictGetTank(self._moeCache, tankID) is None:
                empty = self._EMPTY_XP if isXp else self._EMPTY_MOE
                (self._pushMastery if isXp else self._pushMoe)(empty)
            return
        pending.discard(tankID)
        nowTs = int(time.time())
        if isXp:
            self._xpCache[_tankKey(tankID)]   = parsed
            self._xpCacheTs[_tankKey(tankID)] = nowTs
        else:
            self._moeCache[_tankKey(tankID)]   = parsed
            self._moeCacheTs[_tankKey(tankID)] = nowTs
        self._scheduleSaveCache()
        current = g_currentVehicle.item if g_currentVehicle.isPresent() else None
        isCurrent = current is not None and getattr(current, 'intCD', None) == tankID
        if isCurrent:
            (self._pushMastery if isXp else self._pushMoe)(parsed)
        if self._battleMode and self._battleTankID == tankID and not isXp:
            self._pushBattleBadge()

    def _onModsSettingsChanged(self, isOpen):
        newState = bool(isOpen)
        if self._modsSettingsOpen == newState:
            return
        self._modsSettingsOpen = newState
        logger.debug('modsSettings state -> %s', self._modsSettingsOpen)
        self._updateVisibility()

    def _bindPrbDispatcher(self):
        if self._prbDispatcherBound:
            return
        try:
            from gui.prb_control.dispatcher import g_prbLoader
            dispatcher = g_prbLoader.getDispatcher()
            if dispatcher is None:
                return
            dispatcher.onPrbEntitySwitched += self._onPrbEntitySwitched
            self._prbDispatcherBound = True
            self._refreshQueueMode()
        except Exception:
            logger.exception('failed to bind prb dispatcher')

    def _unbindPrbDispatcher(self):
        if not self._prbDispatcherBound:
            return
        try:
            from gui.prb_control.dispatcher import g_prbLoader
            dispatcher = g_prbLoader.getDispatcher()
            if dispatcher is not None:
                dispatcher.onPrbEntitySwitched -= self._onPrbEntitySwitched
        except Exception:
            pass
        self._prbDispatcherBound = False

    def _onPrbEntitySwitched(self, *_):
        self._refreshQueueMode()

    def _refreshQueueMode(self):
        allowed = self._isQueueModeAllowed()
        if allowed == self._queueModeAllowed:
            return
        self._queueModeAllowed = allowed
        logger.debug('queue mode allowed=%s', allowed)
        self._updateVisibility()

    def _isQueueModeAllowed(self):
        if self._isStrongholdPrbActive():
            return False
        try:
            from gui.Scaleform.daapi.view.lobby.header import battle_selector_items
            items = battle_selector_items.getItems()
        except Exception:
            return True
        if items is None:
            return True
        selected = None
        for attrName in ('getSelected', 'getSelectedItem', 'getCurrent', 'getCurrentItem'):
            try:
                getter = getattr(items, attrName, None)
                if getter is not None:
                    selected = getter()
                    if selected is not None:
                        break
            except Exception:
                selected = None
        if selected is None:
            return True
        try:
            mode_id = selected.getID() if hasattr(selected, 'getID') else None
        except Exception:
            mode_id = None
        modeText = _safeLower(mode_id)
        if any(marker in modeText for marker in _STRONGHOLD_MODE_MARKERS):
            return False
        return mode_id in _GARAGE_ALLOWED_QUEUE_MODES

    def _isStrongholdPrbActive(self):
        try:
            from gui.prb_control.dispatcher import g_prbLoader
            dispatcher = g_prbLoader.getDispatcher()
            if dispatcher is None:
                return False
            entity = dispatcher.getEntity()
        except Exception:
            return False
        if entity is None:
            return False
        try:
            entityType = entity.getEntityType()
        except Exception:
            entityType = None
        try:
            prebattleType = getattr(constants, 'PREBATTLE_TYPE', None)
            strongholdTypes = []
            for attrName in _STRONGHOLD_PRB_TYPE_NAMES:
                val = getattr(prebattleType, attrName, None) if prebattleType is not None else None
                if val is not None:
                    strongholdTypes.append(val)
            if entityType in strongholdTypes:
                return True
        except Exception:
            pass
        cls = getattr(entity, '__class__', None)
        if cls is not None:
            clsText = (_safeLower(getattr(cls, '__module__', '')) + ' ' +
                       _safeLower(getattr(cls, '__name__', '')))
            if any(marker in clsText for marker in _STRONGHOLD_MODE_MARKERS):
                return True
        for attrName in ('getStrongholdSettings', 'getStrongholdData', 'getStrongholdState'):
            try:
                getter = getattr(entity, attrName, None)
                data = getter() if getter is not None else None
                if data is None:
                    continue
                isValid = getattr(data, 'isValid', None)
                if isValid is None or isValid():
                    return True
            except Exception:
                pass
        return False

    def onStrongholdBrowserOpened(self, browserID, url):
        key = _browserKey(browserID)
        if key is not None:
            self._strongholdBrowserIDs.discard(_STRONGHOLD_BROWSER_UNKNOWN_ID)
            self._strongholdBrowserIDs.add(key)
        else:
            self._strongholdBrowserIDs.add(_STRONGHOLD_BROWSER_UNKNOWN_ID)
        if not self._strongholdScreenOpen:
            self._strongholdScreenOpen = True
            logger.debug('stronghold browser opened id=%s url=%s', browserID, url)
            self._updateVisibility()

    def onStrongholdBrowserClosed(self, browserID=None, url=None):
        key = _browserKey(browserID)
        if key is not None:
            self._strongholdBrowserIDs.discard(key)
            self._strongholdBrowserIDs.discard(_STRONGHOLD_BROWSER_UNKNOWN_ID)
        elif url is None or _isStrongholdGarageUrl(url):
            self._strongholdBrowserIDs.clear()
        newState = bool(self._strongholdBrowserIDs)
        if self._strongholdScreenOpen != newState:
            self._strongholdScreenOpen = newState
            logger.debug('stronghold browser closed id=%s active=%d',
                         browserID, len(self._strongholdBrowserIDs))
            self._updateVisibility()

    def _onDragEnd(self, offset):
        try:
            self._position = [int(offset[0]), int(offset[1])]
            self._scheduleSaveCache()
            logger.debug('drag end pos=%s', self._position)
        except Exception:
            logger.exception('drag save failed')


class _BattleResultsCollector(object):

    _TICK_INTERVAL = 1.0
    _MAX_GATE_ATTEMPTS = 30
    _MAX_RESPONSE_ATTEMPTS = 30
    _MAX_DOSSIER_ATTEMPTS = 20
    _DOSSIER_FIRST_DELAY = 0.5
    _DOSSIER_RETRY_DELAY = 1.5

    def __init__(self, controller):
        self._controller = controller
        self._queue = deque()
        self._available = False
        self._terminated = False
        self._installed = False
        self._tickCallbackId = None
        self._dossierCallbackIds = {}

    def init(self):
        if self._installed:
            return
        if g_messengerEvents is None or SYS_MESSAGE_TYPE is None:
            logger.debug('battle-results: messenger API unavailable, collector disabled')
            return
        try:
            g_messengerEvents.serviceChannel.onChatMessageReceived += self._onServiceMessage
        except Exception:
            logger.exception('battle-results: serviceChannel hook failed')
            return
        try:
            g_playerEvents.onAccountBecomeNonPlayer += self._onBecomeNonPlayer
        except Exception:
            pass
        if g_eventBus is not None and GUICommonEvent is not None:
            try:
                g_eventBus.addListener(GUICommonEvent.LOBBY_VIEW_LOADED, self._onLobbyLoaded)
            except Exception:
                logger.exception('battle-results: LOBBY_VIEW_LOADED subscribe failed')
        self._installed = True
        self._terminated = False
        self._scheduleTick()
        logger.debug('battle-results: collector started')

    def fini(self):
        self._terminated = True
        _cancelCallbackSafe(self._tickCallbackId)
        self._tickCallbackId = None
        for record in list(self._dossierCallbackIds.values()):
            try:
                _cancelCallbackSafe(record[0])
            except Exception:
                pass
        self._dossierCallbackIds.clear()
        if not self._installed:
            return
        try:
            g_messengerEvents.serviceChannel.onChatMessageReceived -= self._onServiceMessage
        except Exception:
            pass
        try:
            g_playerEvents.onAccountBecomeNonPlayer -= self._onBecomeNonPlayer
        except Exception:
            pass
        if g_eventBus is not None and GUICommonEvent is not None:
            try:
                g_eventBus.removeListener(GUICommonEvent.LOBBY_VIEW_LOADED, self._onLobbyLoaded)
            except Exception:
                pass
        self._queue.clear()
        self._installed = False
        self._available = False

    def _onLobbyLoaded(self, *_):
        self.onAccountShowGUI()

    def onAccountShowGUI(self):
        self._available = True

    def _onBecomeNonPlayer(self, *_):
        self._available = False

    def _onServiceMessage(self, _client, message):
        try:
            if not self._isBattleResultMessage(message):
                return
            data = getattr(message, 'data', None) or {}
            try:
                arenaID = int(data.get('arenaUniqueID', 0) or 0)
            except (TypeError, ValueError):
                return
            if arenaID <= 0:
                return
            for queued in self._queue:
                if queued[0] == arenaID:
                    return
            self._queue.append((arenaID, 0))
            logger.debug('battle-results: arena %s queued', arenaID)
        except Exception:
            logger.exception('battle-results: onServiceMessage failed')

    @staticmethod
    def _isBattleResultMessage(message):
        messageType = getattr(message, 'type', None)
        if messageType is None or SYS_MESSAGE_TYPE is None:
            return False
        try:
            name = str(SYS_MESSAGE_TYPE[messageType])
        except (KeyError, TypeError, ValueError):
            return False
        return name == 'battleResults'

    def _scheduleTick(self):
        if self._terminated:
            return
        _cancelCallbackSafe(self._tickCallbackId)
        self._tickCallbackId = BigWorld.callback(self._TICK_INTERVAL, self._tick)

    def _tick(self):
        self._tickCallbackId = None
        if self._terminated:
            return
        try:
            if self._available and self._queue:
                arenaID, attempt = self._queue.popleft()
                self._processOne(arenaID, attempt)
        except Exception:
            logger.exception('battle-results: tick failed')
        self._scheduleTick()

    def _processOne(self, arenaID, attempt):
        try:
            player = BigWorld.player()
            if not isinstance(player, PlayerAccount):
                self._requeueOrDrop(arenaID, attempt, 'no PlayerAccount')
                return
            try:
                synced = ServicesLocator.itemsCache.isSynced()
            except Exception:
                synced = False
            if not synced:
                self._requeueOrDrop(arenaID, attempt, 'itemsCache not synced')
                return
            cache = getattr(player, 'battleResultsCache', None)
            if cache is None:
                logger.debug('battle-results: arena %s no battleResultsCache, drop', arenaID)
                return
            cache.get(arenaID, functools.partial(self._onResults, arenaID, attempt))
        except Exception:
            logger.exception('battle-results: processOne failed arena %s', arenaID)

    def _requeueOrDrop(self, arenaID, attempt, reason):
        if attempt < self._MAX_GATE_ATTEMPTS:
            self._queue.append((arenaID, attempt + 1))
            logger.debug('battle-results: gate wait (%s) arena %s (%d/%d)',
                         reason, arenaID, attempt + 1, self._MAX_GATE_ATTEMPTS)
        else:
            logger.debug('battle-results: dropping arena %s (gate %s exhausted)',
                         arenaID, reason)

    def _onResults(self, arenaID, attempt, responseCode, results=None):
        try:
            if responseCode is None or responseCode < 0:
                if attempt < self._MAX_RESPONSE_ATTEMPTS:
                    self._queue.append((arenaID, attempt + 1))
                    logger.debug('battle-results: arena %s retry rc=%s (%d/%d)',
                                 arenaID, responseCode, attempt + 1, self._MAX_RESPONSE_ATTEMPTS)
                else:
                    logger.debug('battle-results: arena %s gave up after %d attempts rc=%s',
                                 arenaID, attempt, responseCode)
                return
            if not results:
                logger.debug('battle-results: arena %s empty results rc=%s, drop',
                             arenaID, responseCode)
                return
            self._extractAndApply(arenaID, results)
        except Exception:
            logger.exception('battle-results: onResults failed arena %s', arenaID)

    def _extractAndApply(self, arenaID, results):
        if not isinstance(results, dict):
            return
        common = results.get('common', {}) or {}
        guiType = common.get('guiType', 0)
        allowed = []
        for attr in ('RANDOM', 'MAPBOX'):
            val = getattr(constants.ARENA_GUI_TYPE, attr, None)
            if val is not None:
                allowed.append(val)
        if allowed and guiType not in allowed:
            logger.debug('battle-results: arena %s skipped, guiType=%s not in %s',
                         arenaID, guiType, allowed)
            return

        accountDBID = self._getAccountDBID()
        if not accountDBID:
            logger.debug('battle-results: arena %s no accountDBID', arenaID)
            return

        vehicles = results.get('vehicles', {}) or {}
        personal = results.get('personal', {}) or {}
        tankID = None
        damage = 0
        for _, vehicleInfo in vehicles.iteritems():
            if not vehicleInfo:
                continue
            entry = vehicleInfo[0] if isinstance(vehicleInfo, list) else vehicleInfo
            if not isinstance(entry, dict):
                continue
            try:
                if int(entry.get('accountDBID', 0) or 0) != accountDBID:
                    continue
            except (TypeError, ValueError):
                continue
            try:
                tankID = int(entry.get('typeCompDescr', 0) or 0)
            except (TypeError, ValueError):
                tankID = 0
            damage = _extractMarkDamage(entry)
            if tankID:
                break

        if isinstance(personal, dict):
            personalEntries = []
            for key in (accountDBID, str(accountDBID)):
                value = personal.get(key)
                if isinstance(value, dict):
                    personalEntries.append(value)
            if not personalEntries:
                for value in personal.itervalues():
                    if not isinstance(value, dict):
                        continue
                    try:
                        if int(value.get('accountDBID', value.get('accountDBId', 0)) or 0) == accountDBID:
                            personalEntries.append(value)
                    except Exception:
                        pass
            for v in personalEntries:
                try:
                    d = _extractMarkDamage(v)
                    if d > damage:
                        damage = d
                except (TypeError, ValueError):
                    pass

        if not tankID:
            logger.debug('battle-results: arena %s player tank not found', arenaID)
            return

        logger.debug('battle-results: arena %s tankID=%s damage=%d', arenaID, tankID, damage)

        # Р—Р±РµСЂС–РіР°С”РјРѕ marksOnGun Р· СЂРµР·СѓР»СЊС‚Р°С‚С–РІ Р±РѕСЋ РІ РєРµС€
        for v in personalEntries:
            try:
                mog = int(v.get('marksOnGun', -1))
                if mog >= 0:
                    self._controller._updateLastKnownStats(tankID, marksOnGun=mog, force=True)
                    logger.debug('battle-results: marksOnGun=%d saved for tankID=%s', mog, tankID)
                    break
            except (TypeError, ValueError):
                pass

        mapName = _extractMapName(common)
        if mapName and self._controller._session is not None:
            self._controller._session.overrideMapName(tankID, mapName)

        initialMark = self._controller._getLastKnownMark(tankID)
        if initialMark is None:
            initialMark = _readMarkForTankID(tankID)
        if initialMark is not None:
            self._controller._onBattleProcessed(
                tankID, initialMark, mapName=mapName, damage=damage,
                arenaID=arenaID, provisional=True)

        self._scheduleDossierRead(
            tankID, attempt=0, mapName=mapName, damage=damage, arenaID=arenaID)

    @staticmethod
    def _getAccountDBID():
        try:
            player = BigWorld.player()
            dbid = int(getattr(player, 'databaseID', 0) or 0)
            if dbid:
                return dbid
        except Exception:
            pass
        return 0

    def _scheduleDossierRead(self, tankID, attempt, mapName=u'', damage=0, arenaID=None):
        if self._terminated:
            return
        callbackKey = arenaID if arenaID is not None else tankID
        prev = self._dossierCallbackIds.pop(callbackKey, None)
        if prev is not None:
            _cancelCallbackSafe(prev[0])
        delay = self._DOSSIER_FIRST_DELAY if attempt == 0 else self._DOSSIER_RETRY_DELAY
        expectedMark = self._controller._getBaselineHint(tankID, arenaID)
        cbid = BigWorld.callback(
            delay,
            lambda t=tankID, a=attempt, m=mapName, d=damage, aid=arenaID:
                self._readDossier(t, a, m, d, aid))
        self._dossierCallbackIds[callbackKey] = (cbid, expectedMark, mapName, damage)

    def _readDossier(self, tankID, attempt, mapName=u'', damage=0, arenaID=None):
        callbackKey = arenaID if arenaID is not None else tankID
        entry = self._dossierCallbackIds.pop(callbackKey, None)
        if self._terminated:
            return
        expectedPrev = entry[1] if entry else None
        if not damage and entry is not None and len(entry) > 3:
            try:
                damage = int(entry[3] or 0)
            except (TypeError, ValueError):
                damage = 0
        moe = _readMarkForTankID(tankID)
        if moe is None:
            if attempt < self._MAX_DOSSIER_ATTEMPTS:
                self._scheduleDossierRead(tankID, attempt + 1, mapName=mapName,
                                          damage=damage, arenaID=arenaID)
            else:
                logger.debug('battle-results: dossier gave up tankID=%s', tankID)
            return
        if (expectedPrev is not None
                and abs(float(expectedPrev) - float(moe)) < 0.0001
                and attempt < self._MAX_DOSSIER_ATTEMPTS):
            logger.debug('battle-results: dossier unchanged tankID=%s (%.2f), retry %d',
                         tankID, moe, attempt + 1)
            self._scheduleDossierRead(tankID, attempt + 1, mapName=mapName,
                                      damage=damage, arenaID=arenaID)
            return
        try:

            self._controller._onBattleProcessed(
                tankID, moe, mapName=mapName, damage=damage, preMarkHint=expectedPrev,
                arenaID=arenaID)
        except Exception:
            logger.exception('battle-results: controller dispatch failed tankID=%s', tankID)


class _ModsSettingsApiWatcher(object):

    _RETRY_DELAY       = 1.0
    _MAX_INIT_ATTEMPTS = 30

    def __init__(self, controller):
        self._controller      = controller
        self._api             = None
        self._installed       = False
        self._attempt         = 0
        self._retryCallbackId = None

    def init(self):
        if self._installed or self._retryCallbackId is not None:
            return
        self._attempt = 0
        self._tryInit()

    def fini(self):
        _cancelCallbackSafe(self._retryCallbackId)
        self._retryCallbackId = None
        if self._installed and self._api is not None:
            try:
                self._api.onWindowOpened -= self._onWindowOpened
            except Exception:
                pass
            try:
                self._api.onWindowClosed -= self._onWindowClosed
            except Exception:
                pass
        self._api       = None
        self._installed = False
        self._attempt   = 0

    def _tryInit(self):
        self._retryCallbackId = None
        if self._installed:
            return
        api = self._getEventSource()
        if api is None:
            self._scheduleRetry()
            return
        try:
            api.onWindowOpened += self._onWindowOpened
            api.onWindowClosed += self._onWindowClosed
        except Exception:
            logger.exception('mods-settings-api-watcher: subscribe failed')
            self._scheduleRetry()
            return
        self._api       = api
        self._installed = True
        logger.debug('mods-settings-api-watcher: subscribed')

    def _scheduleRetry(self):
        if self._attempt >= self._MAX_INIT_ATTEMPTS:
            logger.debug('mods-settings-api-watcher: unavailable after %d attempts', self._attempt)
            return
        self._attempt += 1
        self._retryCallbackId = BigWorld.callback(
            self._RETRY_DELAY, _weakCallback(self, '_tryInit'))

    @classmethod
    def _getEventSource(cls):
        try:
            from gui.modsSettingsApi import g_modsSettingsApi
        except ImportError:
            return None
        except Exception:
            logger.exception('mods-settings-api-watcher: import failed')
            return None
        return cls._resolveEventSource(g_modsSettingsApi)

    @staticmethod
    def _resolveEventSource(api):
        for source in (api, getattr(api, '_ModsSettingsApi__instance', None)):
            if source is None:
                continue
            if (getattr(source, 'onWindowOpened', None) is not None and
                    getattr(source, 'onWindowClosed', None) is not None):
                return source
        return None

    def _onWindowOpened(self, *args, **kwargs):
        logger.debug('mods-settings-api-watcher: window opened')
        self._dispatch(True)

    def _onWindowClosed(self, *args, **kwargs):
        logger.debug('mods-settings-api-watcher: window closed')
        self._dispatch(False)

    def _dispatch(self, isOpen):
        try:
            self._controller._onModsSettingsChanged(isOpen)
        except Exception:
            logger.exception('mods-settings-api-watcher: dispatch failed')


class _StrongholdBrowserWatcher(object):

    _MODULE_NAMES = (
        'gui.game_control.BrowserController',
        'gui.game_control.browser_controller',
        'gui.game_control.browser',
    )
    _CLASS_NAMES  = ('BrowserController',)
    _METHOD_HINTS = ('browser', 'load', 'create', 'show', 'open', 'delete', 'destroy', 'close')

    def __init__(self, controller):
        self._controller = controller
        self._installed  = False
        self._patched    = []

    def init(self):
        if self._installed:
            return
        patched = 0
        for moduleName in self._MODULE_NAMES:
            try:
                module = __import__(moduleName, fromlist=['*'])
            except Exception:
                continue
            for className in self._CLASS_NAMES:
                cls = getattr(module, className, None)
                if cls is not None:
                    patched += self._patchClass(cls)
        self._installed = patched > 0
        logger.debug('stronghold-browser-watcher: installed=%s patched=%d', self._installed, patched)

    def fini(self):
        for cls, methodName, original in reversed(self._patched):
            try:
                setattr(cls, methodName, original)
            except Exception:
                pass
        self._patched   = []
        self._installed = False

    def _patchClass(self, cls):
        patched = 0
        for methodName in dir(cls):
            nameText = _safeLower(methodName)
            if methodName.startswith('__'):
                continue
            if not any(hint in nameText for hint in self._METHOD_HINTS):
                continue
            try:
                original = getattr(cls, methodName)
            except Exception:
                continue
            if not callable(original) or getattr(original, '_masteryStrongholdWrapped', False):
                continue
            wrapper = self._makeWrapper(methodName, original)
            try:
                setattr(cls, methodName, wrapper)
            except Exception:
                continue
            self._patched.append((cls, methodName, original))
            patched += 1
        return patched

    def _makeWrapper(self, methodName, original):
        watcherRef = weakref.ref(self)

        def _wrapped(instance, *args, **kwargs):
            watcher = watcherRef()
            if watcher is not None:
                watcher._inspectCall(methodName, args, kwargs)
            result = original(instance, *args, **kwargs)
            watcher = watcherRef()
            if watcher is not None:
                watcher._inspectResult(methodName, args, kwargs, result)
            return result

        _wrapped._masteryStrongholdWrapped = True
        return _wrapped

    def _inspectCall(self, methodName, args, kwargs):
        try:
            browserID, url = self._extractBrowserInfo(args, kwargs)
            if _isCloseBrowserMethod(methodName):
                ctrl = self._controller
                unknownActive = _STRONGHOLD_BROWSER_UNKNOWN_ID in ctrl._strongholdBrowserIDs
                if (browserID is None and ctrl._strongholdBrowserIDs) or \
                        unknownActive or \
                        _browserKey(browserID) in ctrl._strongholdBrowserIDs or \
                        _isStrongholdGarageUrl(url):
                    ctrl.onStrongholdBrowserClosed(browserID, url)
                return
            if _isStrongholdGarageUrl(url):
                self._controller.onStrongholdBrowserOpened(browserID, url)
        except Exception:
            logger.exception('stronghold-browser-watcher: call inspection failed')

    def _inspectResult(self, methodName, args, kwargs, result):
        try:
            if _isCloseBrowserMethod(methodName) or isinstance(result, bool) or \
                    not isinstance(result, (int, long, str, unicode)):
                return
            _, url = self._extractBrowserInfo(args, kwargs)
            if _isStrongholdGarageUrl(url):
                self._controller.onStrongholdBrowserOpened(result, url)
        except Exception:
            logger.exception('stronghold-browser-watcher: result inspection failed')

    def _extractBrowserInfo(self, args, kwargs):
        browserID = None
        url       = None
        try:
            iterable = kwargs.iteritems()
        except Exception:
            iterable = ()
        for key, value in iterable:
            keyText = _safeLower(key)
            if browserID is None and keyText in ('browserid', 'browser_id', 'browser', 'viewid', 'id'):
                browserID = value
            foundUrl = self._findUrl(value)
            if foundUrl is not None:
                url = foundUrl
        for value in args:
            foundUrl = self._findUrl(value)
            if foundUrl is not None:
                url = foundUrl
        if browserID is None:
            for value in args:
                if self._findUrl(value) is not None:
                    continue
                if isinstance(value, (int, long, str, unicode)):
                    browserID = value
                    break
        return browserID, url

    def _findUrl(self, value):
        text = _safeLower(value)
        if (text.startswith('http://') or text.startswith('https://') or
                'wgsh-' in text or 'wgsh.' in text or 'battlerooms' in text):
            return value
        if isinstance(value, dict):
            for v in value.itervalues():
                found = self._findUrl(v)
                if found is not None:
                    return found
        return None


class _Mod(object):

    def __init__(self):
        self._session = MasterySessionHistory()
        self._ctrl = MasteryController(session=self._session)
        self._results = _BattleResultsCollector(self._ctrl)
        self._modsSettingsApiWatcher = _ModsSettingsApiWatcher(self._ctrl)
        self._strongholdBrowserWatcher = _StrongholdBrowserWatcher(self._ctrl)
        self._lobbyEventBound = False
        self._battleEnterCallbackId = None
        MasteryPanelInjectorView._g_controller = self._ctrl

    def init(self):
        _loadLocalization()
        _registerFlash()
        g_playerEvents.onAccountShowGUI        += self._onAccountShowGUI
        if getattr(g_playerEvents, 'onAvatarReady', None) is not None:
            g_playerEvents.onAvatarReady       += self._onAvatarReady
        g_playerEvents.onAvatarBecomePlayer    += self._onAvatarBecomePlayer
        g_playerEvents.onAccountBecomeNonPlayer += self._onAccountBecomeNonPlayer
        g_playerEvents.onDisconnected          += self._onDisconnected
        self._results.init()
        self._modsSettingsApiWatcher.init()
        self._strongholdBrowserWatcher.init()
        self._bindLobbyAppEvent()
        # Ctrl shows the badge +/- control while pressed.
        try:
            import Keys
            from gui import g_keyEventHandlers
            g_keyEventHandlers.add(self._onKeyEvent)
        except Exception:
            logger.exception('Ctrl mark badge control handler: registration failed')
        if self._isAccount():
            dbid = _getActiveAccountDBID()
            if dbid:
                self._ctrl.setActiveAccount(dbid)
            self._results.onAccountShowGUI()
            self._ctrl.enable()
        logger.debug('initialized v%s', __version__)

    def fini(self):
        _cancelCallbackSafe(self._battleEnterCallbackId)
        self._battleEnterCallbackId = None
        try:
            g_playerEvents.onAccountShowGUI        -= self._onAccountShowGUI
            if getattr(g_playerEvents, 'onAvatarReady', None) is not None:
                g_playerEvents.onAvatarReady       -= self._onAvatarReady
            g_playerEvents.onAvatarBecomePlayer    -= self._onAvatarBecomePlayer
            g_playerEvents.onAccountBecomeNonPlayer -= self._onAccountBecomeNonPlayer
            g_playerEvents.onDisconnected          -= self._onDisconnected
        except Exception:
            pass
        try:
            from gui import g_keyEventHandlers
            g_keyEventHandlers.remove(self._onKeyEvent)
        except Exception:
            pass
        self._unbindLobbyAppEvent()
        self._strongholdBrowserWatcher.fini()
        self._modsSettingsApiWatcher.fini()
        self._results.fini()
        self._ctrl.disable()
        MasteryPanelInjectorView._g_controller = None
        _unregisterFlash()
        logger.debug('finalized')

    def _onKeyEvent(self, event):
        try:
            import Keys
            key = getattr(event, 'key', None)
            if key is None:
                key = getattr(event, 'keyCode', None)
            ctrlKeys = []
            for attr in ('KEY_LCONTROL', 'KEY_RCONTROL', 'KEY_LEFTCONTROL', 'KEY_RIGHTCONTROL'):
                value = getattr(Keys, attr, None)
                if value is not None:
                    ctrlKeys.append(value)
            if not ctrlKeys:
                ctrlKeys = [29, 157]
            if key not in ctrlKeys:
                return
            self._ctrl.setMarkBadgeControlVisible(bool(event.isKeyDown()))
        except Exception:
            logger.exception('Ctrl mark badge control handler error')

    def onVehicleDamage(self, attackerID, damage):
        try:
            player = BigWorld.player()
            playerVID = int(getattr(player, 'playerVehicleID', 0) or 0)
            attackerID = int(attackerID or 0)
        except Exception:
            return
        if not playerVID or attackerID != playerVID:
            return
        self._ctrl.addBattleLiveDamage(damage)

    def _bindLobbyAppEvent(self):
        if self._lobbyEventBound:
            return
        if g_eventBus is None or AppLifeCycleEvent is None or EVENT_BUS_SCOPE is None:
            logger.debug('lobby-app event: API unavailable, relogin re-injection disabled')
            return
        try:
            g_eventBus.addListener(
                AppLifeCycleEvent.INITIALIZED, self._onLobbyAppInitialized,
                scope=EVENT_BUS_SCOPE.GLOBAL,
            )
            self._lobbyEventBound = True
        except Exception:
            logger.exception('lobby-app event: subscribe failed')

    def _unbindLobbyAppEvent(self):
        if not self._lobbyEventBound:
            return
        try:
            g_eventBus.removeListener(
                AppLifeCycleEvent.INITIALIZED, self._onLobbyAppInitialized,
                scope=EVENT_BUS_SCOPE.GLOBAL,
            )
        except Exception:
            pass
        self._lobbyEventBound = False

    def _onLobbyAppInitialized(self, event):
        try:
            if APP_NAME_SPACE is not None and event.ns != APP_NAME_SPACE.SF_LOBBY:
                return
            app = ServicesLocator.appLoader.getApp(event.ns)
            if app is None:
                return
            if self._ctrl._injectorView is not None:
                try:
                    self._ctrl._injectorView.flashObject.as_setVisible(False)
                    self._ctrl._injectorView.flashObject.as_setBattleBadgeVisible(False)
                    self._ctrl._injectorView.flashObject.as_showDetail(False)
                except Exception:
                    pass
            self._ctrl._injectorView = None
            self._ctrl._panelReady = False
            self._ctrl._visibleByData = False
            self._ctrl._lastVisibleState = None
            self._ctrl._garageVehicleRetryAttempt = 0
            self._ctrl._injectPending = True
            app.loadView(SFViewLoadParams(_LINKAGE_HANGAR))
            logger.debug('mastery: injector reloaded on SF_LOBBY init')
        except Exception:
            self._ctrl._injectPending = False
            logger.exception('mastery: failed to reload injector on SF_LOBBY init')

    @staticmethod
    def _isAccount():
        return isinstance(BigWorld.player(), PlayerAccount)

    def _onAccountShowGUI(self, _=None):
        _cancelCallbackSafe(self._battleEnterCallbackId)
        self._battleEnterCallbackId = None
        self._ctrl.leaveBattle()
        self._strongholdBrowserWatcher.init()
        self._results.onAccountShowGUI()
        dbid = _getActiveAccountDBID()
        if dbid:
            self._ctrl.setActiveAccount(dbid)
        self._ctrl.enable()
        BigWorld.callback(1.0, self._ctrl._restoreHangarPanelAfterResults)

    def _onAvatarBecomePlayer(self):
        if self._ctrl._battleMode:
            return
        _cancelCallbackSafe(self._battleEnterCallbackId)
        self._battleEnterCallbackId = None
        self._tryEnterBattle(0)

    def _onAvatarReady(self, *args, **kwargs):
        _cancelCallbackSafe(self._battleEnterCallbackId)
        self._battleEnterCallbackId = None
        self._tryEnterBattle(0)

    def _tryEnterBattle(self, attempt):
        tankID = self._snapshotBaselineForBattle()
        if tankID is None:
            if attempt < 12:
                self._battleEnterCallbackId = BigWorld.callback(
                    0.35, lambda: self._tryEnterBattle(attempt + 1))
            else:
                logger.debug('battle enter: no tankID after %d attempts', attempt)
            return
        self._battleEnterCallbackId = None
        if self._ctrl._battleMode and self._ctrl._battleTankID == tankID:
            return
        # Р”РѕР·РІРѕР»СЏС”РјРѕ РјС–С‚РєСѓ С‚С–Р»СЊРєРё РІ СЂР°РЅРґРѕРјС– (RANDOM, MAPBOX)
        try:
            player = BigWorld.player()
            guiType = getattr(player, 'arenaGuiType', None)
            if guiType is None:
                arena = getattr(player, 'arena', None)
                if arena is not None:
                    guiType = getattr(arena, 'guiType', None)
            allowed = []
            for attr in ('RANDOM', 'MAPBOX'):
                val = getattr(constants.ARENA_GUI_TYPE, attr, None)
                if val is not None:
                    allowed.append(val)
            if allowed and guiType not in allowed:
                logger.debug('battle enter: skipped guiType=%s (not RANDOM/MAPBOX)', guiType)
                return
        except Exception:
            pass
        self._ctrl.enterBattle(tankID)

    def _onAccountBecomeNonPlayer(self):
        if not self._isAccount():
            self._ctrl.disable()

    def _onDisconnected(self):
        _cancelCallbackSafe(self._battleEnterCallbackId)
        self._battleEnterCallbackId = None
        self._ctrl.disable()
        self._session.reset()
        self._ctrl.clearActiveAccount()

    def _snapshotBaselineForBattle(self):
        try:
            player = BigWorld.player()
        except Exception:
            return
        tankID = None
        try:
            descr = getattr(player, 'vehicleTypeDescriptor', None)
            if descr is not None:
                tankID = int(descr.type.compactDescr)
        except Exception:
            tankID = None
        if tankID is None:
            try:
                arena = getattr(player, 'arena', None)
                pvid = int(getattr(player, 'playerVehicleID', 0) or 0)
                if arena is not None and pvid:
                    vInfo = arena.vehicles.get(pvid)
                    if vInfo is not None:
                        tankID = int(vInfo['vehicleType'].compactDescr)
            except Exception:
                tankID = None
        if tankID is None:
            return None
        stats = self._ctrl._capturePreBattleStats(tankID)
        baseline = stats.get('damageRating')
        if baseline is None:
            baseline = self._ctrl._getLastKnownMark(tankID)
        if baseline is None:
            logger.debug('session: no baseline for tankID=%s', tankID)
            return tankID
        self._session.snapshotBeforeBattle(
            tankID, baseline,
            movingAvgDamage=stats.get('movingAvgDamage'),
            marksOnGun=stats.get('marksOnGun'))
        logger.debug('session: snapshot tankID=%s baseline=%.2f avg=%s',
                     tankID, baseline, stats.get('movingAvgDamage'))
        return tankID


_ORIG_SHOW_DAMAGE_FROM_SHOT = None
_ORIG_SHOW_DAMAGE_FROM_EXPLOSION = None
_ORIG_HANDLE_BATTLE_EVENTS_SUMMARY = None
_ORIG_SHOW_EXTENDED_INFO = None


def _installShowExtendedInfoHook():
    # РќРµ РјРѕР¶РµРјРѕ С…СѓРєРЅСѓС‚Рё РєР»Р°СЃ Р·Р°Р·РґР°Р»РµРіС–РґСЊ вЂ” СЂРѕР±РёРјРѕ С‡РµСЂРµР· enterBattle
    logger.debug('showExtendedInfo: will hook on enterBattle via player().inputHandler')


def _uninstallShowExtendedInfoHook():
    global _ORIG_SHOW_EXTENDED_INFO
    _ORIG_SHOW_EXTENDED_INFO = None


def _installBattleSummaryHook():
    pass


def _uninstallBattleSummaryHook():
    pass


def _installVehicleDamageHooks():
    pass


def _uninstallVehicleDamageHooks():
    pass


_g_mod = _Mod()


def init():
    try:
        _installBattleSummaryHook()
        _installVehicleDamageHooks()
        _installShowExtendedInfoHook()
        _g_mod.init()
    except Exception:
        logger.exception('init failed')


def fini():
    try:
        _g_mod.fini()
        _uninstallVehicleDamageHooks()
        _uninstallBattleSummaryHook()
        _uninstallShowExtendedInfoHook()
    except Exception:
        logger.exception('fini failed')
