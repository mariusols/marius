using Toybox.WatchUi;
using Toybox.Graphics as Gfx;
using Toybox.System as Sys;
using Toybox.Time;
using Toybox.Time.Gregorian;
using Toybox.Math;

// GMT-style analog watch face: 24h two-tone bezel, Mercedes hour hand,
// arrow-tipped 24h GMT hand, lume-dot markers, date window at 3 o'clock.
class GMTView extends WatchUi.WatchFace {

    // Palette (chosen to map cleanly onto the fenix 7 MIP 64-colour display)
    const C_BLACK  = 0x000000;
    const C_WHITE  = 0xFFFFFF;
    const C_SILVER = 0xAAAAAA;
    const C_STEEL  = 0x555555;

    var _awake = true;
    var _cx = 130.0;
    var _cy = 130.0;
    var _r  = 130.0;
    var _dialTop = null;
    var _dialBottom = null;

    function initialize() {
        WatchFace.initialize();
    }

    function onLayout(dc) {
        var w = dc.getWidth();
        var h = dc.getHeight();
        _cx = w / 2.0;
        _cy = h / 2.0;
        _r = (w < h ? w : h) / 2.0;
        _dialTop = WatchUi.loadResource(Rez.Drawables.DialTop);
        _dialBottom = WatchUi.loadResource(Rez.Drawables.DialBottom);
    }

    function onExitSleep() {
        _awake = true;
        WatchUi.requestUpdate();
    }

    function onEnterSleep() {
        _awake = false;
        WatchUi.requestUpdate();
    }

    // ---------------------------------------------------------------- colours

    // [top half, bottom half, GMT hand]
    function bezelColors(style) {
        if (style == 1) { return [0xAA0000, 0x0055AA, 0xAA0000]; } // Pepsi reversed
        if (style == 2) { return [0x000000, 0x0055AA, 0x0055AA]; } // Batman
        if (style == 3) { return [0x000000, 0xAA0000, 0xAA0000]; } // Coke
        if (style == 4) { return [0x00AA00, 0x000000, 0x00AA00]; } // Sprite
        return [0x0055AA, 0xAA0000, 0xAA0000];                     // Pepsi
    }

    // ---------------------------------------------------------------- geometry

    // Clock angle a (radians, 0 = 12 o'clock, clockwise) and radius factor f -> screen point
    function polar(a, f) {
        return [_cx + _r * f * Math.sin(a), _cy - _r * f * Math.cos(a)];
    }

    // Transform hand-space points ([x across, y outward] in units of radius) to screen
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

    function fillOutlined(dc, pts, fill, edge) {
        dc.setColor(fill, Gfx.COLOR_TRANSPARENT);
        dc.fillPolygon(pts);
        dc.setColor(edge, Gfx.COLOR_TRANSPARENT);
        dc.setPenWidth(1);
        var n = pts.size();
        for (var i = 0; i < n; i++) {
            var p = pts[i];
            var q = pts[(i + 1) % n];
            dc.drawLine(p[0], p[1], q[0], q[1]);
        }
    }

    // Point on the hand axis at distance f (radius units)
    function handPoint(a, f) {
        return polar(a, f);
    }

    // ---------------------------------------------------------------- drawing

    function onUpdate(dc) {
        if (dc has :setAntiAlias) {
            dc.setAntiAlias(true);
        }

        var style = GMTSettings.bezelStyle();
        var cols = bezelColors(style);

        dc.setColor(C_BLACK, C_BLACK);
        dc.clear();

        drawBezel(dc, cols);
        drawDial(dc);

        var clock = Sys.getClockTime();
        var hr = clock.hour;
        var mn = clock.min;
        var sc = clock.sec;
        var twoPi = Math.PI * 2.0;

        // GMT hand: one revolution per 24h, on UTC + configured offset
        var utc = Time.now().value() + GMTSettings.gmtOffset() * 3600;
        var daySec = ((utc % 86400) + 86400) % 86400;
        var aGmt = daySec / 86400.0 * twoPi;

        var aHour = ((hr % 12) + mn / 60.0) / 12.0 * twoPi;
        var aMin = (mn + sc / 60.0) / 60.0 * twoPi;

        drawHourHand(dc, aHour);
        drawGmtHand(dc, aGmt, cols[2]);
        drawMinuteHand(dc, aMin);

        if (_awake) {
            drawSecondHand(dc, sc / 60.0 * twoPi);
        } else {
            drawCenterCap(dc);
        }
    }

    function drawBezel(dc, cols) {
        var w = dc.getWidth();
        var h = dc.getHeight();

        // Two-tone insert: top half / bottom half
        dc.setColor(cols[0], C_BLACK);
        dc.fillCircle(_cx, _cy, _r);
        dc.setClip(0, _cy.toNumber(), w, h - _cy.toNumber());
        dc.setColor(cols[1], C_BLACK);
        dc.fillCircle(_cx, _cy, _r);
        dc.clearClip();

        // Steel edges
        dc.setColor(C_SILVER, Gfx.COLOR_TRANSPARENT);
        dc.setPenWidth(2);
        dc.drawCircle(_cx, _cy, _r - 1);
        dc.setPenWidth(1);

        // 24h markings
        var twoPi = Math.PI * 2.0;
        var font = Gfx.FONT_XTINY;
        dc.setColor(C_WHITE, Gfx.COLOR_TRANSPARENT);
        for (var i = 0; i < 24; i++) {
            var a = i / 24.0 * twoPi;
            if (i == 0) {
                // Inverted triangle at 24
                var tri = [polar(a, 0.835), polar(a - 0.075, 0.975), polar(a + 0.075, 0.975)];
                dc.fillPolygon(tri);
            } else if (i % 2 == 0) {
                var p = polar(a, 0.90);
                dc.drawText(p[0], p[1], font, i.toString(), Gfx.TEXT_JUSTIFY_CENTER | Gfx.TEXT_JUSTIFY_VCENTER);
            } else {
                // Odd hours: small rectangular index
                var bar = xf([[-0.012, 0.86], [-0.012, 0.95], [0.012, 0.95], [0.012, 0.86]], a);
                dc.fillPolygon(bar);
            }
        }

        // Inner steel ring separating bezel from dial
        dc.setColor(C_BLACK, C_BLACK);
        dc.fillCircle(_cx, _cy, _r * 0.80);
        dc.setColor(C_SILVER, Gfx.COLOR_TRANSPARENT);
        dc.setPenWidth(2);
        dc.drawCircle(_cx, _cy, _r * 0.80);
        dc.setPenWidth(1);
    }

    function drawDial(dc) {
        var twoPi = Math.PI * 2.0;

        // Minute track
        dc.setColor(C_WHITE, Gfx.COLOR_TRANSPARENT);
        for (var m = 0; m < 60; m++) {
            var a = m / 60.0 * twoPi;
            var inner = (m % 5 == 0) ? 0.735 : 0.755;
            var p1 = polar(a, inner);
            var p2 = polar(a, 0.785);
            dc.setPenWidth((m % 5 == 0) ? 2 : 1);
            dc.drawLine(p1[0], p1[1], p2[0], p2[1]);
        }
        dc.setPenWidth(1);

        // Hour markers
        for (var hh = 0; hh < 12; hh++) {
            var ah = hh / 12.0 * twoPi;
            if (hh == 0) {
                // 12: inverted triangle
                var tri = xf([[0.0, 0.55], [-0.085, 0.715], [0.085, 0.715]], ah);
                fillOutlined(dc, tri, C_WHITE, C_SILVER);
            } else if (hh == 3) {
                drawDate(dc);
            } else if (hh == 6 || hh == 9) {
                var bar = xf([[-0.04, 0.54], [-0.04, 0.715], [0.04, 0.715], [0.04, 0.54]], ah);
                fillOutlined(dc, bar, C_WHITE, C_SILVER);
            } else {
                var p = polar(ah, 0.645);
                dc.setColor(C_SILVER, Gfx.COLOR_TRANSPARENT);
                dc.fillCircle(p[0], p[1], _r * 0.068);
                dc.setColor(C_WHITE, Gfx.COLOR_TRANSPARENT);
                dc.fillCircle(p[0], p[1], _r * 0.055);
            }
        }

        // Dial print (crown + wordmarks) as bitmaps, one set per screen size
        if (_dialTop != null) {
            dc.drawBitmap(_cx - _dialTop.getWidth() / 2, _cy - _r * 0.53, _dialTop);
        }
        if (_dialBottom != null) {
            dc.drawBitmap(_cx - _dialBottom.getWidth() / 2, _cy + _r * 0.165, _dialBottom);
        }
    }

    function drawDate(dc) {
        var info = Gregorian.info(Time.now(), Time.FORMAT_SHORT);
        var day = info.day.toString();
        var f = Gfx.FONT_TINY;
        var fh = dc.getFontHeight(f);
        var bw = _r * 0.25;
        var bh = fh * 0.85;
        var x = _cx + _r * 0.63;
        var y = _cy;

        // Window frame (steel) + white date disc
        dc.setColor(C_SILVER, Gfx.COLOR_TRANSPARENT);
        dc.fillRectangle(x - bw / 2 - 2, y - bh / 2 - 2, bw + 4, bh + 4);
        dc.setColor(C_WHITE, Gfx.COLOR_TRANSPARENT);
        dc.fillRectangle(x - bw / 2, y - bh / 2, bw, bh);
        dc.setColor(C_BLACK, Gfx.COLOR_TRANSPARENT);
        dc.drawText(x, y, f, day, Gfx.TEXT_JUSTIFY_CENTER | Gfx.TEXT_JUSTIFY_VCENTER);
    }

    // Mercedes hour hand
    function drawHourHand(dc, a) {
        var shaft = xf([[-0.035, -0.10], [-0.035, 0.36], [0.035, 0.36], [0.035, -0.10]], a);
        fillOutlined(dc, shaft, C_WHITE, C_STEEL);

        var tip = xf([[-0.05, 0.48], [0.0, 0.585], [0.05, 0.48]], a);
        fillOutlined(dc, tip, C_WHITE, C_STEEL);

        // Mercedes circle
        var c = handPoint(a, 0.42);
        dc.setColor(C_SILVER, Gfx.COLOR_TRANSPARENT);
        dc.fillCircle(c[0], c[1], _r * 0.088);
        dc.setColor(C_WHITE, Gfx.COLOR_TRANSPARENT);
        dc.fillCircle(c[0], c[1], _r * 0.076);
        dc.setColor(C_BLACK, Gfx.COLOR_TRANSPARENT);
        dc.fillCircle(c[0], c[1], _r * 0.056);

        // Three spokes at 0, 120, 240 degrees (relative to hand)
        var cy = 0.42;
        var len = 0.058;
        var wd = 0.012;
        for (var k = 0; k < 3; k++) {
            var t = k * Math.PI * 2.0 / 3.0;
            var dx = Math.sin(t);
            var dy = Math.cos(t);
            var px = dy;   // perpendicular
            var py = -dx;
            var spoke = xf([
                [px * wd, cy + py * wd],
                [dx * len + px * wd, cy + dy * len + py * wd],
                [dx * len - px * wd, cy + dy * len - py * wd],
                [-px * wd, cy - py * wd]
            ], a);
            dc.setColor(C_WHITE, Gfx.COLOR_TRANSPARENT);
            dc.fillPolygon(spoke);
        }
        dc.fillCircle(c[0], c[1], _r * 0.016);
    }

    // 24h GMT hand with arrow tip reaching the bezel
    function drawGmtHand(dc, a, color) {
        var shaft = xf([[-0.013, -0.12], [-0.013, 0.66], [0.013, 0.66], [0.013, -0.12]], a);
        fillOutlined(dc, shaft, color, color);

        var arrow = xf([[-0.075, 0.645], [0.0, 0.80], [0.075, 0.645]], a);
        fillOutlined(dc, arrow, color, C_SILVER);
        var lume = xf([[-0.04, 0.67], [0.0, 0.75], [0.04, 0.67]], a);
        dc.setColor(C_WHITE, Gfx.COLOR_TRANSPARENT);
        dc.fillPolygon(lume);
    }

    // Baton minute hand with pointed tip
    function drawMinuteHand(dc, a) {
        var hand = xf([[-0.032, -0.12], [-0.032, 0.66], [0.0, 0.76], [0.032, 0.66], [0.032, -0.12]], a);
        fillOutlined(dc, hand, C_WHITE, C_STEEL);
    }

    function drawSecondHand(dc, a) {
        var c = C_WHITE;
        var hand = xf([[-0.009, -0.20], [-0.009, 0.76], [0.009, 0.76], [0.009, -0.20]], a);
        fillOutlined(dc, hand, c, C_STEEL);

        var dot = handPoint(a, 0.56);
        dc.setColor(C_SILVER, Gfx.COLOR_TRANSPARENT);
        dc.fillCircle(dot[0], dot[1], _r * 0.045);
        dc.setColor(C_WHITE, Gfx.COLOR_TRANSPARENT);
        dc.fillCircle(dot[0], dot[1], _r * 0.035);

        drawCenterCap(dc);
    }

    function drawCenterCap(dc) {
        dc.setColor(C_SILVER, Gfx.COLOR_TRANSPARENT);
        dc.fillCircle(_cx, _cy, _r * 0.045);
        dc.setColor(C_WHITE, Gfx.COLOR_TRANSPARENT);
        dc.fillCircle(_cx, _cy, _r * 0.025);
    }
}
