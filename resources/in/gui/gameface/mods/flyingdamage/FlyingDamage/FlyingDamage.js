(function () {
    'use strict';

    var root = document.getElementById('fd-root');
    var lastPayload = '';
    var pollTimer = null;
    var lastEventId = 0;
    var tickCount = 0;
    var bootShown = false;

    function log(msg) {
        try { console.warn('[FlyingDamageGF_JS] ' + msg); } catch (e) {}
    }

    function num(v, d) {
        v = Number(v);
        return isNaN(v) ? d : v;
    }

    function clamp(v, min, max) {
        return Math.max(min, Math.min(max, v));
    }

    function colorFromInt(v) {
        v = Number(v);
        if (isNaN(v)) v = 0xFF3838;
        v = v & 0xFFFFFF;
        var s = v.toString(16);
        while (s.length < 6) s = '0' + s;
        return '#' + s;
    }

    function ensureRoot() {
        if (!root) root = document.getElementById('fd-root');
        if (!root && document.body) {
            root = document.createElement('div');
            root.id = 'fd-root';
            document.body.appendChild(root);
        }
        return !!root;
    }

    function viewportW() {
        return Math.max(1, window.innerWidth || document.documentElement.clientWidth || document.body.clientWidth || 2560);
    }

    function viewportH() {
        return Math.max(1, window.innerHeight || document.documentElement.clientHeight || document.body.clientHeight || 1369);
    }

    function addDamage(ev) {
        if (!ensureRoot() || !ev) return;

        var vw = viewportW();
        var vh = viewportH();
        var sw = Math.max(1, num(ev.sw, vw));
        var sh = Math.max(1, num(ev.sh, vh));
        var sx = vw / sw;
        var sy = vh / sh;
        var x = clamp(num(ev.x, vw * 0.5) * sx, 8, vw - 8);
        var y = clamp(num(ev.y, vh * 0.5) * sy, 8, vh - 8);

        var el = document.createElement('div');
        el.className = 'fd-damage';
        el.textContent = String(Math.round(num(ev.dmg, 0)));
        el.style.left = x + 'px';
        el.style.top = y + 'px';
        el.style.color = colorFromInt(ev.color);
        el.style.fontSize = Math.max(18, num(ev.size, 28)) + 'px';
        el.style.opacity = Math.max(0.15, Math.min(1, num(ev.alpha, 1)));
        el.style.animationDuration = Math.max(0.6, num(ev.life, 1.6)) + 's';
        root.appendChild(el);

        log('draw dmg=' + el.textContent + ' xy=' + Math.round(x) + ',' + Math.round(y) + ' view=' + vw + 'x' + vh);

        window.setTimeout(function () {
            if (el && el.parentNode) el.parentNode.removeChild(el);
        }, Math.max(700, num(ev.life, 1.6) * 1000 + 300));
    }

    function showBootMarker() {
        if (bootShown) return;
        bootShown = true;
        addDamage({ id: -1, x: 110, y: 90, sw: 2560, sh: 1369, dmg: 'FD', color: 0x66FF66, size: 30, alpha: 1, life: 4.0 });
    }

    function getRawPayload() {
        var raw = '';
        try {
            if (window.model) {
                if (typeof window.model.getPayload === 'function') raw = window.model.getPayload();
                else if (window.model.payload !== undefined) raw = window.model.payload;
            }
            if ((!raw || raw === '{}') && window.viewModel) {
                if (typeof window.viewModel.getPayload === 'function') raw = window.viewModel.getPayload();
                else if (window.viewModel.payload !== undefined) raw = window.viewModel.payload;
            }
            if ((!raw || raw === '{}') && window.__payload !== undefined) raw = window.__payload;
        } catch (e) {
            log('payload read exception ' + e);
        }
        return raw ? String(raw) : '';
    }

    function readPayload() {
        tickCount++;
        var raw = getRawPayload();
        if (tickCount === 1 || tickCount === 60 || tickCount === 180) {
            log('tick=' + tickCount + ' hasModel=' + !!window.model + ' hasViewModel=' + !!window.viewModel + ' rawLen=' + (raw ? raw.length : 0));
        }
        if (!raw || raw === lastPayload) return;
        lastPayload = raw;

        var payload = null;
        try { payload = JSON.parse(raw); } catch (e) {
            log('JSON parse failed raw=' + raw.substr(0, 120));
            return;
        }
        if (!payload) return;

        var events = payload.events || [];
        log('payload seq=' + payload.seq + ' events=' + events.length);
        for (var i = 0; i < events.length; i++) {
            var ev = events[i];
            var id = Math.round(num(ev.id, 0));
            if (id && id <= lastEventId) continue;
            if (id > lastEventId) lastEventId = id;
            addDamage(ev);
        }
    }

    function tick() {
        readPayload();
    }

    function initialize() {
        log('initialize view=' + viewportW() + 'x' + viewportH() + ' root=' + !!root);
        showBootMarker();
        tick();
        window.setTimeout(tick, 50);
        window.setTimeout(tick, 150);
        window.setTimeout(tick, 500);
        if (!pollTimer) pollTimer = window.setInterval(tick, 33);
        try {
            if (window.engine) {
                window.engine.on('viewEnv.onDataChanged', tick);
                window.engine.on('self.onDataUpdated', tick);
            }
        } catch (e) {}
    }

    window.__fdShowDamage = addDamage;

    if (window.engine && window.engine.whenReady) {
        var domReady = window.isDomBuilt ? Promise.resolve() : new Promise(function (resolve) {
            window.engine.on('self.onDomBuilt', resolve);
        });
        Promise.all([window.engine.whenReady, domReady]).then(function () {
            requestAnimationFrame(function () { requestAnimationFrame(initialize); });
        });
    } else {
        initialize();
        var demoId = 1;
        window.setInterval(function () {
            addDamage({ id: demoId++, x: 400 + Math.random() * 300, y: 300 + Math.random() * 100, sw: 1920, sh: 1080, dmg: 814, color: 0xFF3838, size: 28, alpha: 1, life: 1.6 });
        }, 1200);
    }
}());
