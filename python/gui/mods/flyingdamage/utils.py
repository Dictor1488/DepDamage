# -*- coding: utf-8 -*-
# utils.py  --  Python 2.7
# Clean override system with restore-on-fini.

import types
import BigWorld

_overrides = []


def override(holder, name, wrapper=None):
    """Monkey-patch holder.name so that wrapper(original, *args, **kwargs) runs.

    Usage as decorator:
        @override(Vehicle, 'showDamageFromShot')
        def hooked(base, self, *a, **kw):
            base(self, *a, **kw)
            ...
    """
    if wrapper is None:
        return lambda w: override(holder, name, w)

    target = getattr(holder, name)
    _overrides.append((holder, name, target))
    wrapped = lambda *a, **kw: wrapper(target, *a, **kw)

    if not isinstance(holder, types.ModuleType) and isinstance(target, types.FunctionType):
        setattr(holder, name, staticmethod(wrapped))
    else:
        setattr(holder, name, wrapped)


def restore_overrides():
    while _overrides:
        holder, name, original = _overrides.pop()
        try:
            setattr(holder, name, original)
        except Exception:
            pass


def cancelCallbackSafe(cbid):
    try:
        if cbid is not None:
            BigWorld.cancelCallback(cbid)
            return True
    except (AttributeError, ValueError):
        return False
