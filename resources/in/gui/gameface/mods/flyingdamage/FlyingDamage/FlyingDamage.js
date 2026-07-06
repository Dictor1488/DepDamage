(function () {
    'use strict';

    var NS = 'http://www.w3.org/2000/svg';
    var root = document.getElementById('fd-root');
    var hud = document.getElementById('fd-hud');
    var lastPayload = '';
    var started = false;

    function log(msg) {
        try { console.warn('[FlyingDamageGF_JS] ' + msg); } catch (e) {}
    }

    function num(v, d) {
        v = Number(v);
        return isNaN(v) ? d : v;
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
                width: '220',
                height: '120',
                viewBox: '0 0 220 120'
            }, root);
        }
        return !!hud;
    }

    function ready() {
        try {
            if (window.model && typeof window.model.onReady === 'function') window.model.onReady();
            else if (window.viewModel && typeof window.viewModel.onReady === 'function') window.viewModel.onReady();
        } catch (e) {
            log('onReady failed ' + e);
        }
    }

    function addDamage(ev) {
        if (!ensureHud() || !ev) return;

        var x = num(ev.x, 110);
        var y = num(ev.y, 66);
        var textValue = String(Math.round(num(ev.dmg, 0)));
        var size = Math.max(24, num(ev.size, 38));
        var life = Math.max(0.8, num(ev.life, 1.6));
        var color = colorFromInt(ev.color);
        var alpha = Math.max(0.2, Math.min(1, num(ev.alpha, 1)));

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
            opacity: String(alpha)
        }, g);
        main.textContent = textValue;

        log('draw-popup-svg dmg=' + textValue + ' xy=' + Math.round(x) + ',' + Math.round(y) + ' view=' + window.innerWidth + 'x' + window.innerHeight);

        var start = Date.now();
        function anim() {
            var t = Math.min(1, (Date.now() - start) / (life * 1000));
            var dy = -58 * t;
            var sc = 1 + 0.08 * (1 - Math.abs(t * 2 - 1));
            var op = t < 0.72 ? alpha : Math.max(0, alpha * (1 - (t - 0.72) / 0.28));
            g.setAttribute('transform', 'translate(' + x + ' ' + (y + dy) + ') scale(' + sc + ')');
            main.setAttribute('opacity', String(op));
            shadow.setAttribute('opacity', String(op * 0.65));
            if (t < 1) window.requestAnimationFrame(anim);
            else if (g && g.parentNode) g.parentNode.removeChild(g);
        }
        window.requestAnimationFrame(anim);
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
        } catch (e) {
            log('payload read exception ' + e);
        }
        return raw ? String(raw) : '';
    }

    function readPayload() {
        var raw = getRawPayload();
        if (!raw || raw === lastPayload) return;
        lastPayload = raw;
        var payload = null;
        try { payload = JSON.parse(raw); } catch (e) {
            log('JSON parse failed raw=' + raw.substr(0, 120));
            return;
        }
        var events = payload && payload.events ? payload.events : [];
        log('payload-popup seq=' + payload.seq + ' events=' + events.length);
        for (var i = 0; i < events.length; i++) addDamage(events[i]);
    }

    function initialize() {
        if (started) return;
        started = true;
        ensureHud();
        log('initialize-popup-svg view=' + window.innerWidth + 'x' + window.innerHeight + ' hud=' + !!hud);
        ready();
        readPayload();
        window.setTimeout(readPayload, 50);
        window.setTimeout(readPayload, 150);
        window.setTimeout(readPayload, 500);
        try {
            if (window.engine) {
                window.engine.on('viewEnv.onDataChanged', readPayload);
                window.engine.on('self.onDataUpdated', readPayload);
            }
        } catch (e) {}
    }

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
