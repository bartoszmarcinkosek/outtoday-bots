# Lista kontrolna nocnego testera kart (rośnie z każdym nowym rodzajem błędu)
Format: data | rodzaj błędu | przykład | jak naprawione (reguła / plik)

2026-11-26 | Free pokazuje płatne: Meetup („Free” = darmowy zapis) | Heels & Chair, padel, badminton | bot/run.py: Meetup nigdy is_free; price_min_aed czyszczone
2026-11-26 | Free pokazuje płatne: spektakl w galerii z wolnym wstępem | The Game's Afoot (The Junction, Alserkal) | bot/run.py free_entry_applies tylko wystawy
2026-11-26 | Ladies only pusty | Heels & Chair (Ladies Only) | app/src/logic.ts LADIES_RE z tytułu i opisu
2026-11-26 | Mężczyźni/pary na zdjęciu pozycji tylko dla pań | Heels & Chair | photos.ts: klucz dance_ladies (ikonka do czasu zdjęcia)
2026-11-26 | Zdjęcie pokoju przy afternoon tea | Afternoon Tea at La Farine (typ staycation) | typ → lunch; photos.ts klucz afternoon_tea
2026-11-26 | Zdjęcie pokoju przy staycation w beach resorcie | Fairmont Fujairah Beach Resort | photos.ts: beach resort → day_pass
2026-11-26 | Wyścigi konne przy targach łowieckich | Al Ain Hunting & Equestrian Exhibition | photos.ts: hunting exhibition → expo
2026-11-26 | Plaża przy wieczorze DJ w beach clubie; fort przy miejscowości Dibba Al Hisn; dolina górska przy pustyni | Lost Frequencies at Bohemia; Dibba Al Hisn Beach; Al Wadi Desert | photos.ts reguły
2026-11-26 | Wydarzenie powtarza stałe miejsce | La Perle (miejsce + „wydarzenie do 31.12”) | qa_after_add: długie wydarzenie = nazwa miejsca → FAIL
2026-11-26 | Wyprzedaż w centrum handlowym jako wydarzenie | 12-Day Super Sale, Reem Mall | qa_after_add: sale/discount → FAIL
2026-11-26 | Niezrozumiały tytuł | „BWP 1” (gala MMA) | tytuł poprawiony ręcznie
2026-11-26 | Rodzinne wydarzenie poza filtrem Kids | Aladdin at Al Qasba | diag_filters (niedziela)
2026-11-26 | Brunch z Mikołajem bez świątecznego zdjęcia | Santa brunch Market Kitchen | photos.ts santa/christmas → xmas
2026-11-26 | Wydarzenie za granicą wpisane jako ZEA | Highlander: Mount Macedon (Australia), Ehmej (Liban) jako Ras Al Khaimah | odrzucone; qa_after_add: miejsce za granicą / globalny organizator bez miejsca w ZEA → FAIL
2026-11-26 | Ten sam spektakl jako osobna karta na każdy termin | Cléopâtre „29/1”, „30/1”, „31/1”; Peter Pan (9–10 Dec)/(11–12 Dec); Hansel & Gretel 9.12 i 10.12 | połączone (od–do); qa_after_add: numer terminu w tytule / ten sam tytuł w tym samym miejscu ≤3 dni → FAIL
2026-11-26 | Tytuł z wyciętym separatorem (kilka spacji), WIELKIE LITERY | „RAFAEL   Skyline Saturdays”, „SVEN VÄTH   House Rules” | poprawione ręcznie; bot/run.py _guard: kilka spacji → „ – ”
2026-11-26 | Zła data z portalu biletowego = ukryty duplikat | Gulf Bar Show 2026 jako 1.04.2027 (naprawdę 30.11–1.12.2026, już w apce) | odrzucone; QA po poprawce daty wykrywa duplikat
2026-11-26 | Strona z programem z zeszłego roku | Dubai Fitness Challenge 2025 (Bluewaters) jako wydarzenie 2026 | odrzucone (qa: rok w tytule ≠ rok wydarzenia to WARN)
2026-11-26 | Mężczyźni na zdjęciu sportu dla kobiet | Ladies Football Social Game, Hudayriyat Women's Cycling Series | photos.ts klucz sport_ladies (ikonka do czasu zdjęcia)
2026-11-26 | Zdjęcie innej czynności | Face painting → malowanie na sztalugach; wystawa rzeźby → koło garncarskie; wyścig dhow → paddleboard; Hurricane Heat → flamingi Al Qudra; zawody kulturystyczne → trening na plaży; Motor Show → bolid F1; ladies night z duetem → tłum festiwalowy | photos.ts: facepaint, studios tylko zajęcia, sailing, obstacle, bodybuilding, motor show → carshow, ladies night → ladies_night
2026-11-26 | Panorama innego miasta w ogólnej puli | running-2 (Burj Khalifa) przy Sharjah Half Marathon / biegu w Abu Zabi | photos.ts CITY_ONLY: running-2 tylko Dubaj
2026-11-26 | Zdjęcie jednego miejsca przy wydarzeniu w kilku miejscach | UAE National Day Celebrations (Al Majaz, Al Qasba, Al Heera, Chorfakkan) → plaża Chorfakkan | photoOff.ts
2026-11-26 | Ten sam cykl jako osobna karta na każdy weekend / numer edycji w tytule | Eid Al Etihad Weekend at Al Marjan (4 karty), RAK Night Market (27–29 Nov)/(4–6 Dec), „Community Run at the Ripe Market -4” | połączone / tytuły poprawione; qa_after_add SESSION_RE łapie też „ -4”
2026-11-26 | Ta sama wystawa dwa razy (różnie zapisane miejsce) | Malik Thomas Jalil Kydd: „CARBON 12, WH 37” i „WH 37” | odrzucony duplikat
2026-11-26 | Danie dnia jako wydarzenie | Sunday Roast Short Rib Special (Topgolf) | odrzucone
2026-11-26 | Tytuł bez treści | „Bohemia Presents” (bez składu) | tytuł z DJ-ami z opisu
2026-11-26 | Zdjęcie innej czynności (2) | SailGP → paddleboard; kurs jazdy konnej → wyścigi; stanowisko archeologiczne → uliczka z wieżą wiatrową; koncert kolęd → stół z indykiem | photos.ts: sailing (+SailGP), horseriding, ruins, carols (ikonka do czasu zdjęć)
2026-11-26 | Miejskie zdjęcie przy górskim/nadmorskim miejscu we wschodniej Szardży | Kalba Corniche, Al Hefaiyah Lake, Shees Park → park z wieżowcami; Resistance Monument → sala muzeum; Abu Dhabi Festival → scena z laserami | photoOff.ts
2026-11-27 | Zdjęcie o konkretnej treści z ogólnej puli typu oferty | karaoke przy każdej „night out” (Cocktail Night, Stout N Smoke), szisza przy Zuma i dim sum, kuchnia indyjska przy steku (T-Bone & Tallow), teppanyaki przy Café 302, basen wśród wydm przy day passie w mieście / plaży Mamsha / Kids Zone | photos.ts ONLY_IF: night_out-5 tylko karaoke, night_out-6 tylko szisza/arabskie, dinner-7 tylko kuchnia indyjska, dinner-8 tylko japońska, day_pass-8 tylko pustynia, brunch-10 tylko azjatycki (113 kart dostaje inne zdjęcie)
2026-11-27 | Zdjęcie z wieżowcami w mieście bez wieżowców | Ain Al Madhab Gardens (Fudżajra) → park z wieżowcami; lunch/kolacje w RAK, Ajmanie, Fudżajrze → okno na wieżowce | photos.ts SKYLINE_FILES (parks-1, lunch-3, dinner-2, night_out-2) tylko Dubaj, Abu Zabi, Szardża
2026-11-27 | Lodowisko ze zdjęciem stoku narciarskiego | Dubai Ice Rink → Ski Dubai | photos.ts klucz ice_rink (ikonka do czasu zdjęcia)
2026-11-27 | Park trampolin jako day pass z basenem | Flip Junior (Flipped Park RAK) | photos.ts trampoline łapie „flipped park”
2026-11-27 | Koncert muzyki klasycznej ze zdjęciem zespołu rockowego | Young Maestro: Bach, Vivaldi & Handel | photos.ts candlelight: nazwiska kompozytorów
2026-11-27 | Ten sam event dwa razy z różnymi datami (ta sama strona biletów) | Lamhayab ft. Yassar Lemghari 25.12 i 9.01; Harry Potter Film Concert Series (zła data 10–28.03) + osobna karta Prisoner of Azkaban | odrzucone/poprawione; qa_after_add: ta sama strona biletów + podobny tytuł + inna data → FAIL
2026-11-27 | Cena z portalu zupełnie zła | Katy Perry NYE gala (30 AED zamiast od 6 500 AED) | poprawione ręcznie
2026-11-27 | Pakiet / zamknięty szczyt jako wydarzenie | Festive Package (Bedrock), World Majlis for Urban Intelligence | odrzucone
2026-11-27 | Tytuł z kilkoma spacjami w starych wpisach | Yaw Owusu / Tatiana Chalhoub (Alserkal) | poprawione; qa_after_add: kilka spacji w tytule → FAIL (łapie też stare przy pełnym przebiegu)
2026-11-27 | Wyprzedaż w liczbie mnogiej / wyprzedaż za rok | „Summer Sales (Back to School)” 2027, „Winter Clearance Sale” 2027 (Expo Centre Sharjah) | odrzucone; qa_after_add: sales? + summer/winter/clearance → FAIL
2026-11-27 | Wystawa dwa razy: druga karta ma datę końca jako datę startu | Faris Alshafar, Yaw Owusu (Alserkal) | odrzucone / data poprawiona; łapie istniejąca reguła „ta sama strona biletów + inna data”
2026-11-27 | Separator „|” lub „\” albo godzina w tytule | „Faris Alshafar | Everybody…”, „Saturday Run \ Al Heera Beach”, „Board game night…, 6 PM” | poprawione; qa_after_add: „|”/„\” → FAIL, godzina na końcu tytułu → WARN
2026-11-27 | Cena = najdroższe miejsce | Max Amini, Coca-Cola Arena (1 795 zamiast od 195 AED) | poprawione ręcznie
2026-11-27 | Zdjęcie innej czynności (3) | „Kuwaiti Musical Night” → balet; recital Yuja Wang → świece Candlelight; bieg na plaży → wydmy; zapalanie choinki → stół z indykiem; Mariah Carey w arenie → stół z indykiem; Home Alone/Encanto w arenie i festiwal na plaży → kameralny klub | photos.ts: „musical night” ≠ teatr; ONLY_IF candlelight-5, running-3, xmas-1/2, concert-5; święta w arenie → wnętrze areny
2026-11-27 | Opis obiecuje coś, czego organizator nie podaje (free parking, family-friendly, free entry, live music, unlimited drinks, konkretny artysta/godzina) | – | tester i nocna kontrola 1 porównują opis ze stroną; nie potwierdzone → usunąć z opisu
- Brak opisu / opis < 40 znaków (nie wiadomo, o co chodzi) → dopisz 1–2 zdania ze strony organizatora (27.11 Ghostly Kisses). Nowe pozycje bez opisu bramka QA trzyma ukryte.
- Gra planszowa ze zdjęciem sprzątania plaży / zdjęcie z innej czynności → zła reguła w photos.ts (27.11 Board Game Adventure, Luwr).
- Świąteczny posiłek (kolacja, lunch, brunch w restauracji/barze) ze zdjęciem jarmarku albo choinki → ma być świąteczny stół; jarmark tylko dla jarmarków (27.11 Christmas Day, Turtle Bay).
- Zdjęcie budynku nie wygląda jak prawdziwy budynek (AI narysowało inny kształt) → wyłącz plik w DISABLED (photos.ts) i zgłoś właścicielowi; porównaj z prawdziwym zdjęciem miejsca (27.11 Etihad Arena).
- Występ w sali (taniec, teatr) ze zdjęciem kampusu/budynku zamiast rodzaju występu → rodzaj z opisu (27.11 Cycles – Boy Blue, NYUAD).
- Oferta bez strony lokalu, tylko z portalu (Time Out, Yalla…) albo z dopiskiem „confirm before you go” → ukryj (hide_deal_ids), aż potwierdzisz u lokalu (27.11).
