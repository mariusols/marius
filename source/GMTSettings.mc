using Toybox.Application.Properties;
using Toybox.Lang;
using Toybox.WatchUi;

module GMTSettings {

    const BEZEL_COUNT = 3;

    function getNumber(key, def) {
        var v = Properties.getValue(key);
        if (v instanceof Lang.Number) {
            return v;
        }
        return def;
    }

    function setNumber(key, value) {
        try {
            Properties.setValue(key, value);
        } catch (e) {
        }
    }

    function bezelStyle() {
        var b = getNumber("BezelStyle", 0);
        if (b < 0 || b >= BEZEL_COUNT) {
            b = 0;
        }
        return b;
    }

    function gmtOffset() {
        var o = getNumber("GmtOffset", 0);
        if (o < -12) { o = -12; }
        if (o > 14) { o = 14; }
        return o;
    }

    function bezelName(b) {
        if (b == 1) { return "Batman"; }
        if (b == 2) { return "Sprite"; }
        return "Pepsi";
    }

    function offsetLabel(o) {
        if (o == 0) { return "UTC"; }
        if (o > 0) { return "UTC+" + o.toString(); }
        return "UTC" + o.toString();
    }
}

class GMTSettingsMenu extends WatchUi.Menu2 {

    var bezelItem;
    var plusItem;
    var minusItem;

    function initialize() {
        Menu2.initialize({ :title => "GMT-Master II" });
        bezelItem = new WatchUi.MenuItem("Bezel", GMTSettings.bezelName(GMTSettings.bezelStyle()), :bezel, {});
        plusItem = new WatchUi.MenuItem("GMT +1 time", GMTSettings.offsetLabel(GMTSettings.gmtOffset()), :plus, {});
        minusItem = new WatchUi.MenuItem("GMT -1 time", GMTSettings.offsetLabel(GMTSettings.gmtOffset()), :minus, {});
        addItem(bezelItem);
        addItem(plusItem);
        addItem(minusItem);
    }

    function refresh() {
        bezelItem.setSubLabel(GMTSettings.bezelName(GMTSettings.bezelStyle()));
        var lbl = GMTSettings.offsetLabel(GMTSettings.gmtOffset());
        plusItem.setSubLabel(lbl);
        minusItem.setSubLabel(lbl);
        WatchUi.requestUpdate();
    }
}

class GMTSettingsDelegate extends WatchUi.Menu2InputDelegate {

    var _menu;

    function initialize(menu) {
        Menu2InputDelegate.initialize();
        _menu = menu;
    }

    function onSelect(item) {
        var id = item.getId();
        if (id == :bezel) {
            GMTSettings.setNumber("BezelStyle", (GMTSettings.bezelStyle() + 1) % GMTSettings.BEZEL_COUNT);
        } else if (id == :plus) {
            var o = GMTSettings.gmtOffset() + 1;
            if (o > 14) { o = -12; }
            GMTSettings.setNumber("GmtOffset", o);
        } else if (id == :minus) {
            var o2 = GMTSettings.gmtOffset() - 1;
            if (o2 < -12) { o2 = 14; }
            GMTSettings.setNumber("GmtOffset", o2);
        }
        _menu.refresh();
    }

    function onBack() {
        WatchUi.popView(WatchUi.SLIDE_IMMEDIATE);
    }
}
