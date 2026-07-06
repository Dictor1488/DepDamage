(function () {
    'use strict';

    var NS = 'http://www.w3.org/2000/svg';
    var root = document.getElementById('fd-root');
    var hud = document.getElementById('fd-hud');
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

    function svgEl(name, attrs, parent) {
        var e = document.createElementNS(NS, name);
        if (attrs) {
            for (var k in attrs) {
                if (attrs.hasOwnProperty(k)) e.setAttribute(k, attrs[k]);
            }
        }
        if (parent) parent.appendChild(e);
        return e;
    }

    function ensureHud() {
        if (!root) root = document.getElementById('fd-root');
        if (!hud) hud = document.getElementById('fd-hud');
        if (!root && document.body) {
            root = document.createElement('div');
            root.id = 'fd-root';
            document.body.appendChild(root);
        }
        if (!hud && root) {
            hud = svgEl('svg', {
                id: 'fd-hud',
                width: '2560',
                height: '1369',
                viewBox: '0 0 2560 1369'
            }, root);
        }
        return !!hud;
    }

    function viewportW() {
        return Math.max(1, window.innerWidth || document.documentElement.clientWidth || document.body.clientWidth || 256);
    }

    function viewportH() {
        return Math.max(1, window.innerHeight || document.documentElement.clientHeight || document.body.clientHeight || 256);
    }

    function addDamage(ev) {
        if (!ensureHud() || !ev) return;

        var vw = viewportW();
        var vh = viewportH();
        var sw = Math.max(1, num(ev.sw, 2560));
        var sh = Math.max(1, num(ev.sh, 1369));
        var x = clamp(num(ev.x, sw * 0.5), -2000, sw + 2000);
        var y = clamp(num(ev.y, sh * 0.5), -2000, sh + 2000);
        var textValue = String(Math.round(num(ev.dmg, 0)));
        var size = Math.max(24, num(ev.size, 36));
        var life = Math.max(0.8, num(ev.life, 1.6));
        var color = colorFromInt(ev.color);

        var g = svgEl('g', { transform: 'translate(' + x + ' ' + y + ')' }, hud);
        var shadow = svgEl('text', {
            'class': 'fd-damage-shadow',
            x: '3',
            y: '3',
            'font-size': String(size)
        }, g);
        shadow.textContent = textValue;

        var main = svgEl('text', {
            'class': 'fd-damage-main',
            x: '0',
            y: '0',
            fill: color,
            'font-size': String(size),
            opacity: String(Math.max(0.2, Math.min(1, num(ev.alpha, 1))))
        }, g);
        main.textContent = textValue;

        log('draw-svg dmg=' + textValue + ' xy=' + Math.round(x) + ',' + Math.round(y) + ' view=' + vw + 'x' + vh + ' screen=' + sw + 'x' + sh);

        var start = Date.now();
        function anim() {
            var t = Math.min(1, (Date.now() - start) / (life * 1000));
            var dy = -72 * t;
            var sc = 1 + 0.04 * (1 - Math.abs(t * 2 - 1));
            var op = t < 0.72 ? 1 : Math.max(0, 1 - (t - 0.72) / 0.28);
            g.setAttribute('transform', 'translate(' + x + ' ' + (y + dy) + ') scale(' + sc + ')');
            main.setAttribute('opacity', String(op));
            shadow.setAttribute('opacity', String(op * 0.65));
            if (t < 1) window.requestAnimationFrame(anim);
            else if (g && g.parentNode) g.parentNode.removeChild(g);
        }
        window.requestAnimationFrame(anim);
    }

    function showBootMarker() {
        if (bootShown) return;
        bootShown = true;
        addDamage({ id: -1, x: 1280, y: 180, sw: 2560, sh: 1369, dmg: 9999, color: 0x66FF66, size: 54, alpha: 1, life: 8.0 });
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
        ensureHud();
        log('initialize-svg view=' + viewportW() + 'x' + viewportH() + ' hud=' + !!hud);
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
    }
}());
