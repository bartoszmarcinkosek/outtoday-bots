// Karty, które mają pokazywać samą ikonkę, bo żadne z dostępnych zdjęć do nich nie pasuje
// (zasada właściciela: złe zdjęcie → tylko ikonka). Dopisuje nocna kontrola jakości:
// jedna linia = 'id pozycji', // tytuł – dlaczego
// Gdy powstanie pasujące zdjęcie albo reguła w photos.ts, linię można usunąć.
export const PHOTO_OFF = new Set<string>([
]);
