// Klucz Google Maps (Android) nie jest w kodzie: EAS bierze go z sekretu GOOGLE_MAPS_API_KEY.
module.exports = ({ config }) => ({
  ...config,
  android: {
    ...config.android,
    config: { ...(config.android?.config ?? {}), googleMaps: { apiKey: process.env.GOOGLE_MAPS_API_KEY ?? '' } },
  },
});
