// Google Play: aplikacja jest w pionie, ale nie wymaga ekranu "portrait" (tablety, Chromebooki).
const { withAndroidManifest } = require("expo/config-plugins");
module.exports = function portraitOptional(config) {
  return withAndroidManifest(config, (cfg) => {
    const m = cfg.modResults.manifest;
    m["uses-feature"] = (m["uses-feature"] || []).filter((f) => f.$["android:name"] !== "android.hardware.screen.portrait");
    m["uses-feature"].push({ $: { "android:name": "android.hardware.screen.portrait", "android:required": "false" } });
    return cfg;
  });
};
