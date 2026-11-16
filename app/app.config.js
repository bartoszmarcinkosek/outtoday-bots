// Klucz Google Maps (Android) nie jest w kodzie: EAS bierze go z sekretu GOOGLE_MAPS_API_KEY.
// FOR_EXPO_GO=1: aktualizacja dla Expo Go na iPhonie (Expo Go przyjmuje tylko wersję "exposdk:<SDK>").
module.exports = ({ config }) => ({
  ...config,
  ...(process.env.FOR_EXPO_GO === '1' ? { runtimeVersion: `exposdk:${config.sdkVersion ?? '58.0.0'}` } : {}),
  android: {
    ...config.android,
    config: { ...(config.android?.config ?? {}), googleMaps: { apiKey: process.env.GOOGLE_MAPS_API_KEY ?? '' } },
  },
});
