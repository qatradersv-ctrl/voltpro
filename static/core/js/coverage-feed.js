/* The coverage map's demo feed.
 *
 * Clicking a county dot opens what a monitored VoltPro site would report — grid,
 * solar, load, inverter and battery — with the numbers generated here in the
 * browser. Nothing is read from a real installation, so every surface that shows
 * these figures labels them as a simulation.
 */
(function () {
    'use strict';

    var section = document.getElementById('coverage');
    var panel = document.getElementById('site-feed');
    if (!section || !panel) return;

    var dots = Array.prototype.slice.call(section.querySelectorAll('.ken-map-dot[data-county]'));
    if (!dots.length) return;

    var site = panel.querySelector('[data-feed="site"]');
    var clock = panel.querySelector('[data-feed="clock"]');
    var led = panel.querySelector('.feed-led');
    if (!site || !clock) return;
    var values = {}, bars = {};
    ['grid', 'solar', 'load', 'inverter', 'battery'].forEach(function (key) {
        values[key] = panel.querySelector('[data-value="' + key + '"]');
        bars[key] = panel.querySelector('[data-bar="' + key + '"]');
    });

    var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    var TICK_MS = reduce ? 5000 : 1400;
    var timer = null;
    var site_state = null;

    /* FNV-1a, so a county always gets the same profile as it did last visit. */
    function hash(text) {
        var h = 2166136261;
        for (var i = 0; i < text.length; i += 1) {
            h ^= text.charCodeAt(i);
            h = Math.imul(h, 16777619) >>> 0;
        }
        return h;
    }

    function profile(name) {
        var h = hash(name);
        return {
            arrayKw: 26 + (h % 9) * 15,
            battKw: 12 + ((h >>> 4) % 6) * 7,
            baseLoad: 9 + ((h >>> 8) % 7) * 4,
            soc: 46 + ((h >>> 12) % 44),
            minutes: h % 1440
        };
    }

    function clamp(value, low, high) {
        return Math.min(high, Math.max(low, value));
    }

    function bar(key, ratio) {
        if (bars[key]) bars[key].style.width = Math.round(clamp(ratio, 0, 1) * 100) + '%';
    }

    function show(key, text, cls) {
        if (!values[key]) return;
        values[key].textContent = text;
        if (cls !== undefined) values[key].className = cls;
    }

    function timeOfDay(minutes) {
        var h = Math.floor(minutes / 60), m = Math.floor(minutes % 60);
        return (h < 10 ? '0' : '') + h + ':' + (m < 10 ? '0' : '') + m;
    }

    function tick() {
        var s = site_state;
        if (!s) return;

        s.minutes = (s.minutes + 8) % 1440;
        var hour = s.minutes / 60;
        var sun = Math.max(0, Math.sin((hour - 6) / 12 * Math.PI));

        var solar = s.arrayKw * sun * (0.84 + Math.random() * 0.16);
        var load = Math.max(1.4, s.baseLoad * (1 + 0.26 * Math.sin(s.minutes / 97)) + (Math.random() - 0.5) * 2.6);
        var net = solar - load;
        var battery = clamp(net, -s.battKw, s.battKw);
        var grid = net - battery;

        s.soc = clamp(s.soc + battery * 0.03, 18, 100);

        clock.textContent = timeOfDay(s.minutes);
        show('grid', (grid < -0.3 ? 'Import ' : grid > 0.3 ? 'Export ' : 'Balanced ') + Math.abs(grid).toFixed(1) + ' kW');
        show('solar', solar.toFixed(1) + ' kW');
        show('load', load.toFixed(1) + ' kW');
        var awake = sun > 0.02 || Math.abs(battery) > 0.5;
        show('inverter', awake ? 'Online' : 'Standby', 'feed-value feed-value--' + (awake ? 'ok' : 'dim'));
        if (led) led.classList.toggle('is-on', awake);
        show('battery', Math.round(s.soc) + ' %  ' + (battery > 0.4 ? 'charging' : battery < -0.4 ? 'supplying' : 'floating'));

        bar('grid', Math.abs(grid) / 55);
        bar('solar', solar / s.arrayKw);
        bar('load', load / (s.baseLoad * 1.6));
        bar('battery', s.soc / 100);
    }

    function restart() {
        if (timer) clearInterval(timer);
        timer = setInterval(tick, TICK_MS);
    }

    function select(dot) {
        var name = dot.getAttribute('data-county');
        dots.forEach(function (d) { d.classList.toggle('ken-map-dot--on', d === dot); });
        section.querySelectorAll('.ken-map-served').forEach(function (path) {
            path.classList.toggle('ken-map-served--on', path.getAttribute('data-county') === name);
        });

        site.textContent = dot.getAttribute('data-label') || name;
        panel.classList.add('is-live');
        site_state = profile(name);
        tick();
        restart();
    }

    dots.forEach(function (dot) {
        dot.addEventListener('click', function () { select(dot); });
        dot.addEventListener('keydown', function (event) {
            if (event.key === 'Enter' || event.key === ' ' || event.key === 'Spacebar') {
                event.preventDefault();
                select(dot);
            }
        });
    });

    document.addEventListener('visibilitychange', function () {
        if (document.hidden) {
            if (timer) { clearInterval(timer); timer = null; }
        } else if (site_state) {
            restart();
        }
    });
}());
