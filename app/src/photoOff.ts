// Karty, które mają pokazywać samą ikonkę, bo żadne z dostępnych zdjęć do nich nie pasuje
// (zasada właściciela: złe zdjęcie → tylko ikonka). Dopisuje nocna kontrola jakości:
// jedna linia = 'id pozycji', // tytuł – dlaczego
// Gdy powstanie pasujące zdjęcie albo reguła w photos.ts, linię można usunąć.
export const PHOTO_OFF = new Set<string>([
  '45aaab6f-5f3e-488d-874d-ffeb5227f53d', // La Perle – teatr z pokazem wodnym, a dostawała Burj Khalifę i fontanny (zgłoszenie testerki 26.11)
  '8f9d6d1c-82fb-434e-8665-291eefc4bec3', // Al Ain Adventure – park raftingu, a dostawał widok góry
  '35eb6532-27ab-47ad-abe4-edd5957234bd', // Storytelling Tours – oprowadzanie po muzeum, a dostawało scenę teatru
  'ca1bd774-a10b-4dd9-aac9-6388120a8873', // Book an Easel – rysowanie przy sztaludze w muzeum, a dostawało książkę w bibliotece
  'cab8c08c-03fe-4513-9ace-536f0efdae54', // XCAT World Championship: Fujairah Grand Prix – wyścig łodzi motorowych, a dostawał bolid F1
  '1e9f88b3-4235-421d-b6d5-56456db9d39b', // Ajman Fish Market – targ rybny, a dostawał suk z przyprawami
]);
