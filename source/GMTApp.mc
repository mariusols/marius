using Toybox.Application;
using Toybox.WatchUi;

class GMTApp extends Application.AppBase {

    function initialize() {
        AppBase.initialize();
    }

    function onStart(state) {
    }

    function onStop(state) {
    }

    function getInitialView() {
        return [ new GMTView() ];
    }

    // Called when settings are changed from Garmin Connect / Connect IQ app
    function onSettingsChanged() {
        WatchUi.requestUpdate();
    }

    // On-watch settings: hold UP/MENU on the watch face > "Tilpass"/"Customize"
    function getSettingsView() {
        var menu = new GMTSettingsMenu();
        return [ menu, new GMTSettingsDelegate(menu) ];
    }
}
