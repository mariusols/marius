using Toybox.WatchUi;
using Toybox.Graphics as Gfx;
using Toybox.System as Sys;
using Toybox.Time;
using Toybox.Time.Gregorian;
using Toybox.Math;

// GMT-Master II style watch face.
// Static dial (bezel, print, markers) is a pre-rendered bitmap per variant and screen size
// (see tools/render_face.py). Hands and date are drawn live.
class GMTView extends WatchUi.WatchFace {

    const C_WHITE  = 0xFFFFFF;
    const C_SILVER = 0xAAAAAA;
    const C_STEEL  = 0x555555;

    const DATE_R = 0.625;

    var _awake = true;
    var _cx = 130.0;
    var _cy = 130.0;
    var _r  = 130.0;
    var _bg = null;
    var _bgStyle = -1;
    var _digits = null;

    function initialize() {
        WatchFace.initialize();
    }

    function onLayout(dc) {
        var w = dc.getWidth();
        var h = dc.getHeight();
        _cx = w / 2.0;
        _cy = h / 2.0;
        _r = (w < h ? w : h) / 2.0;
        _digits = [
            WatchUi.loadResource(Rez.Drawables.D0), WatchUi.loadResource(Rez.Drawables.D1),
            WatchUi.loadResource(Rez.Drawables.D2), WatchUi.loadResource(Rez.Drawables.D3),
            WatchUi.loadResource(Rez.Drawables.D4), WatchUi.loadResource(Rez.Drawables.D5),
            WatchUi.loadResource(Rez.Drawables.D6), WatchUi.loadResource(Rez.Drawables.D7),
            WatchUi.loadResource(Rez.Drawables.D8), WatchUi.loadResource(Rez.Drawables.D9)
        ];
    }

    function onExitSleep() {
        _awake = true;
        WatchUi.requestUpdate();
    }

    function onEnterSleep() {
        _awake = false;
        WatchUi.requestUpdate();
    }

    // ---------------------------------------------------------------- variant data

    function loadBackground(style) {
        if (style == _bgStyle && _bg != null) {
            return;
        }
        _bg = null; // free the previous bitmap first
        if (style == 1) {
            _bg = WatchUi.loadResource(Rez.Drawables.BgBatman);
        } else if (style == 2) {
            _bg = WatchUi.loadResource(Rez.Drawables.BgSprite);
        } else {
            _bg = WatchUi.loadResource(Rez.Drawables.BgPepsi);
        }
        _bgStyle = style;
    }

    function gmtColor(style) {
        if (style == 1) { return 0x0055AA; }  // Batman: blue
        if (style == 2) { return 0x00AA55; }  // Sprite: green
        return 0xAA0000;                      // Pepsi: red
    }

    // ---------------------------------------------------------------- geometry

    // Clock angle a (radians, 0 = 12 o'clock, clockwise), radius factor f -> screen point
    function polar(a, f) {
        return [_cx + _r * f * Math.sin(a), _cy - _r * f * Math.cos(a)];
    }

    // Hand-space points ([x across, y outward] in radius units) -> screen polygon
    function xf(pts, a) {
        var s = Math.sin(a);
        var c = Math.cos(a);
        var out = new [pts.size()];
        for (var i = 0; i < pts.size(); i++) {
            var x = pts[i][0] * _r;
            var y = pts[i][1] * _r;
            out[i] = [_cx + y * s + x * c, _cy - y * c + x * s];
        }
        return out;
    }

    function poly(dc, pts, a, color) {
        dc.setColor(color, Gfx.COLOR_TRANSPARENT);
        dc.fillPolygon(xf(pts, a));
    }

    function disc(dc, p, f, color) {
        dc.setColor(color, Gfx.COLOR_TRANSPARENT);
        dc.fillCircle(p[0], p[1], _r * f);
    }

    // ---------------------------------------------------------------- drawing

    function onUpdate(dc) {
        if (dc has :setAntiAlias) {
            dc.setAntiAlias(true);
        }
        var style = GMTSettings.bezelStyle();
        loadBackground(style);

        dc.setColor(0x000000, 0x000000);
        dc.clear();
        dc.drawBitmap(0, 0, _bg);

        drawDate(dc, style == 2 ? 9 : 3);

        var clock = Sys.getClockTime();
        var twoPi = Math.PI * 2.0;

        // 24h hand: one turn per day on UTC + configured offset
        var t = Time.now().value() + GMTSettings.gmtOffset() * 3600;
        var daySec = ((t % 86400) + 86400) % 86400;
        var aGmt = daySec / 86400.0 * twoPi;
        var aHour = ((clock.hour % 12) + clock.min / 60.0) / 12.0 * twoPi;
        var aMin = (clock.min + clock.sec / 60.0) / 60.0 * twoPi;

        drawHourHand(dc, aHour);
        drawGmtHand(dc, aGmt, gmtColor(style));
        drawMinuteHand(dc, aMin);
        if (_awake) {
            drawSecondHand(dc, clock.sec / 60.0 * twoPi);
        }
        drawCenterCap(dc);
    }

    function drawDate(dc, atHour) {
        var day = Gregorian.info(Time.now(), Time.FORMAT_SHORT).day;
        var p = polar(atHour / 12.0 * Math.PI * 2.0, DATE_R);
        var bmps = (day >= 10) ? [_digits[day / 10], _digits[day % 10]] : [_digits[day]];
        var tw = 0;
        for (var i = 0; i < bmps.size(); i++) {
            tw += bmps[i].getWidth();
        }
        var x = p[0] - tw / 2.0;
        for (var j = 0; j < bmps.size(); j++) {
            dc.drawBitmap(x, p[1] - bmps[j].getHeight() / 2.0, bmps[j]);
            x += bmps[j].getWidth();
        }
    }

    // Mercedes hour hand: white-gold frame, lume in shaft, circle segments and tip
    function drawHourHand(dc, a) {
        poly(dc, [[-0.032, -0.10], [-0.032, 0.34], [0.032, 0.34], [0.032, -0.10]], a, C_SILVER);
        poly(dc, [[-0.018, 0.03], [-0.018, 0.33], [0.018, 0.33], [0.018, 0.03]], a, C_WHITE);
        poly(dc, [[-0.048, 0.455], [0.0, 0.575], [0.048, 0.455]], a, C_SILVER);
        poly(dc, [[-0.030, 0.47], [0.0, 0.548], [0.030, 0.47]], a, C_WHITE);

        var c = polar(a, 0.40);
        disc(dc, c, 0.085, C_SILVER);
        disc(dc, c, 0.068, C_WHITE);
        var len = 0.072;
        var wd = 0.009;
        for (var k = 0; k < 3; k++) {
            var t = k * Math.PI * 2.0 / 3.0;
            var dx = Math.sin(t);
            var dy = Math.cos(t);
            var px = dy;
            var py = -dx;
            poly(dc, [
                [px * wd, 0.40 + py * wd],
                [dx * len + px * wd, 0.40 + dy * len + py * wd],
                [dx * len - px * wd, 0.40 + dy * len - py * wd],
                [-px * wd, 0.40 - py * wd]
            ], a, C_SILVER);
        }
        disc(dc, c, 0.016, C_SILVER);
    }

    // 24h hand: coloured shaft and arrow, lume inside the arrow
    function drawGmtHand(dc, a, color) {
        poly(dc, [[-0.012, -0.15], [-0.012, 0.65], [0.012, 0.65], [0.012, -0.15]], a, color);
        poly(dc, [[-0.072, 0.635], [0.0, 0.79], [0.072, 0.635]], a, color);
        poly(dc, [[-0.044, 0.658], [0.0, 0.748], [0.044, 0.658]], a, C_WHITE);
    }

    function drawMinuteHand(dc, a) {
        poly(dc, [[-0.030, -0.12], [-0.030, 0.66], [0.0, 0.765], [0.030, 0.66], [0.030, -0.12]], a, C_SILVER);
        poly(dc, [[-0.016, 0.06], [-0.016, 0.655], [0.0, 0.735], [0.016, 0.655], [0.016, 0.06]], a, C_WHITE);
    }

    function drawSecondHand(dc, a) {
        poly(dc, [[-0.008, -0.22], [-0.008, 0.775], [0.008, 0.775], [0.008, -0.22]], a, C_SILVER);
        var q = polar(a, 0.60);
        disc(dc, q, 0.046, C_SILVER);
        disc(dc, q, 0.034, C_WHITE);
    }

    function drawCenterCap(dc) {
        var c = [_cx, _cy];
        disc(dc, c, 0.042, C_SILVER);
        disc(dc, c, 0.018, C_STEEL);
    }
}
