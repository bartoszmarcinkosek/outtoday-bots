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
