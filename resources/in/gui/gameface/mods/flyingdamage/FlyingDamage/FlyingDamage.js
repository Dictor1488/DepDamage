(function () {
    'use strict';

    var root = document.getElementById('fd-root');
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

    function ensureRoot() {
        if (!root) root = document.getElementById('fd-root');
        if (!root && document.body) {
            root = document.createElement('div');
            root.id = 'fd-root';
            document.body.appendChild(root);
        }
        return !!root;
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
        if (!ensureRoot() || !ev) return;

        var x = num(ev.x, 110);
        var y = num(ev.y, 66);
        var textValue = String(Math.round(num(ev.dmg, 0)));
        var size = Math.max(24, num(ev.size, 38));
        var life = Math.max(0.8, num(ev.life, 1.6));
        var alpha = Math.max(0.2, Math.min(1, num(ev.alpha, 1)));

        var el = document.createElement('div');
        el.className = 'fd-damage';
        el.textContent = textValue;
        el.style.left = x + 'px';
        el.style.top = y + 'px';
        el.style.color = colorFromInt(ev.color);
        el.style.fontSize = size + 'px';
        el.style.opacity = alpha;
        root.appendChild(el);

        log('draw-popup-html dmg=' + textValue + ' xy=' + Math.round(x) + ',' + Math.round(y) + ' view=' + window.innerWidth + 'x' + window.innerHeight);

        var start = Date.now();
        function anim() {
            var t = Math.min(1, (Date.now() - start) / (life * 1000));
            var dy = -58 * t;
            var sc = 1 + 0.08 * (1 - Math.abs(t * 2 - 1));
            var op = t < 0.72 ? alpha : Math.max(0, alpha * (1 - (t - 0.72) / 0.28));
            el.style.transform = 'translate(-50%, -50%) translateY(' + dy + 'px) scale(' + sc + ')';
            el.style.opacity = op;
            if (t < 1) window.requestAnimationFrame(anim);
            else if (el && el.parentNode) el.parentNode.removeChild(el);
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
        ensureRoot();
        log('initialize-popup-html view=' + window.innerWidth + 'x' + window.innerHeight + ' root=' + !!root);
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
