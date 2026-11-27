// Karty, które mają pokazywać samą ikonkę, bo żadne z dostępnych zdjęć do nich nie pasuje
// (zasada właściciela: złe zdjęcie → tylko ikonka). Dopisuje nocna kontrola jakości:
// jedna linia = 'id pozycji', // tytuł – dlaczego
// Gdy powstanie pasujące zdjęcie albo reguła w photos.ts, linię można usunąć.
export const PHOTO_OFF = new Set<string>([
  'e4c3816a-f278-4aad-915c-a5bb0ff762b7', // Orange Wheels – sala zabaw, a dostawała zdjęcie tańca (przegląd 26.11)
  '45aaab6f-5f3e-488d-874d-ffeb5227f53d', // La Perle – teatr z pokazem wodnym, a dostawała Burj Khalifę i fontanny (zgłoszenie testerki 26.11)
  '8f9d6d1c-82fb-434e-8665-291eefc4bec3', // Al Ain Adventure – park raftingu, a dostawał widok góry
  '35eb6532-27ab-47ad-abe4-edd5957234bd', // Storytelling Tours – oprowadzanie po muzeum, a dostawało scenę teatru
  'ca1bd774-a10b-4dd9-aac9-6388120a8873', // Book an Easel – rysowanie przy sztaludze w muzeum, a dostawało książkę w bibliotece
  'cab8c08c-03fe-4513-9ace-536f0efdae54', // XCAT World Championship: Fujairah Grand Prix – wyścig łodzi motorowych, a dostawał bolid F1
  '1e9f88b3-4235-421d-b6d5-56456db9d39b', // Ajman Fish Market – targ rybny, a dostawał suk z przyprawami
  '7f4f1304-e035-400c-a3c0-dc6e91d36c76', // UAE National Day Celebrations – kilka miejsc w Szardży, a dostawało plażę Chorfakkan (tester 26.11)
  '4dbddc45-aa13-4d03-a8ff-638ee2f0a1a8', // Al Hefaiyah Mountain Conservation Centre – ośrodek ze zwierzętami, a dostawał górską drogę (tester 26.11)
  '6cbc99d5-6655-431b-9376-124826d5528e', // Kalba Corniche – nadmorska promenada, a dostawała miejski park z fontanną i wieżowcami (tester 26.11)
  'b5b65fe1-65e2-49fe-af56-f0abe095650e', // Al Hefaiyah Lake – jezioro w górach, a dostawało miejski park z fontanną (tester 26.11)
  'fd418970-2798-46d7-81a8-6126763a87eb', // Shees Park – park w górskiej wiosce, a dostawał park z wieżowcami (tester 26.11)
  'bc1e1651-5707-4411-a6b3-8bfff8ec25e6', // Resistance Monument – pomnik pod gołym niebem, a dostawał salę muzeum (tester 26.11)
  '0c4f5222-9e11-44fa-a2cf-18404a6123fd', // Abu Dhabi Festival 2026 – festiwal muzyki klasycznej i sztuki (cała jesień), a dostawał scenę z laserami (tester 26.11)
  '04e99c0b-3477-47f3-bd64-c5dfd02f20e8', // ARTE Museum Dubai – cyfrowe projekcje (immersive), a dostawało salę z amforą (tester 27.11)
  '7553c09d-bbe3-4ca9-8d90-ee4506ca5cb0', // Sharjah Desert Theatre Festival – teatr pod gołym niebem na pustyni, a dostawał salę teatru z czerwoną kurtyną
  '6c398092-e8f7-42b2-b59a-f597626c3f14', // Al Fursan Eid Al Etihad Airshow at Kite Beach – pokaz odrzutowców nad plażą, a dostawał awionetkę nad pustynią
  '2b136d6b-ca50-4fb5-aea3-e9bd258356db', // Pool Day Access, Millennium Plaza (hotel przy Sheikh Zayed Rd) – dostawał plażę z Burj Al Arab (tester A 28.11)
  '02c64c07-4c73-444d-bd42-32d016ce370b', // New Year's Eve Celebrations (Mleiha National Park) – sylwester na pustyni pod gołym niebem, a dostawał stół sylwestrowy w sali (QC 28.11)
  'fbc3ed68-a33d-43d9-9f1d-6087cf1f74a9', // Indo Warehouse – New Year's Eve at the Penthouse Club – noc z DJ-em w klubie, a dostawał stół sylwestrowy ze świecami (QC 28.11)
  '64850fad-1cb5-4587-acfc-43f4a425ff36', // Bohemia Presents Mita Gami – DJ w beach clubie, a dostawał zespół rockowy (QC 28.11)
  '84876f6a-256e-4bd2-bb41-e80ffccb4a92', // Run for Everyone by Emirates Bodybuilding & Fitness Federation – bieg na wyspie Hudayriyat, a dostawał biegaczy wśród wydm (QC 28.11)
  'cfe4be7b-6abe-46a1-860e-0f371e1308ab', // Wild Winter Camp – obóz w Dubai Safari Park (zwierzęta), a dostawał krytą salę zabaw z kulkami (QC 28.11)
  'ac6dc233-20b2-46c3-8dad-85bc101ebc15', // Sharjah Architecture Triennial: Architecture Otherwise – wydarzenie w kilku miejscach, a dostawało zdjęcie jednego muzeum (QC 28.11)
]);
