(function () {
    'use strict';

    var root = document.getElementById('fd-root');
    var lastPayload = '';
    var pollTimer = null;
    var lastEventId = 0;

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

    function addDamage(ev) {
        if (!root || !ev) return;

        var sw = Math.max(1, num(ev.sw, window.innerWidth || 1920));
        var sh = Math.max(1, num(ev.sh, window.innerHeight || 1080));
        var sx = (window.innerWidth || sw) / sw;
        var sy = (window.innerHeight || sh) / sh;
        var x = clamp(num(ev.x, 0) * sx, -200, (window.innerWidth || sw) + 200);
        var y = clamp(num(ev.y, 0) * sy, -200, (window.innerHeight || sh) + 200);

        var el = document.createElement('div');
        el.className = 'fd-damage';
        el.textContent = String(Math.round(num(ev.dmg, 0)));
        el.style.left = x + 'px';
        el.style.top = y + 'px';
        el.style.color = colorFromInt(ev.color);
        el.style.fontSize = Math.max(12, num(ev.size, 26)) + 'px';
        el.style.opacity = Math.max(0.05, Math.min(1, num(ev.alpha, 1)));
        el.style.animationDuration = Math.max(0.3, num(ev.life, 1.6)) + 's';
        root.appendChild(el);

        window.setTimeout(function () {
            if (el && el.parentNode) el.parentNode.removeChild(el);
        }, Math.max(400, num(ev.life, 1.6) * 1000 + 200));
    }

    function readPayload() {
        var raw = window.model && window.model.payload ? String(window.model.payload) : '';
        if (!raw || raw === lastPayload) return;
        lastPayload = raw;

        var payload = null;
        try { payload = JSON.parse(raw); } catch (e) { return; }
        if (!payload) return;

        var events = payload.events || [];
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
        tick();
        window.setTimeout(tick, 50);
        window.setTimeout(tick, 150);
        if (!pollTimer) pollTimer = window.setInterval(tick, 33);
        if (window.engine) window.engine.on('viewEnv.onDataChanged', tick);
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
        var demoId = 1;
        window.setInterval(function () {
            addDamage({ id: demoId++, x: 400 + Math.random() * 300, y: 300 + Math.random() * 100, sw: 1920, sh: 1080, dmg: 814, color: 0xFF3838, size: 28, alpha: 1, life: 1.6 });
        }, 1200);
    }
}());
